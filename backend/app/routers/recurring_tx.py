from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from datetime import datetime, timezone, timedelta
import calendar

from app.database.session import get_db
from app.models.recurring import RecurringTransaction
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.planning import RecurringTransactionCreate, RecurringTransactionUpdate, RecurringTransactionResponse
from app.routers.deps import get_current_user
from app.services.cache import cache_service

router = APIRouter()

def calculate_next_run(current_date: datetime, frequency: str) -> datetime:
    """
    Calculate the next execution date based on frequency.
    """
    freq = frequency.lower()
    if freq == 'daily':
        return current_date + timedelta(days=1)
    elif freq == 'weekly':
        return current_date + timedelta(weeks=1)
    elif freq == 'monthly':
        year = current_date.year
        month = current_date.month + 1
        if month > 12:
            month = 1
            year += 1
        _, last_day = calendar.monthrange(year, month)
        day = min(current_date.day, last_day)
        return current_date.replace(year=year, month=month, day=day)
    elif freq == 'yearly':
        year = current_date.year + 1
        day = current_date.day
        if current_date.month == 2 and current_date.day == 29:
            if not calendar.isleap(year):
                day = 28
        return current_date.replace(year=year, day=day)
    return current_date + timedelta(days=30)  # default fallback

@router.get("/", response_model=List[RecurringTransactionResponse])
def get_recurring_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve all active recurring transaction rules for the user.
    """
    stmt = (
        select(RecurringTransaction)
        .options(
            joinedload(RecurringTransaction.category),
            joinedload(RecurringTransaction.account)
        )
        .where(RecurringTransaction.user_id == current_user.id)
    )
    return db.execute(stmt).scalars().all()

@router.post("/", response_model=RecurringTransactionResponse, status_code=status.HTTP_201_CREATED)
def create_recurring_transaction(
    rule_in: RecurringTransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new recurring transaction schedule rule.
    """
    # Verify account
    stmt_acct = select(Account).where(Account.id == rule_in.account_id, Account.user_id == current_user.id)
    account = db.execute(stmt_acct).scalar_one_or_none()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found."
        )

    # Calculate initial next_run (equals start_date; if it is in the past, the process job will catch it up)
    start_date_naive = rule_in.start_date.replace(tzinfo=None)
    next_run = start_date_naive

    rule = RecurringTransaction(
        user_id=current_user.id,
        category_id=rule_in.category_id,
        account_id=rule_in.account_id,
        type=rule_in.type,
        amount=rule_in.amount,
        description=rule_in.description,
        frequency=rule_in.frequency,
        start_date=start_date_naive,
        next_run=next_run
    )
    
    db.add(rule)
    db.commit()
    db.refresh(rule)
    
    # Invalidate cache
    cache_service.delete(f"user:{current_user.id}:stats")
    cache_service.delete_pattern(f"user:{current_user.id}:insights*")
    
    stmt_reload = (
        select(RecurringTransaction)
        .options(
            joinedload(RecurringTransaction.category),
            joinedload(RecurringTransaction.account)
        )
        .where(RecurringTransaction.id == rule.id)
    )
    return db.execute(stmt_reload).scalar_one()

@router.post("/process", status_code=status.HTTP_200_OK)
def process_recurring_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check active rules and automatically generate due ledger transactions.
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    stmt = (
        select(RecurringTransaction)
        .where(
            RecurringTransaction.user_id == current_user.id,
            RecurringTransaction.next_run <= now
        )
    )
    due_rules = db.execute(stmt).scalars().all()
    
    generated_count = 0
    for rule in due_rules:
        # Fetch account
        account = db.get(Account, rule.account_id)
        if not account:
            continue

        # In case the next_run is far in the past, loop to generate multiple missed cycles
        while rule.next_run <= now:
            # 1. Log transaction
            tx = Transaction(
                user_id=rule.user_id,
                type=rule.type,
                amount=rule.amount,
                description=f"{rule.description} (Recurring)",
                date=rule.next_run,
                category_id=rule.category_id,
                account_id=rule.account_id
            )
            db.add(tx)
            
            # 2. Adjust account balance
            if rule.type == "income":
                account.balance += rule.amount
            elif rule.type == "expense":
                account.balance -= rule.amount
                
            generated_count += 1
            
            # 3. Increment next_run
            rule.last_run = rule.next_run
            rule.next_run = calculate_next_run(rule.next_run, rule.frequency)
            
    if generated_count > 0:
        db.commit()
        # Invalidate cache
        cache_service.delete(f"user:{current_user.id}:stats")
        cache_service.delete_pattern(f"user:{current_user.id}:insights*")
        
    return {"success": True, "generated_transactions_count": generated_count}

@router.put("/{recurring_id}", response_model=RecurringTransactionResponse)
def update_recurring_transaction(
    recurring_id: int,
    rule_in: RecurringTransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update recurring transaction properties.
    """
    stmt = select(RecurringTransaction).where(RecurringTransaction.id == recurring_id, RecurringTransaction.user_id == current_user.id)
    rule = db.execute(stmt).scalar_one_or_none()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurring transaction schedule not found."
        )

    update_data = rule_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)
        
    db.commit()
    db.refresh(rule)
    
    # Invalidate cache
    cache_service.delete(f"user:{current_user.id}:stats")
    cache_service.delete_pattern(f"user:{current_user.id}:insights*")
    
    stmt_reload = (
        select(RecurringTransaction)
        .options(
            joinedload(RecurringTransaction.category),
            joinedload(RecurringTransaction.account)
        )
        .where(RecurringTransaction.id == rule.id)
    )
    return db.execute(stmt_reload).scalar_one()

@router.delete("/{recurring_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recurring_transaction(
    recurring_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a recurring transaction schedule rule.
    """
    stmt = select(RecurringTransaction).where(RecurringTransaction.id == recurring_id, RecurringTransaction.user_id == current_user.id)
    rule = db.execute(stmt).scalar_one_or_none()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurring transaction schedule not found."
        )
        
    db.delete(rule)
    db.commit()
    
    # Invalidate cache
    cache_service.delete(f"user:{current_user.id}:stats")
    cache_service.delete_pattern(f"user:{current_user.id}:insights*")
    return

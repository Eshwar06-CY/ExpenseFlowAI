from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from datetime import datetime, timezone

from app.database.session import get_db
from app.models.bill import Bill
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.planning import BillCreate, BillUpdate, BillResponse
from app.routers.deps import get_current_user
from app.services.cache import cache_service

router = APIRouter()

@router.get("/", response_model=List[BillResponse])
def get_bills(
    is_paid: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve all bills for the user.
    """
    stmt = select(Bill).options(joinedload(Bill.category)).where(Bill.user_id == current_user.id)
    if is_paid is not None:
        stmt = stmt.where(Bill.is_paid == is_paid)
    stmt = stmt.order_by(Bill.due_date.asc())
    return db.execute(stmt).scalars().all()

@router.post("/", response_model=BillResponse, status_code=status.HTTP_201_CREATED)
def create_bill(
    bill_in: BillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new pending bill.
    """
    bill = Bill(
        user_id=current_user.id,
        name=bill_in.name,
        amount=bill_in.amount,
        due_date=bill_in.due_date,
        category_id=bill_in.category_id,
        is_paid=False
    )
    db.add(bill)
    db.commit()
    db.refresh(bill)
    
    # Invalidate cache
    cache_service.delete(f"user:{current_user.id}:stats")
    cache_service.delete_pattern(f"user:{current_user.id}:insights*")
    
    stmt_reload = select(Bill).options(joinedload(Bill.category)).where(Bill.id == bill.id)
    return db.execute(stmt_reload).scalar_one()

@router.put("/{bill_id}", response_model=BillResponse)
def update_bill(
    bill_id: int,
    bill_in: BillUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update bill attributes.
    """
    stmt = select(Bill).where(Bill.id == bill_id, Bill.user_id == current_user.id)
    bill = db.execute(stmt).scalar_one_or_none()
    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bill not found."
        )

    update_data = bill_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(bill, field, value)

    db.commit()
    db.refresh(bill)
    
    # Invalidate cache
    cache_service.delete(f"user:{current_user.id}:stats")
    cache_service.delete_pattern(f"user:{current_user.id}:insights*")
    
    stmt_reload = select(Bill).options(joinedload(Bill.category)).where(Bill.id == bill.id)
    return db.execute(stmt_reload).scalar_one()

@router.post("/{bill_id}/pay", response_model=BillResponse)
def pay_bill(
    bill_id: int,
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Pay a bill, automatically debiting from a bank account and logging the expense.
    """
    stmt = select(Bill).where(Bill.id == bill_id, Bill.user_id == current_user.id)
    bill = db.execute(stmt).scalar_one_or_none()
    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bill not found."
        )

    if bill.is_paid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bill has already been paid."
        )

    stmt_acct = select(Account).where(Account.id == account_id, Account.user_id == current_user.id)
    account = db.execute(stmt_acct).scalar_one_or_none()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found."
        )

    # 1. Deduct account balance
    account.balance -= bill.amount

    # 2. Log transaction in ledger
    tx = Transaction(
        user_id=current_user.id,
        type="expense",
        amount=bill.amount,
        description=f"Paid bill: {bill.name}",
        date=datetime.now(timezone.utc),
        account_id=account.id,
        category_id=bill.category_id
    )
    db.add(tx)

    # 3. Mark bill as paid
    bill.is_paid = True
    db.commit()
    db.refresh(bill)
    
    # Invalidate cache
    cache_service.delete(f"user:{current_user.id}:stats")
    cache_service.delete_pattern(f"user:{current_user.id}:insights*")
    
    stmt_reload = select(Bill).options(joinedload(Bill.category)).where(Bill.id == bill.id)
    return db.execute(stmt_reload).scalar_one()

@router.delete("/{bill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bill(
    bill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a bill.
    """
    stmt = select(Bill).where(Bill.id == bill_id, Bill.user_id == current_user.id)
    bill = db.execute(stmt).scalar_one_or_none()
    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bill not found."
        )
        
    db.delete(bill)
    db.commit()
    
    # Invalidate cache
    cache_service.delete(f"user:{current_user.id}:stats")
    cache_service.delete_pattern(f"user:{current_user.id}:insights*")
    return

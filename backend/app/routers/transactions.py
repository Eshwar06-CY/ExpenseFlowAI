from datetime import datetime, timezone
from typing import List, Optional
import calendar
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, or_, func
from app.database.session import get_db
from app.models.transaction import Transaction
from app.models.account import Account
from app.models.category import Category
from app.models.user import User
from app.models.budget import Budget
from app.models.notification import Notification
from app.schemas.transaction import TransactionCreate, TransactionUpdate, TransactionResponse
from app.routers.deps import get_current_user
from app.services.cache import cache_service
from app.services.automation_service import AutomationRunner

router = APIRouter()

def sync_budget_for_transaction(db: Session, user_id: int, category_id: Optional[int], date_val: datetime):
    """
    Recalculates a category budget's spent field and triggers a notification if exceeded.
    """
    if not category_id:
        return
    month_str = date_val.strftime("%Y-%m")
    stmt = select(Budget).options(joinedload(Budget.category)).where(
        Budget.user_id == user_id,
        Budget.category_id == category_id,
        Budget.month == month_str
    )
    budget = db.execute(stmt).scalar_one_or_none()
    if not budget:
        return

    try:
        year, month = map(int, month_str.split("-"))
        _, last_day = calendar.monthrange(year, month)
        start_date = datetime(year, month, 1, 0, 0, 0)
        end_date = datetime(year, month, last_day, 23, 59, 59)
    except Exception:
        return

    stmt_sum = select(func.sum(Transaction.amount)).where(
        Transaction.user_id == user_id,
        Transaction.category_id == category_id,
        Transaction.type == "expense",
        Transaction.date >= start_date,
        Transaction.date <= end_date
    )
    spent_sum = db.execute(stmt_sum).scalar() or 0.0
    budget.spent = spent_sum
    
    if budget.spent > budget.amount:
        cat_name = budget.category.name if budget.category else "Category"
        title = f"Budget Alert: {cat_name} Limit Exceeded"
        message = f"You spent ${budget.spent:,.2f} of your ${budget.amount:,.2f} budget for {cat_name} in {month_str}."
        
        # Check duplicate notification
        stmt_check = select(Notification).where(
            Notification.user_id == user_id,
            Notification.title == title,
            Notification.message == message
        )
        existing_notif = db.execute(stmt_check).scalar_one_or_none()
        if not existing_notif:
            notif = Notification(user_id=user_id, title=title, message=message, is_read=False)
            db.add(notif)
            
    db.commit()


@router.get("/", response_model=List[TransactionResponse])
def get_transactions(
    response: Response,
    type: Optional[str] = None,
    category_id: Optional[int] = None,
    account_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    sort_by: Optional[str] = "date",
    sort_order: Optional[str] = "desc",
    q: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve all transactions for the authenticated user with advanced filters, pagination, and search.
    """
    stmt = (
        select(Transaction)
        .options(
            joinedload(Transaction.category),
            joinedload(Transaction.account),
            joinedload(Transaction.to_account)
        )
        .where(Transaction.user_id == current_user.id)
    )
    
    if type:
        stmt = stmt.where(Transaction.type == type)
    if category_id:
        stmt = stmt.where(Transaction.category_id == category_id)
    if account_id:
        stmt = stmt.where(
            or_(
                Transaction.account_id == account_id,
                Transaction.to_account_id == account_id
            )
        )
    if start_date:
        stmt = stmt.where(Transaction.date >= start_date)
    if end_date:
        stmt = stmt.where(Transaction.date <= end_date)
    if min_amount is not None:
        stmt = stmt.where(Transaction.amount >= min_amount)
    if max_amount is not None:
        stmt = stmt.where(Transaction.amount <= max_amount)
    if q:
        stmt = stmt.where(Transaction.description.ilike(f"%{q}%"))
        
    # Get total count before pagination
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_count = db.execute(count_stmt).scalar() or 0

    response.headers["X-Total-Count"] = str(total_count)
    response.headers["X-Limit"] = str(limit)
    response.headers["X-Skip"] = str(skip)

    # Sorting
    sort_col = Transaction.date
    if sort_by == "amount":
        sort_col = Transaction.amount
    elif sort_by == "description":
        sort_col = Transaction.description

    if sort_order == "asc":
        stmt = stmt.order_by(sort_col.asc())
    else:
        stmt = stmt.order_by(sort_col.desc())

    stmt = stmt.offset(skip).limit(limit)
    result = db.execute(stmt)
    return result.scalars().all()

@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    transaction_in: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new transaction and reconcile affected account balances.
    """
    # 1. Fetch and validate source account
    stmt = select(Account).where(Account.id == transaction_in.account_id, Account.user_id == current_user.id)
    account = db.execute(stmt).scalar_one_or_none()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source account not found."
        )

    to_account = None
    if transaction_in.type == "transfer":
        # 2. Fetch and validate destination account
        stmt = select(Account).where(Account.id == transaction_in.to_account_id, Account.user_id == current_user.id)
        to_account = db.execute(stmt).scalar_one_or_none()
        if not to_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Destination transfer account not found."
            )

    # 3. Check and validate Category if provided
    if transaction_in.category_id:
        stmt = select(Category).where(
            Category.id == transaction_in.category_id,
            or_(
                Category.user_id == current_user.id,
                Category.user_id.is_(None)
            )
        )
        category = db.execute(stmt).scalar_one_or_none()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found."
            )

    # 4. Perform balance reconciliation
    if transaction_in.type == "income":
        account.balance += transaction_in.amount
    elif transaction_in.type == "expense":
        account.balance -= transaction_in.amount
    elif transaction_in.type == "transfer":
        account.balance -= transaction_in.amount
        to_account.balance += transaction_in.amount

    # 5. Save transaction
    transaction = Transaction(
        user_id=current_user.id,
        type=transaction_in.type,
        amount=transaction_in.amount,
        description=transaction_in.description,
        date=transaction_in.date,
        category_id=transaction_in.category_id,
        account_id=transaction_in.account_id,
        to_account_id=transaction_in.to_account_id
    )
    
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    # Sync budget spent balance
    sync_budget_for_transaction(db, current_user.id, transaction.category_id, transaction.date)

    # Fire automation rules (non-blocking: failures are logged, not raised)
    try:
        AutomationRunner.run_for_transaction(db, transaction, current_user.id)
    except Exception as _auto_err:
        import logging
        logging.getLogger(__name__).warning("Automation hook failed: %s", _auto_err)

    # Invalidate cache
    cache_service.delete(f"user:{current_user.id}:stats")
    cache_service.delete_pattern(f"user:{current_user.id}:insights*")
    
    # Reload relation fields
    stmt = (
        select(Transaction)
        .options(
            joinedload(Transaction.category),
            joinedload(Transaction.account),
            joinedload(Transaction.to_account)
        )
        .where(Transaction.id == transaction.id)
    )
    return db.execute(stmt).scalar_one()

@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: int,
    transaction_in: TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing transaction and reconcile impacted account balances.
    """
    # Fetch existing transaction
    stmt = select(Transaction).where(Transaction.id == transaction_id, Transaction.user_id == current_user.id)
    transaction = db.execute(stmt).scalar_one_or_none()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found."
        )

    # 1. UNDO old transaction balance impact
    old_account = db.execute(select(Account).where(Account.id == transaction.account_id)).scalar_one_or_none()
    old_to_account = db.execute(select(Account).where(Account.id == transaction.to_account_id)).scalar_one_or_none() if transaction.to_account_id else None

    if old_account:
        if transaction.type == "income":
            old_account.balance -= transaction.amount
        elif transaction.type == "expense":
            old_account.balance += transaction.amount
        elif transaction.type == "transfer":
            old_account.balance += transaction.amount
            if old_to_account:
                old_to_account.balance -= transaction.amount

    # 2. Prepare new properties and validate updates
    update_data = transaction_in.model_dump(exclude_unset=True)
    new_type = update_data.get("type", transaction.type)
    new_amount = update_data.get("amount", transaction.amount)
    new_account_id = update_data.get("account_id", transaction.account_id)
    new_to_account_id = update_data.get("to_account_id", transaction.to_account_id)
    new_category_id = update_data.get("category_id", transaction.category_id)

    # Validate accounts exist and belong to user
    new_account = db.execute(select(Account).where(Account.id == new_account_id, Account.user_id == current_user.id)).scalar_one_or_none()
    if not new_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target account not found."
        )

    new_to_account = None
    if new_type == "transfer":
        if not new_to_account_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Destination transfer account required."
            )
        if new_account_id == new_to_account_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Source and destination accounts must be different."
            )
        new_to_account = db.execute(select(Account).where(Account.id == new_to_account_id, Account.user_id == current_user.id)).scalar_one_or_none()
        if not new_to_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target destination account not found."
            )

    # Validate category exists
    if new_category_id:
        new_cat = db.execute(select(Category).where(
            Category.id == new_category_id,
            or_(Category.user_id == current_user.id, Category.user_id.is_(None))
        )).scalar_one_or_none()
        if not new_cat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found."
            )

    # 3. APPLY new transaction balance impact
    if new_type == "income":
        new_account.balance += new_amount
    elif new_type == "expense":
        new_account.balance -= new_amount
    elif new_type == "transfer":
        new_account.balance -= new_amount
        if new_to_account:
            new_to_account.balance += new_amount

    # 4. Update database values
    old_category_id = transaction.category_id
    old_date = transaction.date

    for field, value in update_data.items():
        setattr(transaction, field, value)
    
    # Ensure correct null-values for to_account_id if changing from transfer to income/expense
    if new_type != "transfer":
        transaction.to_account_id = None

    db.commit()
    db.refresh(transaction)
    
    # Sync new and old budgets spent balances
    sync_budget_for_transaction(db, current_user.id, old_category_id, old_date)
    if transaction.category_id != old_category_id or transaction.date != old_date:
        sync_budget_for_transaction(db, current_user.id, transaction.category_id, transaction.date)
        
    # Invalidate cache
    cache_service.delete(f"user:{current_user.id}:stats")
    cache_service.delete_pattern(f"user:{current_user.id}:insights*")
    
    # Reload relation fields
    stmt = (
        select(Transaction)
        .options(
            joinedload(Transaction.category),
            joinedload(Transaction.account),
            joinedload(Transaction.to_account)
        )
        .where(Transaction.id == transaction.id)
    )
    return db.execute(stmt).scalar_one()

@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a transaction and revert its balance impact.
    """
    stmt = select(Transaction).where(Transaction.id == transaction_id, Transaction.user_id == current_user.id)
    transaction = db.execute(stmt).scalar_one_or_none()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found."
        )

    # Revert balance changes
    account = db.execute(select(Account).where(Account.id == transaction.account_id)).scalar_one_or_none()
    to_account = db.execute(select(Account).where(Account.id == transaction.to_account_id)).scalar_one_or_none() if transaction.to_account_id else None

    if account:
        if transaction.type == "income":
            account.balance -= transaction.amount
        elif transaction.type == "expense":
            account.balance += transaction.amount
        elif transaction.type == "transfer":
            account.balance += transaction.amount
            if to_account:
                to_account.balance -= transaction.amount

    old_category_id = transaction.category_id
    old_date = transaction.date

    db.delete(transaction)
    db.commit()
    
    # Sync budget spent balance
    sync_budget_for_transaction(db, current_user.id, old_category_id, old_date)
    
    # Invalidate cache
    cache_service.delete(f"user:{current_user.id}:stats")
    cache_service.delete_pattern(f"user:{current_user.id}:insights*")
    return

@router.get("/stats")
def get_transaction_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve financial summary stats for the dashboard.
    """
    cache_key = f"user:{current_user.id}:stats"
    cached = cache_service.get(cache_key)
    if cached is not None:
        return cached

    from app.services.finance_engine import FinanceEngine

    summary = FinanceEngine.get_dashboard_summary(db, current_user.id)

    stmt_recent = (
        select(Transaction)
        .options(
            joinedload(Transaction.category),
            joinedload(Transaction.account),
            joinedload(Transaction.to_account)
        )
        .where(Transaction.user_id == current_user.id)
        .order_by(Transaction.date.desc())
        .limit(5)
    )
    recent_transactions = [
        TransactionResponse.model_validate(tx)
        for tx in db.execute(stmt_recent).scalars().all()
    ]

    stats_result = {
        "total_balance": summary["total_balance"],
        "total_income": summary["total_income"],
        "total_expenses": summary["total_expenses"],
        "savings": summary["period_savings"],
        "category_spending": summary["category_spending"],
        "monthly_trends": summary["monthly_trends"],
        "recent_transactions": recent_transactions
    }
    cache_service.set(cache_key, stats_result, ttl=60)
    return stats_result


@router.post("/bulk-delete", status_code=status.HTTP_200_OK)
def bulk_delete_transactions(
    transaction_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Bulk delete transactions and revert their account balance impacts.
    """
    stmt = select(Transaction).where(
        Transaction.id.in_(transaction_ids),
        Transaction.user_id == current_user.id
    )
    transactions = db.execute(stmt).scalars().all()
    if not transactions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No matching transactions found."
        )

    # Revert all balance changes
    impacted_budgets = set()
    for tx in transactions:
        account = db.execute(select(Account).where(Account.id == tx.account_id)).scalar_one_or_none()
        to_account = db.execute(select(Account).where(Account.id == tx.to_account_id)).scalar_one_or_none() if tx.to_account_id else None

        if account:
            if tx.type == "income":
                account.balance -= tx.amount
            elif tx.type == "expense":
                account.balance += tx.amount
            elif tx.type == "transfer":
                account.balance += tx.amount
                if to_account:
                    to_account.balance -= tx.amount

        # Store for budget sync
        if tx.category_id:
            impacted_budgets.add((tx.category_id, tx.date))

        db.delete(tx)

    db.commit()

    # Re-sync all impacted budgets
    for cat_id, dt in impacted_budgets:
        sync_budget_for_transaction(db, current_user.id, cat_id, dt)

    # Invalidate cache
    cache_service.delete(f"user:{current_user.id}:stats")
    cache_service.delete_pattern(f"user:{current_user.id}:insights*")

    return {"success": True, "deleted_count": len(transactions)}


@router.post("/bulk-update-category", status_code=status.HTTP_200_OK)
def bulk_update_category(
    transaction_ids: List[int],
    category_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Bulk update the category of multiple transactions and reconcile category budgets.
    """
    if category_id is not None:
        cat = db.execute(select(Category).where(
            Category.id == category_id,
            or_(Category.user_id == current_user.id, Category.user_id.is_(None))
        )).scalar_one_or_none()
        if not cat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found."
            )

    stmt = select(Transaction).where(
        Transaction.id.in_(transaction_ids),
        Transaction.user_id == current_user.id
    )
    transactions = db.execute(stmt).scalars().all()
    if not transactions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No matching transactions found."
        )

    impacted_budgets = set()
    for tx in transactions:
        if tx.category_id:
            impacted_budgets.add((tx.category_id, tx.date))
        
        tx.category_id = category_id
        
        if category_id:
            impacted_budgets.add((category_id, tx.date))

    db.commit()

    # Re-sync all budgets
    for cat_id, dt in impacted_budgets:
        sync_budget_for_transaction(db, current_user.id, cat_id, dt)

    # Invalidate cache
    cache_service.delete(f"user:{current_user.id}:stats")
    cache_service.delete_pattern(f"user:{current_user.id}:insights*")

    return {"success": True, "updated_count": len(transactions)}

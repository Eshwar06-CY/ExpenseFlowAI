from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func
from datetime import datetime, timezone
import calendar

from app.database.session import get_db
from app.models.budget import Budget
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.user import User
from app.schemas.planning import BudgetCreate, BudgetUpdate, BudgetResponse
from app.routers.deps import get_current_user
from app.services.cache import cache_service

router = APIRouter()

def recalculate_budget_spent(db: Session, budget: Budget) -> float:
    """
    Calculate total expenses for the budget's category and month,
    then update and commit the spent field.
    """
    try:
        # Parse month string YYYY-MM
        year, month = map(int, budget.month.split("-"))
        # Start and end datetimes for month
        _, last_day = calendar.monthrange(year, month)
        start_date = datetime(year, month, 1, 0, 0, 0)
        end_date = datetime(year, month, last_day, 23, 59, 59)
    except Exception:
        return budget.spent

    # Query sum of expenses
    stmt = select(func.sum(Transaction.amount)).where(
        Transaction.user_id == budget.user_id,
        Transaction.category_id == budget.category_id,
        Transaction.type == "expense",
        Transaction.date >= start_date,
        Transaction.date <= end_date
    )
    spent_sum = db.execute(stmt).scalar() or 0.0
    budget.spent = spent_sum
    db.commit()
    db.refresh(budget)
    return spent_sum

@router.get("/", response_model=List[BudgetResponse])
def get_budgets(
    month: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve all budgets for the current user, optionally filtered by month (YYYY-MM).
    """
    if not month:
        month = datetime.now(timezone.utc).strftime("%Y-%m")
        
    stmt = (
        select(Budget)
        .options(joinedload(Budget.category))
        .where(Budget.user_id == current_user.id, Budget.month == month)
    )
    budgets = db.execute(stmt).scalars().all()
    
    # Recalculate spent values on the fly to guarantee accuracy
    for budget in budgets:
        recalculate_budget_spent(db, budget)
        
    return budgets

@router.post("/", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
def create_budget(
    budget_in: BudgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a category budget limit for a specific month.
    """
    # Check if category exists
    stmt_cat = select(Category).where(Category.id == budget_in.category_id)
    cat = db.execute(stmt_cat).scalar_one_or_none()
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found."
        )

    # Check duplicate budget (same category and month)
    stmt_dup = select(Budget).where(
        Budget.user_id == current_user.id,
        Budget.category_id == budget_in.category_id,
        Budget.month == budget_in.month
    )
    existing = db.execute(stmt_dup).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Budget for category '{cat.name}' in month '{budget_in.month}' already configured. Edit instead."
        )

    budget = Budget(
        user_id=current_user.id,
        category_id=budget_in.category_id,
        amount=budget_in.amount,
        month=budget_in.month,
        spent=0.0
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    
    # Calculate spent amount immediately
    recalculate_budget_spent(db, budget)
    
    # Invalidate cache
    cache_service.delete(f"user:{current_user.id}:stats")
    cache_service.delete_pattern(f"user:{current_user.id}:insights*")
    
    # Reload relation fields
    stmt_reload = select(Budget).options(joinedload(Budget.category)).where(Budget.id == budget.id)
    return db.execute(stmt_reload).scalar_one()

@router.put("/{budget_id}", response_model=BudgetResponse)
def update_budget(
    budget_id: int,
    budget_in: BudgetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update budget limit amount.
    """
    stmt = select(Budget).where(Budget.id == budget_id, Budget.user_id == current_user.id)
    budget = db.execute(stmt).scalar_one_or_none()
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found."
        )

    budget.amount = budget_in.amount
    db.commit()
    db.refresh(budget)
    
    recalculate_budget_spent(db, budget)
    
    # Invalidate cache
    cache_service.delete(f"user:{current_user.id}:stats")
    cache_service.delete_pattern(f"user:{current_user.id}:insights*")
    
    stmt_reload = select(Budget).options(joinedload(Budget.category)).where(Budget.id == budget.id)
    return db.execute(stmt_reload).scalar_one()

@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a budget limit.
    """
    stmt = select(Budget).where(Budget.id == budget_id, Budget.user_id == current_user.id)
    budget = db.execute(stmt).scalar_one_or_none()
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found."
        )
        
    db.delete(budget)
    db.commit()
    
    # Invalidate cache
    cache_service.delete(f"user:{current_user.id}:stats")
    cache_service.delete_pattern(f"user:{current_user.id}:insights*")
    return

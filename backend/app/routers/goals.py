from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database.session import get_db
from app.models.goal import Goal
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.planning import GoalCreate, GoalUpdate, GoalResponse
from app.routers.deps import get_current_user
from app.services.cache import cache_service
from datetime import datetime, timezone

router = APIRouter()

@router.get("/", response_model=List[GoalResponse])
def get_goals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve all savings goals for the user.
    """
    stmt = select(Goal).where(Goal.user_id == current_user.id)
    return db.execute(stmt).scalars().all()

@router.post("/", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal(
    goal_in: GoalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new savings goal.
    """
    goal = Goal(
        user_id=current_user.id,
        name=goal_in.name,
        target_amount=goal_in.target_amount,
        current_amount=goal_in.current_amount,
        target_date=goal_in.target_date
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    
    # Invalidate cache
    cache_service.delete(f"user:{current_user.id}:stats")
    cache_service.delete_pattern(f"user:{current_user.id}:insights*")
    return goal

@router.put("/{goal_id}", response_model=GoalResponse)
def update_goal(
    goal_id: int,
    goal_in: GoalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a savings goal.
    """
    stmt = select(Goal).where(Goal.id == goal_id, Goal.user_id == current_user.id)
    goal = db.execute(stmt).scalar_one_or_none()
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Savings goal not found."
        )
        
    update_data = goal_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(goal, field, value)
        
    db.commit()
    db.refresh(goal)
    
    # Invalidate cache
    cache_service.delete(f"user:{current_user.id}:stats")
    cache_service.delete_pattern(f"user:{current_user.id}:insights*")
    return goal

@router.post("/{goal_id}/contribute", response_model=GoalResponse)
def contribute_to_goal(
    goal_id: int,
    amount: float,
    account_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add funds to a savings goal, optionally debiting from a bank account.
    """
    stmt = select(Goal).where(Goal.id == goal_id, Goal.user_id == current_user.id)
    goal = db.execute(stmt).scalar_one_or_none()
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Savings goal not found."
        )

    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contribution amount must be positive."
        )

    if account_id:
        stmt_acct = select(Account).where(Account.id == account_id, Account.user_id == current_user.id)
        account = db.execute(stmt_acct).scalar_one_or_none()
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found."
            )
            
        # Deduct balance
        account.balance -= amount
        
        # Log transaction
        tx = Transaction(
            user_id=current_user.id,
            type="expense",
            amount=amount,
            description=f"Goal contribution: {goal.name}",
            date=datetime.now(timezone.utc),
            account_id=account.id
        )
        db.add(tx)

    goal.current_amount += amount
    db.commit()
    db.refresh(goal)
    
    # Invalidate cache
    cache_service.delete(f"user:{current_user.id}:stats")
    cache_service.delete_pattern(f"user:{current_user.id}:insights*")
    return goal

@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a savings goal.
    """
    stmt = select(Goal).where(Goal.id == goal_id, Goal.user_id == current_user.id)
    goal = db.execute(stmt).scalar_one_or_none()
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Savings goal not found."
        )
        
    db.delete(goal)
    db.commit()
    
    # Invalidate cache
    cache_service.delete(f"user:{current_user.id}:stats")
    cache_service.delete_pattern(f"user:{current_user.id}:insights*")
    return

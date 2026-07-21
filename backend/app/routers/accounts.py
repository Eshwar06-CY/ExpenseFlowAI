from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database.session import get_db
from app.models.account import Account
from app.models.user import User
from app.schemas.account import AccountCreate, AccountUpdate, AccountResponse
from app.routers.deps import get_current_user

router = APIRouter()

@router.get("/", response_model=List[AccountResponse])
def get_accounts(
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve all accounts for the authenticated user.
    """
    stmt = select(Account).where(Account.user_id == current_user.id)
    if q:
        stmt = stmt.where(Account.name.ilike(f"%{q}%"))
    
    result = db.execute(stmt)
    return result.scalars().all()

@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(
    account_in: AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new account for the authenticated user.
    """
    account = Account(
        user_id=current_user.id,
        name=account_in.name,
        type=account_in.type,
        balance=account_in.balance,
        currency=account_in.currency
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account

@router.put("/{account_id}", response_model=AccountResponse)
def update_account(
    account_id: int,
    account_in: AccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an account's details.
    """
    stmt = select(Account).where(Account.id == account_id, Account.user_id == current_user.id)
    account = db.execute(stmt).scalar_one_or_none()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found."
        )
    
    update_data = account_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(account, field, value)
        
    db.commit()
    db.refresh(account)
    return account

@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete an account.
    """
    stmt = select(Account).where(Account.id == account_id, Account.user_id == current_user.id)
    account = db.execute(stmt).scalar_one_or_none()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found."
        )
    
    db.delete(account)
    db.commit()
    return

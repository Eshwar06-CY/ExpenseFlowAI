import json
from io import BytesIO
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.security import verify_password, get_password_hash
from app.database.session import get_db
from app.models.user import User
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.budget import Budget
from app.models.goal import Goal
from app.models.bill import Bill
from app.models.notification import Notification
from app.routers.deps import get_current_user

router = APIRouter()


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)


class AccountDeleteRequest(BaseModel):
    password: str = Field(..., min_length=1)
    confirmation: str = Field(..., description="Must be 'DELETE MY ACCOUNT'")


@router.put("/password")
def change_password(
    data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change the current user's password. Requires current password verification."""
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )
    if data.new_password != data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password and confirmation do not match.",
        )
    if data.current_password == data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password.",
        )

    current_user.password_hash = get_password_hash(data.new_password)
    db.add(current_user)
    db.commit()
    return {"success": True, "message": "Password updated successfully."}


@router.post("/export-data")
def export_user_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export all user data as a JSON download."""
    # Gather all user data
    accounts = db.execute(
        select(Account).where(Account.user_id == current_user.id)
    ).scalars().all()

    transactions = db.execute(
        select(Transaction).where(Transaction.user_id == current_user.id).order_by(Transaction.date.desc())
    ).scalars().all()

    categories = db.execute(
        select(Category).where(Category.user_id == current_user.id)
    ).scalars().all()

    budgets = db.execute(
        select(Budget).where(Budget.user_id == current_user.id)
    ).scalars().all()

    goals = db.execute(
        select(Goal).where(Goal.user_id == current_user.id)
    ).scalars().all()

    bills = db.execute(
        select(Bill).where(Bill.user_id == current_user.id)
    ).scalars().all()

    data = {
        "export_date": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "created_at": str(current_user.created_at) if current_user.created_at else None,
        },
        "accounts": [
            {"name": a.name, "type": a.type, "balance": float(a.balance), "currency": a.currency}
            for a in accounts
        ],
        "categories": [
            {"name": c.name, "type": c.type, "color": c.color, "icon": c.icon}
            for c in categories
        ],
        "transactions": [
            {
                "date": str(t.date) if t.date else None,
                "type": t.type,
                "amount": float(t.amount),
                "description": t.description,
                "account_id": t.account_id,
                "to_account_id": t.to_account_id,
            }
            for t in transactions
        ],
        "budgets": [
            {"month": b.month, "amount": float(b.amount), "spent": float(b.spent)}
            for b in budgets
        ],
        "goals": [
            {
                "name": g.name,
                "target_amount": float(g.target_amount),
                "current_amount": float(g.current_amount),
                "target_date": str(g.target_date) if g.target_date else None,
            }
            for g in goals
        ],
        "bills": [
            {
                "name": b.name,
                "amount": float(b.amount),
                "due_date": str(b.due_date) if b.due_date else None,
                "is_paid": b.is_paid,
            }
            for b in bills
        ],
    }

    json_str = json.dumps(data, indent=2, default=str)
    buffer = BytesIO(json_str.encode("utf-8"))
    buffer.seek(0)

    filename = f"expenseflow_data_export_{datetime.now().strftime('%Y%m%d')}.json"
    return StreamingResponse(
        buffer,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.delete("/account")
def delete_account(
    data: AccountDeleteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Soft-delete user account. Requires password and typed confirmation."""
    if data.confirmation != "DELETE MY ACCOUNT":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please type 'DELETE MY ACCOUNT' to confirm.",
        )
    if not verify_password(data.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is incorrect.",
        )

    # Soft-delete: deactivate the account
    current_user.is_active = False
    db.add(current_user)
    db.commit()
    return {"success": True, "message": "Account has been deactivated."}

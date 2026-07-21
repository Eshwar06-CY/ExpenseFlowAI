from typing import Dict, List, Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, or_

from app.database.session import get_db
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.bill import Bill
from app.models.goal import Goal
from app.models.category import Category
from app.models.notification import Notification
from app.models.user import User
from app.models.workspace import WorkspaceMember
from app.routers.deps import get_current_user

router = APIRouter()

@router.get("/")
def search_global(
    q: str = Query(..., min_length=2, description="The search term"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, List[Any]]:
    """
    Search across multiple database entities (Accounts, Transactions, Bills, Goals, Categories, Notifications)
    and return grouped results matching the query string.
    """
    search_pattern = f"%{q}%"

    # 1. Search Accounts
    acc_stmt = select(Account).where(
        Account.user_id == current_user.id,
        Account.name.ilike(search_pattern)
    )
    accounts = db.execute(acc_stmt).scalars().all()
    accounts_res = [
        {"id": a.id, "name": a.name, "type": a.type, "balance": a.balance, "currency": a.currency}
        for a in accounts
    ]

    # 2. Search Transactions
    tx_stmt = (
        select(Transaction)
        .options(joinedload(Transaction.category))
        .where(
            Transaction.user_id == current_user.id,
            or_(
                Transaction.description.ilike(search_pattern),
                Transaction.type.ilike(search_pattern)
            )
        )
        .order_by(Transaction.date.desc())
        .limit(30)
    )
    transactions = db.execute(tx_stmt).scalars().all()
    transactions_res = [
        {
            "id": t.id,
            "description": t.description,
            "type": t.type,
            "amount": t.amount,
            "date": t.date.isoformat(),
            "category": t.category.name if t.category else "Uncategorized"
        }
        for t in transactions
    ]

    # 3. Search Bills
    bill_stmt = select(Bill).where(
        Bill.user_id == current_user.id,
        Bill.name.ilike(search_pattern)
    )
    bills = db.execute(bill_stmt).scalars().all()
    bills_res = [
        {"id": b.id, "name": b.name, "amount": b.amount, "due_date": b.due_date.isoformat(), "is_paid": b.is_paid}
        for b in bills
    ]

    # 4. Search Goals
    goal_stmt = select(Goal).where(
        Goal.user_id == current_user.id,
        Goal.name.ilike(search_pattern)
    )
    goals = db.execute(goal_stmt).scalars().all()
    goals_res = [
        {
            "id": g.id,
            "name": g.name,
            "target_amount": g.target_amount,
            "current_amount": g.current_amount,
            "target_date": g.target_date.isoformat() if g.target_date else None
        }
        for g in goals
    ]

    # 5. Search Categories
    cat_stmt = select(Category).where(
        or_(
            Category.user_id == current_user.id,
            Category.user_id.is_(None)
        ),
        Category.name.ilike(search_pattern)
    )
    categories = db.execute(cat_stmt).scalars().all()
    categories_res = [
        {"id": c.id, "name": c.name, "type": c.type, "icon": c.icon, "color": c.color}
        for c in categories
    ]

    # 6. Search Notifications
    notif_stmt = select(Notification).where(
        Notification.user_id == current_user.id,
        or_(
            Notification.title.ilike(search_pattern),
            Notification.message.ilike(search_pattern)
        )
    ).order_by(Notification.created_at.desc()).limit(20)
    notifications = db.execute(notif_stmt).scalars().all()
    notifications_res = [
        {"id": n.id, "title": n.title, "message": n.message, "is_read": n.is_read, "created_at": n.created_at.isoformat()}
        for n in notifications
    ]

    # 7. Search Workspace Members
    ws_stmt = select(WorkspaceMember.workspace_id).where(
        WorkspaceMember.user_id == current_user.id,
        WorkspaceMember.is_accepted == True
    )
    ws_ids = db.execute(ws_stmt).scalars().all()
    members_res = []
    if ws_ids:
        mem_stmt = (
            select(User)
            .join(WorkspaceMember, WorkspaceMember.user_id == User.id)
            .where(
                WorkspaceMember.workspace_id.in_(ws_ids),
                User.id != current_user.id,
                or_(
                    User.full_name.ilike(search_pattern),
                    User.email.ilike(search_pattern)
                )
            )
            .distinct()
        )
        members = db.execute(mem_stmt).scalars().all()
        members_res = [
            {"id": m.id, "name": m.full_name or m.email.split("@")[0], "email": m.email}
            for m in members
        ]

    return {
        "accounts": accounts_res,
        "transactions": transactions_res,
        "bills": bills_res,
        "goals": goals_res,
        "categories": categories_res,
        "notifications": notifications_res,
        "members": members_res
    }

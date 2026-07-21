from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from app.database.session import get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.planning import NotificationResponse
from app.routers.deps import get_current_user

router = APIRouter()

@router.get("/", response_model=List[NotificationResponse])
def get_notifications(
    is_read: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve all notifications for the authenticated user.
    """
    stmt = select(Notification).where(Notification.user_id == current_user.id)
    if is_read is not None:
        stmt = stmt.where(Notification.is_read == is_read)
    stmt = stmt.order_by(Notification.created_at.desc())
    return db.execute(stmt).scalars().all()

@router.put("/read-all", response_model=dict)
def mark_all_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark all unread notifications as read.
    """
    stmt = (
        update(Notification)
        .where(Notification.user_id == current_user.id, Notification.is_read == False)
        .values(is_read=True)
    )
    db.execute(stmt)
    db.commit()
    return {"success": True, "message": "All notifications marked as read."}

@router.put("/{notification_id}/read", response_model=NotificationResponse)
def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark a specific notification as read.
    """
    stmt = select(Notification).where(Notification.id == notification_id, Notification.user_id == current_user.id)
    notification = db.execute(stmt).scalar_one_or_none()
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found."
        )

    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification

@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a notification.
    """
    stmt = select(Notification).where(Notification.id == notification_id, Notification.user_id == current_user.id)
    notification = db.execute(stmt).scalar_one_or_none()
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found."
        )

    db.delete(notification)
    db.commit()
    return

@router.post("/bulk-read", response_model=dict)
def bulk_read_notifications(
    notification_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark multiple notifications as read."""
    stmt = (
        update(Notification)
        .where(Notification.user_id == current_user.id, Notification.id.in_(notification_ids))
        .values(is_read=True)
    )
    db.execute(stmt)
    db.commit()
    return {"success": True, "message": f"{len(notification_ids)} notifications marked as read."}

@router.post("/bulk-delete", response_model=dict)
def bulk_delete_notifications(
    notification_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete multiple notifications."""
    from sqlalchemy import delete
    stmt = (
        delete(Notification)
        .where(Notification.user_id == current_user.id, Notification.id.in_(notification_ids))
    )
    db.execute(stmt)
    db.commit()
    return {"success": True, "message": f"{len(notification_ids)} notifications deleted."}

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def delete_all_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete all notifications for the current user."""
    from sqlalchemy import delete
    stmt = delete(Notification).where(Notification.user_id == current_user.id)
    db.execute(stmt)
    db.commit()
    return

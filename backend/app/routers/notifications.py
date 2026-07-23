"""
Notifications API Router - ExpenseFlowAI

Endpoints:
- GET /api/v1/notifications (List smart notifications)
- PATCH / PUT /api/v1/notifications/{id}/read (Mark single read)
- PATCH / PUT /api/v1/notifications/read-all (Mark all read)
- DELETE /api/v1/notifications/{id} (Delete notification)
- GET /api/v1/notifications/preferences (Get delivery settings)
- PUT /api/v1/notifications/preferences (Update delivery settings)
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.routers.deps import get_current_user
from app.services.notification_service import NotificationService, NotificationPreferenceService

router = APIRouter()


@router.get("/", summary="List User Notifications")
def get_notifications(
    category: Optional[str] = Query(None, description="Filter category: budget, bills, goals, forecast, ai, security, system, achievements"),
    priority: Optional[str] = Query(None, description="Filter priority: critical, high, medium, low"),
    unread_only: bool = Query(False, description="Filter unread notifications only"),
    search: Optional[str] = Query(None, description="Search query string"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    return NotificationService.list_notifications(
        db=db,
        user_id=current_user.id,
        category=category,
        priority=priority,
        unread_only=unread_only,
        search=search,
        limit=limit,
        offset=offset
    )


@router.patch("/{notification_id}/read", summary="Mark Notification as Read (PATCH)")
@router.put("/{notification_id}/read", summary="Mark Notification as Read (PUT)")
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    notif = NotificationService.mark_as_read(db=db, user_id=current_user.id, notification_id=notification_id)
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found."
        )
    return {"success": True, "id": notif.id, "is_read": True}


@router.patch("/read-all", summary="Mark All Notifications as Read (PATCH)")
@router.put("/read-all", summary="Mark All Notifications as Read (PUT)")
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    count = NotificationService.mark_all_as_read(db=db, user_id=current_user.id)
    return {"success": True, "marked_count": count}


@router.delete("/{notification_id}", summary="Delete Notification")
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    success = NotificationService.delete_notification(db=db, user_id=current_user.id, notification_id=notification_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found."
        )
    return {"success": True, "message": "Notification deleted."}


@router.get("/preferences", summary="Get Notification Preferences")
def get_notification_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    pref = NotificationPreferenceService.get_or_create_preferences(db=db, user_id=current_user.id)
    return {
        "id": pref.id,
        "user_id": pref.user_id,
        "enable_budget_alerts": pref.enable_budget_alerts,
        "enable_bill_reminders": pref.enable_bill_reminders,
        "enable_goal_updates": pref.enable_goal_updates,
        "enable_forecast_warnings": pref.enable_forecast_warnings,
        "enable_ai_recommendations": pref.enable_ai_recommendations,
        "enable_security_alerts": pref.enable_security_alerts,
        "enable_achievements": pref.enable_achievements,
        "enable_email_notifications": pref.enable_email_notifications,
        "enable_in_app": pref.enable_in_app,
        "digest_frequency": pref.digest_frequency
    }


@router.put("/preferences", summary="Update Notification Preferences")
def update_notification_preferences(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    pref = NotificationPreferenceService.update_preferences(
        db=db,
        user_id=current_user.id,
        updates=payload
    )
    return {
        "success": True,
        "preferences": {
            "id": pref.id,
            "enable_budget_alerts": pref.enable_budget_alerts,
            "enable_bill_reminders": pref.enable_bill_reminders,
            "enable_goal_updates": pref.enable_goal_updates,
            "enable_forecast_warnings": pref.enable_forecast_warnings,
            "enable_ai_recommendations": pref.enable_ai_recommendations,
            "enable_security_alerts": pref.enable_security_alerts,
            "enable_achievements": pref.enable_achievements,
            "enable_email_notifications": pref.enable_email_notifications,
            "enable_in_app": pref.enable_in_app,
            "digest_frequency": pref.digest_frequency
        }
    }

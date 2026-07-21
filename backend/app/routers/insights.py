from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import date

from app.database.session import get_db
from app.models.insight import FinancialInsight, FinancialEvent, DailyBriefing
from app.models.user import User
from app.schemas.intelligence_schemas import FinancialInsightResponse, FinancialEventResponse, DailyBriefingResponse
from app.services.intelligence import InsightsEngine
from app.routers.deps import get_current_user
from app.services.cache import cache_service

router = APIRouter()

@router.post("/generate", status_code=status.HTTP_200_OK)
def trigger_generation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Triggers the InsightsEngine to regenerate insights, events, and daily briefings.
    """
    insights = InsightsEngine.generate_insights(db, current_user.id)
    InsightsEngine.detect_events(db, current_user.id)
    InsightsEngine.generate_daily_briefing(db, current_user.id)
    
    # Invalidate cache
    cache_service.delete_pattern(f"user:{current_user.id}:insights*")
    cache_service.delete(f"user:{current_user.id}:stats")
    return {"success": True, "insights_count": len(insights)}

@router.get("/", response_model=List[FinancialInsightResponse])
def get_insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve all generated financial insights for the user.
    """
    cache_key = f"user:{current_user.id}:insights:list"
    cached = cache_service.get(cache_key)
    if cached is not None:
        return cached

    stmt = select(FinancialInsight).where(FinancialInsight.user_id == current_user.id).order_by(FinancialInsight.created_at.desc())
    insights = db.execute(stmt).scalars().all()
    
    # If empty, generate them on the fly
    if not insights:
        insights = InsightsEngine.generate_insights(db, current_user.id)
        
    cache_service.set(cache_key, insights, ttl=300)
    return insights

@router.get("/events", response_model=List[FinancialEventResponse])
def get_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve active (undismissed) financial events and alerts.
    """
    cache_key = f"user:{current_user.id}:insights:events"
    cached = cache_service.get(cache_key)
    if cached is not None:
        return cached

    stmt = select(FinancialEvent).where(
        FinancialEvent.user_id == current_user.id,
        FinancialEvent.is_dismissed == False
    ).order_by(FinancialEvent.event_date.desc())
    events = db.execute(stmt).scalars().all()
    
    # If no events exist at all for user, detect them on the fly
    stmt_any = select(FinancialEvent).where(FinancialEvent.user_id == current_user.id)
    any_events = db.execute(stmt_any).scalars().all()
    if not any_events:
        events = InsightsEngine.detect_events(db, current_user.id)
        
    cache_service.set(cache_key, events, ttl=300)
    return events

@router.post("/events/{event_id}/dismiss", response_model=FinancialEventResponse)
def dismiss_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Dismiss a specific financial event/warning from dashboard list.
    """
    stmt = select(FinancialEvent).where(FinancialEvent.id == event_id, FinancialEvent.user_id == current_user.id)
    event = db.execute(stmt).scalar_one_or_none()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial event not found."
        )

    event.is_dismissed = True
    db.commit()
    db.refresh(event)
    cache_service.delete_pattern(f"user:{current_user.id}:insights*")
    return event

@router.get("/briefing/daily", response_model=DailyBriefingResponse)
def get_daily_briefing(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve the structured daily briefing packet for today.
    """
    cache_key = f"user:{current_user.id}:insights:briefing"
    cached = cache_service.get(cache_key)
    if cached is not None:
        return cached

    today_date = date.today()
    stmt = select(DailyBriefing).where(DailyBriefing.user_id == current_user.id, DailyBriefing.date == today_date)
    briefing = db.execute(stmt).scalar_one_or_none()
    
    # Generate on the fly if not exists
    if not briefing:
        briefing = InsightsEngine.generate_daily_briefing(db, current_user.id)
        
    cache_service.set(cache_key, briefing, ttl=300)
    return briefing

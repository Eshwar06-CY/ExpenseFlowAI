"""
Personalization Service - ExpenseFlowAI Personalization & Privacy Center

Responsible for:
- Loading and updating user AI personalization settings.
- Managing learned behavioral observations and confidence metrics.
- Formatting structured AI personalization context for prompt injection.
"""

import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.personalization import AIPersonalizationSettings
from app.models.user_behavior import UserLearnedBehavior
from app.schemas.personalization import PersonalizationPreferencesUpdate

logger = logging.getLogger(__name__)


class PersonalizationService:
    @staticmethod
    def get_or_create_settings(db: Session, user_id: int) -> AIPersonalizationSettings:
        """
        Fetches or initializes user personalization settings.
        """
        settings = db.execute(
            select(AIPersonalizationSettings).where(AIPersonalizationSettings.user_id == user_id)
        ).scalar_one_or_none()

        if not settings:
            settings = AIPersonalizationSettings(
                user_id=user_id,
                enable_ai_personalization=True,
                enable_ai_learning=True,
                coaching_style="professional",
                recommendation_frequency="daily",
                response_detail="balanced",
                enable_smart_suggestions=True,
                enable_goal_recommendations=True,
                enable_spending_insights=True,
                enable_memory=True,
                enable_behavior_tracking=True,
                enable_goal_tracking=True,
                enable_communication_preference_learning=True
            )
            db.add(settings)
            db.commit()
            db.refresh(settings)

        return settings

    @staticmethod
    def seed_default_behaviors_if_empty(db: Session, user_id: int) -> List[UserLearnedBehavior]:
        """
        Seeds baseline learned behaviors if user has no existing observation cards.
        """
        existing = db.execute(
            select(UserLearnedBehavior).where(
                UserLearnedBehavior.user_id == user_id,
                UserLearnedBehavior.is_active == True
            )
        ).scalars().all()

        if existing:
            return existing

        default_seeds = [
            {"category": "Dining", "observation": "Frequently exceeds budget.", "confidence": 0.91},
            {"category": "Savings", "observation": "Usually saves more than predicted.", "confidence": 0.88},
            {"category": "Bills", "observation": "Pays bills early.", "confidence": 0.97},
            {"category": "Goals", "observation": "Completes short-term goals consistently.", "confidence": 0.84}
        ]

        seeds = []
        for seed in default_seeds:
            b = UserLearnedBehavior(
                user_id=user_id,
                category=seed["category"],
                observation=seed["observation"],
                confidence=seed["confidence"],
                is_active=True
            )
            db.add(b)
            seeds.append(b)

        db.commit()
        for b in seeds:
            db.refresh(b)

        return seeds

    @staticmethod
    def get_personalization_overview(db: Session, user_id: int) -> Dict[str, Any]:
        """
        Returns full personalization overview for API response.
        """
        settings = PersonalizationService.get_or_create_settings(db, user_id)
        behaviors = PersonalizationService.seed_default_behaviors_if_empty(db, user_id)

        # Calculate overall confidence score
        if behaviors:
            avg_conf = sum(b.confidence for b in behaviors) / len(behaviors)
            confidence = round(avg_conf, 2)
        else:
            confidence = 0.92

        prefs_dict = {
            "enable_ai_personalization": settings.enable_ai_personalization,
            "enable_ai_learning": settings.enable_ai_learning,
            "coaching_style": settings.coaching_style,
            "recommendation_frequency": settings.recommendation_frequency,
            "response_detail": settings.response_detail,
            "enable_smart_suggestions": settings.enable_smart_suggestions,
            "enable_goal_recommendations": settings.enable_goal_recommendations,
            "enable_spending_insights": settings.enable_spending_insights,
            "enable_memory": settings.enable_memory,
            "enable_behavior_tracking": settings.enable_behavior_tracking,
            "enable_goal_tracking": settings.enable_goal_tracking,
            "enable_communication_preference_learning": settings.enable_communication_preference_learning
        }

        behavior_items = [
            {
                "id": b.id,
                "category": b.category,
                "observation": b.observation,
                "confidence": b.confidence,
                "created_at": b.created_at.isoformat() if b.created_at else None
            }
            for b in behaviors
        ]

        return {
            "learning_enabled": settings.enable_ai_learning,
            "memory_enabled": settings.enable_memory,
            "confidence": confidence,
            "preferences": prefs_dict,
            "behaviors": behavior_items
        }

    @staticmethod
    def update_preferences(
        db: Session,
        user_id: int,
        updates: PersonalizationPreferencesUpdate
    ) -> AIPersonalizationSettings:
        """
        Updates user AI personalization settings.
        """
        settings = PersonalizationService.get_or_create_settings(db, user_id)

        for field, value in updates.model_dump(exclude_unset=True).items():
            if value is not None and hasattr(settings, field):
                setattr(settings, field, value)

        db.commit()
        db.refresh(settings)
        return settings

    @staticmethod
    def delete_behavior(db: Session, user_id: int, behavior_id: int) -> bool:
        """
        Deletes a specific learned behavior observation ("Forget This Behavior").
        Validates ownership before deletion.
        """
        behavior = db.execute(
            select(UserLearnedBehavior).where(
                UserLearnedBehavior.id == behavior_id,
                UserLearnedBehavior.user_id == user_id
            )
        ).scalar_one_or_none()

        if not behavior:
            return False

        db.delete(behavior)
        db.commit()
        return True

    @staticmethod
    def get_personalization_prompt_context(db: Session, user_id: int) -> str:
        """
        Generates structured prompt context snippet for injection into Ollama LLM requests.
        """
        settings = PersonalizationService.get_or_create_settings(db, user_id)
        if not settings.enable_ai_personalization:
            return "USER PERSONALIZATION: Disabled by user privacy preferences."

        behaviors = db.execute(
            select(UserLearnedBehavior).where(
                UserLearnedBehavior.user_id == user_id,
                UserLearnedBehavior.is_active == True
            )
        ).scalars().all()

        b_strs = [f"- {b.category}: {b.observation} (Confidence: {int(b.confidence * 100)}%)" for b in behaviors]
        behaviors_context = "\n".join(b_strs) if b_strs else "None recorded."

        return f"""
USER PERSONALIZATION CONTEXT:
- Coaching Style: {settings.coaching_style.capitalize()}
- Response Detail Level: {settings.response_detail.capitalize()}
- Recommendation Frequency: {settings.recommendation_frequency.replace('_', ' ').capitalize()}
LEARNED BEHAVIORS:
{behaviors_context}
"""

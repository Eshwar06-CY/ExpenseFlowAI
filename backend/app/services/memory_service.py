"""
AI Persistent Memory Service - ExpenseFlowAI

Manages structured user memories (financial goals, preferences, lifestyle context, decisions).
Ranks relevant memories for prompt context injection while respecting user privacy controls.
"""

from datetime import datetime, timezone
import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_

from app.models.memory import AIMemory

logger = logging.getLogger(__name__)


class AIMemoryService:
    @staticmethod
    def remember(
        db: Session,
        user_id: int,
        category: str,
        key: str,
        value: str,
        confidence: float = 1.0
    ) -> AIMemory:
        """
        Upserts a structured memory record for a user.
        If a memory with (user_id, category, key) exists, it is updated.
        """
        stmt = select(AIMemory).where(
            and_(
                AIMemory.user_id == user_id,
                AIMemory.category == category,
                AIMemory.key == key
            )
        )
        existing = db.execute(stmt).scalar_one_or_none()

        now = datetime.now(timezone.utc)
        if existing:
            existing.value = value
            existing.confidence = confidence
            existing.is_active = True
            existing.updated_at = now
            db.commit()
            db.refresh(existing)
            logger.info("Updated existing memory record id=%d for user=%d.", existing.id, user_id)
            return existing
        else:
            memory = AIMemory(
                user_id=user_id,
                category=category,
                key=key,
                value=value,
                confidence=confidence,
                is_active=True,
                created_at=now,
                updated_at=now
            )
            db.add(memory)
            db.commit()
            db.refresh(memory)
            logger.info("Created new memory record id=%d for user=%d.", memory.id, user_id)
            return memory

    @staticmethod
    def get_memories(
        db: Session,
        user_id: int,
        category: Optional[str] = None,
        active_only: bool = True
    ) -> List[AIMemory]:
        """
        Returns all memories stored for a user, optionally filtered by category.
        """
        conditions = [AIMemory.user_id == user_id]
        if active_only:
            conditions.append(AIMemory.is_active == True)
        if category:
            conditions.append(AIMemory.category == category)

        stmt = select(AIMemory).where(and_(*conditions)).order_by(AIMemory.updated_at.desc())
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def get_relevant_memories(
        db: Session,
        user_id: int,
        query_text: str = "",
        limit: int = 10
    ) -> List[AIMemory]:
        """
        Ranks and retrieves top relevant active memories for prompt context injection.
        Capped strictly at `limit` (default 10).
        """
        stmt = select(AIMemory).where(
            and_(
                AIMemory.user_id == user_id,
                AIMemory.is_active == True
            )
        ).order_by(AIMemory.confidence.desc(), AIMemory.updated_at.desc())

        all_active = list(db.execute(stmt).scalars().all())

        if not query_text:
            return all_active[:limit]

        # Simple keyword ranking strategy
        query_tokens = set(query_text.lower().split())
        scored = []
        for mem in all_active:
            content = f"{mem.category} {mem.key} {mem.value}".lower()
            overlap = sum(1 for token in query_tokens if token in content)
            scored.append((overlap, mem))

        # Sort by overlap score descending, then by memory confidence
        scored.sort(key=lambda x: (x[0], x[1].confidence), reverse=True)
        return [mem for _, mem in scored[:limit]]

    @staticmethod
    def update_memory(
        db: Session,
        user_id: int,
        memory_id: int,
        value: Optional[str] = None,
        confidence: Optional[float] = None,
        is_active: Optional[bool] = None
    ) -> Optional[AIMemory]:
        """
        Updates an existing memory record owned by user_id.
        """
        stmt = select(AIMemory).where(and_(AIMemory.id == memory_id, AIMemory.user_id == user_id))
        memory = db.execute(stmt).scalar_one_or_none()
        if not memory:
            return None

        if value is not None:
            memory.value = value
        if confidence is not None:
            memory.confidence = confidence
        if is_active is not None:
            memory.is_active = is_active
        memory.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(memory)
        return memory

    @staticmethod
    def delete_memory(db: Session, user_id: int, memory_id: int) -> bool:
        """
        Deletes a memory record owned by user_id.
        """
        stmt = select(AIMemory).where(and_(AIMemory.id == memory_id, AIMemory.user_id == user_id))
        memory = db.execute(stmt).scalar_one_or_none()
        if not memory:
            return False

        db.delete(memory)
        db.commit()
        return True

    @staticmethod
    def export_memories(db: Session, user_id: int) -> Dict[str, Any]:
        """
        Exports all active and inactive memories stored for a user as JSON format.
        """
        memories = AIMemoryService.get_memories(db, user_id, active_only=False)
        return {
            "user_id": user_id,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "total_memories": len(memories),
            "memories": memories
        }

"""
Conversation Manager Module - ExpenseFlowAI Multi-Stage Reasoning Pipeline

Manages multi-turn conversation history, tracks entity state persistence across turns,
and constructs clean conversation context strings for LLM prompts.
"""

import logging
from typing import Dict, Any, List, Optional
from app.ai.entity_extractor import EntityExtractor, ExtractedEntities

logger = logging.getLogger(__name__)


class ConversationManager:
    @classmethod
    def format_history_block(
        cls,
        chat_history: Optional[List[Dict[str, str]]] = None,
        max_turns: int = 6
    ) -> str:
        """
        Formats recent turns into clean markdown text for prompt injection.
        """
        if not chat_history:
            return ""

        recent_turns = chat_history[-max_turns:]
        lines = []
        for msg in recent_turns:
            role = "User" if msg.get("role") in ("user", "human") else "Assistant"
            content = (msg.get("content") or "").strip()
            if content:
                lines.append(f"{role}: {content}")

        if not lines:
            return ""

        return "PREVIOUS CONVERSATION CONTEXT:\n" + "\n".join(lines) + "\n\n"

    @classmethod
    def accumulate_entities(
        cls,
        user_message: str,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> ExtractedEntities:
        """
        Extracts entities across past turns to retain active goal context (e.g. target amount from turn 1, timeline from turn 2).
        """
        return EntityExtractor.extract(user_message=user_message, chat_history=chat_history)

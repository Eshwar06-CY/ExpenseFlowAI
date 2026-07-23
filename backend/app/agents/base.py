"""
BaseAgent Abstract Class - ExpenseFlowAI Multi-Agent Architecture

Defines the core interface for specialized domain AI agents.
Each agent has dedicated expertise, system prompt, tool bindings, and output structure.
"""

from abc import ABC, abstractmethod
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.ai.provider import LLMProvider
from app.ai.factory import get_llm_provider

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    name: str = "BaseAgent"
    description: str = "Abstract Base Agent"
    capabilities: List[str] = []

    def __init__(self, provider: Optional[LLMProvider] = None):
        self.provider = provider or get_llm_provider()

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Dedicated domain system prompt for the agent."""
        pass

    @abstractmethod
    def run(self, db: Session, user_id: int, message: str, period: str = "30d") -> Dict[str, Any]:
        """
        Executes domain agent logic and returns structured output dict.
        Output MUST include keys: 'summary', 'confidence', 'data'.
        """
        pass

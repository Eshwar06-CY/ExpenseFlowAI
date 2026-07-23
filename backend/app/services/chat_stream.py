"""
Chat Stream Service - ExpenseFlowAI Multi-Stage Real-Time Streaming AI Chat

Provides Server-Sent Events (SSE) token-by-token streaming response generation:
- Executes Multi-Stage Reasoning Pipeline (Intent -> Entity -> TaskPlanner -> Decision -> Prompt -> Validator).
- Asks interactive clarification questions when missing information is detected.
- Streams token chunks from Google Gemini 3.6 Flash / Hybrid LLM Provider.
- Yields SSE formatted JSON events:
    data: {"type": "token", "content": "..."}
    data: {"type": "done"}
    data: {"type": "error", "message": "..."}
"""

import json
import logging
import asyncio
from typing import AsyncGenerator, Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.services.finance_engine import FinanceEngine
from app.services.memory_service import AIMemoryService
from app.services.personalization_service import PersonalizationService
from app.ai.prompt_builder import PromptBuilder, PipelineContext
from app.ai.response_validator import ResponseValidator
from app.ai.provider import LLMProvider
from app.ai.factory import get_llm_provider
from app.ai.templates import TemplateEngine

logger = logging.getLogger(__name__)


class ChatStreamService:
    def __init__(self, provider: Optional[LLMProvider] = None):
        self.provider = provider or get_llm_provider()

    async def stream_chat_response(
        self,
        db: Session,
        user_id: int,
        user_message: str,
        period: str = "30d",
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Asynchronously streams SSE formatted tokens based on multi-stage pipeline reasoning.
        """
        try:
            # 1. First-pass intent check to determine if DB read is needed
            pipeline_pre = PromptBuilder.run_pipeline(
                user_message=user_message,
                chat_history=chat_history or []
            )

            # 2. Fetch verified financial metrics ONLY if Decision Engine requests DB metrics
            summary = None
            if pipeline_pre.decision.use_finance_engine:
                summary = FinanceEngine.get_dashboard_summary(db, user_id=user_id, period=period)

            # 3. Fetch persistent user memories & personalization
            memories = []
            try:
                mem_records = AIMemoryService.get_memories(db, user_id=user_id, active_only=True)
                memories = [{"category": m.category, "key": m.key, "value": m.value} for m in mem_records[:5]]
            except Exception:
                pass

            pers_context = ""
            try:
                pers_context = PersonalizationService.get_personalization_prompt_context(db, user_id=user_id)
            except Exception:
                pass

            # 4. Run full multi-stage pipeline with summary context
            pipeline = PromptBuilder.run_pipeline(
                user_message=user_message,
                chat_history=chat_history or [],
                financial_summary=summary,
                memories=memories,
                personalization_context=pers_context
            )

            # 5. Handle Clarification Path directly (ask user for missing information)
            if pipeline.is_clarification and pipeline.prompt_text:
                logger.info("[ChatStreamService] Yielding interactive clarification prompt to client.")
                chunks = TemplateEngine.render_stream_chunks(pipeline.prompt_text, words_per_chunk=4)
                for chunk in chunks:
                    event_data = json.dumps({"type": "token", "content": chunk})
                    yield f"data: {event_data}\n\n"
                    await asyncio.sleep(0.02)

                done_data = json.dumps({"type": "done"})
                yield f"data: {done_data}\n\n"
                return

            # 6. Stream tokens from Hybrid Provider (Gemini 3.6 Flash -> Fallback Engine)
            full_response_acc = []
            async for token in self.provider.generate_stream(
                prompt=pipeline.prompt_text,
                system_prompt=pipeline.system_prompt,
                summary=summary
            ):
                if token:
                    full_response_acc.append(token)
                    event_data = json.dumps({"type": "token", "content": token})
                    yield f"data: {event_data}\n\n"

            # 7. Validate generated response
            full_text = "".join(full_response_acc)
            val_res = ResponseValidator.validate_and_sanitize(
                response_text=full_text,
                decision_result=pipeline.decision,
                user_message=user_message
            )
            if val_res.warnings:
                logger.info("[ChatStreamService] Response validation warnings: %s", val_res.warnings)

            # 8. Signal completion
            done_data = json.dumps({"type": "done"})
            yield f"data: {done_data}\n\n"

        except Exception as exc:
            logger.error("Error in ChatStreamService.stream_chat_response: %s", str(exc), exc_info=True)
            err_data = json.dumps({"type": "error", "message": "Streaming service encountered a temporary error. Please retry."})
            yield f"data: {err_data}\n\n"

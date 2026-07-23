"""
AI Tool Executor - ExpenseFlowAI

Orchestrates tool discovery, intent classification, parameter validation,
and safety confirmation checks before delegating tool execution to ToolRegistry handlers.

Enforces zero direct SQL / database manipulation by the LLM.
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.ai.tool_registry import ToolRegistry, BaseTool
from app.schemas.tools import ToolExecutionStatus
from app.ai.provider import LLMProvider
from app.ai.factory import get_llm_provider

logger = logging.getLogger(__name__)


class ToolExecutor:
    def __init__(self, provider: Optional[LLMProvider] = None):
        self.provider = provider or get_llm_provider()

    def execute_action(
        self,
        db: Session,
        user_id: int,
        message: Optional[str] = None,
        tool_name: Optional[str] = None,
        action: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        confirmed: bool = False
    ) -> Dict[str, Any]:
        """
        Main tool execution entrypoint:
        1. Classifies intent & selects tool if not explicitly specified.
        2. Validates tool existence.
        3. Enforces safety confirmation for destructive operations.
        4. Executes backend tool handler.
        5. Formats assistant explanation response.
        """
        params = parameters or {}

        # 1. Infer Tool Name and Action if not provided
        if not tool_name or not action:
            inferred_tool, inferred_action, extracted_params = self._infer_intent(message or "")
            tool_name = tool_name or inferred_tool
            action = action or inferred_action
            if extracted_params:
                params = {**extracted_params, **params}

        # 2. Validate Tool existence
        tool = ToolRegistry.get_tool(tool_name) if tool_name else None
        if not tool:
            return {
                "tool": tool_name or "UnknownTool",
                "status": ToolExecutionStatus.INVALID_TOOL.value,
                "result": {},
                "assistant_response": f"I couldn't identify a valid action tool for '{message or tool_name}'."
            }

        # 3. Safety Confirmation Check for Destructive Actions
        if tool.is_destructive(action) and not confirmed:
            prompt_target = params.get("subscription_name") or params.get("name") or params.get("category") or "this item"
            confirm_msg = f"Are you sure you want to execute '{action}' on '{prompt_target}'?"
            return {
                "tool": tool.name,
                "status": ToolExecutionStatus.REQUIRES_CONFIRMATION.value,
                "result": {"pending_action": action, "parameters": params},
                "assistant_response": f"Executing '{action}' is a destructive action and requires confirmation. {confirm_msg}",
                "confirmation_prompt": confirm_msg
            }

        # 4. Execute Tool Handler
        try:
            result = tool.execute(db=db, user_id=user_id, action=action, parameters=params)
            explanation = result.get("message") or f"Successfully completed {action} using {tool.name}."

            return {
                "tool": tool.name,
                "status": ToolExecutionStatus.SUCCESS.value,
                "result": result,
                "assistant_response": explanation
            }
        except Exception as exc:
            logger.error("Tool execution error in %s (%s): %s", tool_name, action, str(exc))
            return {
                "tool": tool.name,
                "status": ToolExecutionStatus.FAILED.value,
                "result": {"error": str(exc)},
                "assistant_response": f"Failed to complete action: {str(exc)}"
            }

    def _infer_intent(self, text: str) -> tuple[Optional[str], Optional[str], Dict[str, Any]]:
        text_lower = text.lower()
        params: Dict[str, Any] = {}

        # Parse numeric amounts if present
        import re
        amounts = re.findall(r"(?:₹|\$|rs\.?|inr)?\s*(\d+(?:,\d+)*(?:\.\d+)?)", text_lower)
        if amounts:
            try:
                params["amount"] = float(amounts[0].replace(",", ""))
            except ValueError:
                pass

        if "delete" in text_lower or "cancel" in text_lower or "remove" in text_lower:
            if "subscription" in text_lower or "netflix" in text_lower:
                if "netflix" in text_lower:
                    params["subscription_name"] = "Netflix"
                return "ExpenseTool", "delete_subscription", params
            return "ExpenseTool", "delete", params

        if "budget" in text_lower:
            if "show" in text_lower or "list" in text_lower:
                return "BudgetTool", "list_budgets", params
            # Extract category name
            for cat in ["grocery", "groceries", "dining", "entertainment", "savings", "transport"]:
                if cat in text_lower:
                    params["category"] = cat.capitalize()
                    break
            return "BudgetTool", "create_budget", params

        if "goal" in text_lower or "saving" in text_lower or "macbook" in text_lower or "bike" in text_lower:
            if "show" in text_lower or "list" in text_lower:
                return "GoalTool", "list_goals", params
            return "GoalTool", "create_goal", params

        if "reminder" in text_lower or "rent" in text_lower or "bill" in text_lower:
            if "rent" in text_lower:
                params["title"] = "Rent Payment"
            return "ReminderTool", "create_reminder", params

        if "show" in text_lower or "subscription" in text_lower:
            return "ExpenseTool", "list_subscriptions", params

        return "ReportTool", "get_financial_report", params

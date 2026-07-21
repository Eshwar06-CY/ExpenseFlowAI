"""
Pydantic schemas for the Automation Engine.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, field_validator, ConfigDict


# ─── Condition & Action primitives ────────────────────────────────────────

class Condition(BaseModel):
    """A single condition clause."""
    field: str       # description | amount | type | account_id | category_id | merchant
    operator: str    # contains | not_contains | eq | neq | gt | gte | lt | lte | starts_with | ends_with | is_empty | is_not_empty
    value: Optional[Any] = None  # not required for is_empty / is_not_empty


class Action(BaseModel):
    """A single action to execute when conditions match."""
    type: str                                  # assign_category | assign_account | notify | contribute_to_goal | mark_reviewed | archive | create_reminder
    category_id: Optional[int] = None
    account_id: Optional[int] = None
    goal_id: Optional[int] = None
    percent: Optional[float] = None            # for contribute_to_goal
    amount: Optional[float] = None             # fixed amount for contribute_to_goal
    title: Optional[str] = None                # for notify / create_reminder
    message: Optional[str] = None             # for notify
    reminder_days: Optional[int] = None        # for create_reminder (days from now)


# ─── Rule schemas ─────────────────────────────────────────────────────────

VALID_TRIGGERS = {
    "on_transaction", "daily", "weekly", "monthly",
    "on_bill_due", "on_goal_completed"
}
VALID_LOGICS = {"AND", "OR"}


class AutomationRuleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_enabled: bool = True
    priority: int = 100
    trigger: str = "on_transaction"
    condition_logic: str = "AND"
    conditions: List[Condition] = []
    actions: List[Action] = []

    @field_validator("trigger")
    @classmethod
    def validate_trigger(cls, v: str) -> str:
        if v not in VALID_TRIGGERS:
            raise ValueError(f"trigger must be one of {VALID_TRIGGERS}")
        return v

    @field_validator("condition_logic")
    @classmethod
    def validate_logic(cls, v: str) -> str:
        if v not in VALID_LOGICS:
            raise ValueError("condition_logic must be 'AND' or 'OR'")
        return v


class AutomationRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_enabled: Optional[bool] = None
    priority: Optional[int] = None
    trigger: Optional[str] = None
    condition_logic: Optional[str] = None
    conditions: Optional[List[Condition]] = None
    actions: Optional[List[Action]] = None


class AutomationRuleResponse(BaseModel):
    id: int
    user_id: int
    name: str
    description: Optional[str]
    is_enabled: bool
    priority: int
    trigger: str
    condition_logic: str
    conditions: List[Dict]
    actions: List[Dict]
    run_count: int
    last_run_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ─── Execution schemas ────────────────────────────────────────────────────

class AutomationExecutionResponse(BaseModel):
    id: int
    rule_id: int
    rule_name: Optional[str] = None
    user_id: int
    trigger: str
    transaction_id: Optional[int]
    status: str
    actions_executed: List[str]
    result_summary: str
    duration_ms: int
    error_message: Optional[str]
    executed_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ─── Test request/response ────────────────────────────────────────────────

class RuleTestRequest(BaseModel):
    """Test a rule against existing transactions without committing changes."""
    rule_id: Optional[int] = None        # test existing saved rule
    conditions: Optional[List[Condition]] = None  # or test ad-hoc conditions
    actions: Optional[List[Action]] = None
    condition_logic: str = "AND"
    limit: int = 20                      # max transactions to preview


class RuleTestResult(BaseModel):
    matched_count: int
    sample_transactions: List[Dict]
    would_execute_actions: List[str]


# ─── Stats schema ─────────────────────────────────────────────────────────

class AutomationStats(BaseModel):
    total_rules: int
    active_rules: int
    total_executions: int
    successful_executions: int
    failed_executions: int
    skipped_executions: int
    rules_run_today: int

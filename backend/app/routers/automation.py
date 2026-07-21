"""
Automation Router — REST endpoints for rule management, execution history,
rule testing, and statistics.
"""
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.routers.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.models.automation import AutomationRule, AutomationExecution
from app.schemas.automation_schemas import (
    AutomationRuleCreate, AutomationRuleUpdate, AutomationRuleResponse,
    AutomationExecutionResponse, RuleTestRequest, RuleTestResult,
    AutomationStats
)
from app.services import automation_service as svc

router = APIRouter()


# ─── Helpers ──────────────────────────────────────────────────────────────

def _rule_to_response(rule: AutomationRule) -> dict:
    try:
        conditions = json.loads(rule.conditions or "[]")
    except Exception:
        conditions = []
    try:
        actions = json.loads(rule.actions or "[]")
    except Exception:
        actions = []
    return {
        "id": rule.id,
        "user_id": rule.user_id,
        "name": rule.name,
        "description": rule.description,
        "is_enabled": rule.is_enabled,
        "priority": rule.priority,
        "trigger": rule.trigger,
        "condition_logic": rule.condition_logic,
        "conditions": conditions,
        "actions": actions,
        "run_count": rule.run_count,
        "last_run_at": rule.last_run_at,
        "created_at": rule.created_at,
    }


def _exec_to_response(exec_record: AutomationExecution, db: Session) -> dict:
    try:
        actions_executed = json.loads(exec_record.actions_executed or "[]")
    except Exception:
        actions_executed = []
    rule = db.get(AutomationRule, exec_record.rule_id)
    return {
        "id": exec_record.id,
        "rule_id": exec_record.rule_id,
        "rule_name": rule.name if rule else None,
        "user_id": exec_record.user_id,
        "trigger": exec_record.trigger,
        "transaction_id": exec_record.transaction_id,
        "status": exec_record.status,
        "actions_executed": actions_executed,
        "result_summary": exec_record.result_summary,
        "duration_ms": exec_record.duration_ms,
        "error_message": exec_record.error_message,
        "executed_at": exec_record.executed_at,
    }


# ─── Rule CRUD ────────────────────────────────────────────────────────────

@router.post("/rules", response_model=AutomationRuleResponse, status_code=201)
def create_rule(
    data: AutomationRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new automation rule."""
    rule = svc.create_rule(db, current_user.id, data)
    return _rule_to_response(rule)


@router.get("/rules", response_model=List[AutomationRuleResponse])
def list_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all automation rules for the current user."""
    rules = svc.get_rules(db, current_user.id)
    return [_rule_to_response(r) for r in rules]


@router.get("/rules/{rule_id}", response_model=AutomationRuleResponse)
def get_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rule = svc.get_rule(db, rule_id, current_user.id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found.")
    return _rule_to_response(rule)


@router.patch("/rules/{rule_id}", response_model=AutomationRuleResponse)
def update_rule(
    rule_id: int,
    data: AutomationRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rule = svc.update_rule(db, rule_id, current_user.id, data)
    return _rule_to_response(rule)


@router.delete("/rules/{rule_id}", status_code=204)
def delete_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    svc.delete_rule(db, rule_id, current_user.id)


@router.post("/rules/{rule_id}/enable", response_model=AutomationRuleResponse)
def enable_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rule = svc.toggle_rule(db, rule_id, current_user.id, enabled=True)
    return _rule_to_response(rule)


@router.post("/rules/{rule_id}/disable", response_model=AutomationRuleResponse)
def disable_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rule = svc.toggle_rule(db, rule_id, current_user.id, enabled=False)
    return _rule_to_response(rule)


# ─── Rule Tester ─────────────────────────────────────────────────────────

@router.post("/test", response_model=RuleTestResult)
def test_rule(
    req: RuleTestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Dry-run a rule against existing transactions.
    No database writes. Returns preview of which transactions would be affected.
    """
    if req.rule_id:
        rule = svc.get_rule(db, req.rule_id, current_user.id)
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found.")
        conditions = json.loads(rule.conditions or "[]")
        actions = json.loads(rule.actions or "[]")
        logic = rule.condition_logic
    elif req.conditions is not None:
        conditions = [c.model_dump() for c in req.conditions]
        actions = [a.model_dump(exclude_none=True) for a in (req.actions or [])]
        logic = req.condition_logic
    else:
        raise HTTPException(status_code=400, detail="Provide rule_id or conditions.")

    result = svc.test_rule(
        db, current_user.id, conditions, actions, logic, limit=req.limit
    )
    return result


# ─── Execution History ────────────────────────────────────────────────────

@router.get("/executions", response_model=List[AutomationExecutionResponse])
def list_executions(
    rule_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List execution history, optionally filtered by rule or status."""
    executions = svc.get_executions(
        db, current_user.id, rule_id=rule_id, status=status,
        skip=skip, limit=limit
    )
    return [_exec_to_response(e, db) for e in executions]


# ─── Statistics ───────────────────────────────────────────────────────────

@router.get("/stats", response_model=AutomationStats)
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get aggregate automation statistics for the dashboard."""
    return svc.get_stats(db, current_user.id)


# ─── Manual Run ───────────────────────────────────────────────────────────

@router.post("/rules/{rule_id}/run", status_code=200)
def manual_run(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually trigger a scheduled rule against recent transactions.
    """
    rule = svc.get_rule(db, rule_id, current_user.id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found.")
    if rule.trigger == "on_transaction":
        raise HTTPException(
            status_code=400,
            detail="'on_transaction' rules cannot be run manually. They fire on transaction creation."
        )
    executions = svc.AutomationRunner.run_scheduled(
        db, current_user.id, trigger=rule.trigger
    )
    success = sum(1 for e in executions if e.status == "success")
    return {"message": f"Rule executed. {success} transaction(s) updated.", "executions": len(executions)}

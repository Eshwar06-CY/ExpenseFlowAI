"""
Automation Service — Rule Engine, Executor, and Scheduler.

Architecture:
  1. RuleEngine  — pure condition evaluator, no side-effects
  2. ActionExecutor — applies actions to transaction / entities
  3. AutomationRunner — orchestrates: load rules → evaluate → execute → log
  4. Scheduler helpers — call AutomationRunner for time-based triggers
"""
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.models.automation import AutomationRule, AutomationExecution
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.goal import Goal
from app.models.notification import Notification
from app.models.account import Account
from app.schemas.automation_schemas import (
    AutomationRuleCreate, AutomationRuleUpdate, Condition, Action
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# 1. Rule Engine — Pure Condition Evaluator
# ═══════════════════════════════════════════════════════════════════════════

class RuleEngine:
    """
    Evaluates a list of conditions against a transaction dict snapshot.
    No database writes — pure functional evaluation.
    """

    SUPPORTED_FIELDS = {
        "description", "amount", "type", "account_id",
        "category_id", "merchant", "is_reviewed", "is_archived"
    }

    SUPPORTED_OPERATORS = {
        "contains", "not_contains", "eq", "neq",
        "gt", "gte", "lt", "lte",
        "starts_with", "ends_with",
        "is_empty", "is_not_empty"
    }

    @classmethod
    def build_snapshot(cls, tx: Transaction) -> Dict[str, Any]:
        """Convert a Transaction ORM object to a flat comparison dict."""
        desc = (tx.description or "").lower()
        return {
            "description": desc,
            "merchant": desc,           # merchant alias → same field
            "amount": float(tx.amount),
            "type": tx.type,
            "account_id": tx.account_id,
            "category_id": tx.category_id,
            "is_reviewed": tx.is_reviewed,
            "is_archived": tx.is_archived,
        }

    @classmethod
    def evaluate_condition(cls, snapshot: Dict[str, Any], cond: Dict) -> bool:
        """Evaluate a single condition dict against the snapshot."""
        field = cond.get("field", "")
        operator = cond.get("operator", "eq")
        value = cond.get("value")

        if field not in cls.SUPPORTED_FIELDS:
            logger.warning("Unknown field '%s' in condition — skipping", field)
            return False

        actual = snapshot.get(field)

        try:
            if operator == "is_empty":
                return actual is None or actual == ""
            if operator == "is_not_empty":
                return actual is not None and actual != ""
            if operator == "contains":
                return value is not None and str(value).lower() in str(actual or "").lower()
            if operator == "not_contains":
                return value is not None and str(value).lower() not in str(actual or "").lower()
            if operator == "starts_with":
                return str(actual or "").lower().startswith(str(value or "").lower())
            if operator == "ends_with":
                return str(actual or "").lower().endswith(str(value or "").lower())
            if operator == "eq":
                # handle numeric comparison
                try:
                    return float(actual) == float(value)
                except (TypeError, ValueError):
                    return str(actual) == str(value)
            if operator == "neq":
                try:
                    return float(actual) != float(value)
                except (TypeError, ValueError):
                    return str(actual) != str(value)
            if operator == "gt":
                return float(actual) > float(value)
            if operator == "gte":
                return float(actual) >= float(value)
            if operator == "lt":
                return float(actual) < float(value)
            if operator == "lte":
                return float(actual) <= float(value)
        except (TypeError, ValueError) as e:
            logger.debug("Condition evaluation error for field '%s': %s", field, e)
            return False

        return False

    @classmethod
    def evaluate(cls, conditions: List[Dict], snapshot: Dict[str, Any], logic: str = "AND") -> bool:
        """
        Evaluate all conditions with AND or OR logic.
        Empty conditions list → always matches.
        """
        if not conditions:
            return True
        results = [cls.evaluate_condition(snapshot, c) for c in conditions]
        return all(results) if logic == "AND" else any(results)


# ═══════════════════════════════════════════════════════════════════════════
# 2. Action Executor
# ═══════════════════════════════════════════════════════════════════════════

class ActionExecutor:
    """Executes a list of actions against a transaction. Returns list of executed action names."""

    @classmethod
    def execute(
        cls,
        db: Session,
        actions: List[Dict],
        tx: Transaction,
        user_id: int,
        dry_run: bool = False
    ) -> Tuple[List[str], str]:
        """
        Execute all actions. If dry_run=True no DB writes are made.
        Returns: (executed_action_names, result_summary)
        """
        executed = []
        summary_parts = []

        for action in actions:
            action_type = action.get("type", "")
            try:
                label = cls._execute_one(db, action_type, action, tx, user_id, dry_run)
                if label:
                    executed.append(action_type)
                    summary_parts.append(label)
            except Exception as e:
                logger.error("Action '%s' failed: %s", action_type, e)
                summary_parts.append(f"{action_type}: ERROR({e})")

        return executed, "; ".join(summary_parts) if summary_parts else "No actions executed"

    @classmethod
    def _execute_one(
        cls, db: Session, action_type: str, action: Dict,
        tx: Transaction, user_id: int, dry_run: bool
    ) -> Optional[str]:
        """Execute a single action. Returns human-readable label or None."""

        if action_type == "assign_category":
            cat_id = action.get("category_id")
            if cat_id and not dry_run:
                tx.category_id = cat_id
                db.flush()
            return f"Category → #{cat_id}"

        elif action_type == "assign_account":
            acct_id = action.get("account_id")
            if acct_id and not dry_run:
                tx.account_id = acct_id
                db.flush()
            return f"Account → #{acct_id}"

        elif action_type == "mark_reviewed":
            if not dry_run:
                tx.is_reviewed = True
                db.flush()
            return "Marked as reviewed"

        elif action_type == "archive":
            if not dry_run:
                tx.is_archived = True
                db.flush()
            return "Archived transaction"

        elif action_type == "notify":
            title = action.get("title", "Automation Alert")
            message = action.get("message", "An automation rule was triggered.")
            if not dry_run:
                note = Notification(
                    user_id=user_id,
                    title=title,
                    message=message[:255]
                )
                db.add(note)
                db.flush()
            return f"Notification: '{title}'"

        elif action_type == "contribute_to_goal":
            goal_id = action.get("goal_id")
            percent = action.get("percent")
            amount = action.get("amount")

            if goal_id:
                contribution = 0.0
                if percent:
                    contribution = tx.amount * (float(percent) / 100.0)
                elif amount:
                    contribution = float(amount)

                if contribution > 0 and not dry_run:
                    goal = db.get(Goal, goal_id)
                    if goal and goal.user_id == user_id:
                        goal.current_amount += contribution
                        db.flush()
                return f"Goal #{goal_id} +{contribution:.2f}"

        elif action_type == "create_reminder":
            title = action.get("title", "Reminder")
            days = action.get("reminder_days", 1)
            message = action.get("message", f"Reminder from automation rule.")
            if not dry_run:
                note = Notification(
                    user_id=user_id,
                    title=title,
                    message=message[:255]
                )
                db.add(note)
                db.flush()
            return f"Reminder '{title}' in {days}d"

        else:
            logger.warning("Unknown action type: %s", action_type)
            return None


# ═══════════════════════════════════════════════════════════════════════════
# 3. AutomationRunner — Orchestrator
# ═══════════════════════════════════════════════════════════════════════════

class AutomationRunner:
    """
    Orchestrates rule loading, evaluation, execution, and history logging.
    """

    @classmethod
    def run_for_transaction(
        cls,
        db: Session,
        tx: Transaction,
        user_id: int
    ) -> List[AutomationExecution]:
        """
        Called when a transaction is created.
        Evaluates all enabled 'on_transaction' rules in priority order.
        """
        rules = cls._load_enabled_rules(db, user_id, trigger="on_transaction")
        return cls._run_rules(db, rules, tx, user_id, trigger="on_transaction")

    @classmethod
    def run_scheduled(
        cls,
        db: Session,
        user_id: int,
        trigger: str  # "daily" | "weekly" | "monthly"
    ) -> List[AutomationExecution]:
        """Run all scheduled rules for a given trigger frequency."""
        rules = cls._load_enabled_rules(db, user_id, trigger=trigger)
        # For scheduled rules we run against recent transactions
        cutoff = {
            "daily": datetime.utcnow() - timedelta(days=1),
            "weekly": datetime.utcnow() - timedelta(weeks=1),
            "monthly": datetime.utcnow() - timedelta(days=30),
        }.get(trigger, datetime.utcnow() - timedelta(days=1))

        recent_txs = db.execute(
            select(Transaction).where(
                and_(Transaction.user_id == user_id, Transaction.date >= cutoff)
            ).limit(500)
        ).scalars().all()

        executions = []
        for rule in rules:
            for tx in recent_txs:
                execs = cls._run_rules(db, [rule], tx, user_id, trigger=trigger)
                executions.extend(execs)
        return executions

    @classmethod
    def _load_enabled_rules(
        cls, db: Session, user_id: int, trigger: str
    ) -> List[AutomationRule]:
        rows = db.execute(
            select(AutomationRule).where(
                and_(
                    AutomationRule.user_id == user_id,
                    AutomationRule.is_enabled == True,
                    AutomationRule.trigger == trigger
                )
            ).order_by(AutomationRule.priority.asc())
        ).scalars().all()
        return list(rows)

    @classmethod
    def _run_rules(
        cls,
        db: Session,
        rules: List[AutomationRule],
        tx: Transaction,
        user_id: int,
        trigger: str
    ) -> List[AutomationExecution]:
        executions = []
        snapshot = RuleEngine.build_snapshot(tx)

        for rule in rules:
            try:
                conditions = json.loads(rule.conditions or "[]")
                actions = json.loads(rule.actions or "[]")
            except json.JSONDecodeError:
                logger.error("Rule %s has invalid JSON", rule.id)
                continue

            t0 = time.monotonic()

            matched = RuleEngine.evaluate(conditions, snapshot, rule.condition_logic)
            if not matched:
                execution = cls._record(
                    db, rule, tx, user_id, trigger,
                    status="skipped", executed=[], summary="Conditions not met",
                    duration_ms=int((time.monotonic() - t0) * 1000)
                )
                executions.append(execution)
                continue

            try:
                executed, summary = ActionExecutor.execute(
                    db, actions, tx, user_id, dry_run=False
                )
                rule.run_count += 1
                rule.last_run_at = datetime.utcnow()
                db.flush()

                execution = cls._record(
                    db, rule, tx, user_id, trigger,
                    status="success", executed=executed, summary=summary,
                    duration_ms=int((time.monotonic() - t0) * 1000)
                )
            except Exception as e:
                logger.exception("Rule %s execution failed", rule.id)
                execution = cls._record(
                    db, rule, tx, user_id, trigger,
                    status="failed", executed=[], summary="Execution error",
                    duration_ms=int((time.monotonic() - t0) * 1000),
                    error_message=str(e)
                )

            executions.append(execution)

        db.commit()
        return executions

    @classmethod
    def _record(
        cls, db: Session, rule: AutomationRule, tx: Transaction,
        user_id: int, trigger: str, status: str,
        executed: List[str], summary: str, duration_ms: int,
        error_message: Optional[str] = None
    ) -> AutomationExecution:
        exec_record = AutomationExecution(
            rule_id=rule.id,
            user_id=user_id,
            trigger=trigger,
            transaction_id=tx.id if tx else None,
            status=status,
            actions_executed=json.dumps(executed),
            result_summary=summary,
            duration_ms=duration_ms,
            error_message=error_message,
            executed_at=datetime.utcnow()
        )
        db.add(exec_record)
        return exec_record


# ═══════════════════════════════════════════════════════════════════════════
# 4. Rule Tester — Dry Run
# ═══════════════════════════════════════════════════════════════════════════

def test_rule(
    db: Session,
    user_id: int,
    conditions: List[Dict],
    actions: List[Dict],
    condition_logic: str,
    limit: int = 20
) -> Dict:
    """
    Evaluate conditions against recent transactions without committing any changes.
    Returns matched transaction previews and action summaries.
    """
    recent_txs = db.execute(
        select(Transaction).where(Transaction.user_id == user_id)
        .order_by(Transaction.date.desc())
        .limit(200)
    ).scalars().all()

    matched = []
    for tx in recent_txs:
        snapshot = RuleEngine.build_snapshot(tx)
        if RuleEngine.evaluate(conditions, snapshot, condition_logic):
            matched.append({
                "id": tx.id,
                "date": tx.date.isoformat() if tx.date else None,
                "description": tx.description,
                "amount": tx.amount,
                "type": tx.type,
                "category_id": tx.category_id,
                "account_id": tx.account_id,
            })
            if len(matched) >= limit:
                break

    # Simulate actions on the first match (dry run)
    would_execute = []
    if matched and actions:
        sample_tx = db.get(Transaction, matched[0]["id"])
        if sample_tx:
            executed, _ = ActionExecutor.execute(
                db, actions, sample_tx, user_id, dry_run=True
            )
            would_execute = executed
            db.rollback()  # ensure nothing leaks

    return {
        "matched_count": len(matched),
        "sample_transactions": matched[:limit],
        "would_execute_actions": would_execute
    }


# ═══════════════════════════════════════════════════════════════════════════
# 5. CRUD helpers
# ═══════════════════════════════════════════════════════════════════════════

def create_rule(db: Session, user_id: int, data: AutomationRuleCreate) -> AutomationRule:
    rule = AutomationRule(
        user_id=user_id,
        name=data.name,
        description=data.description,
        is_enabled=data.is_enabled,
        priority=data.priority,
        trigger=data.trigger,
        condition_logic=data.condition_logic,
        conditions=json.dumps([c.model_dump() for c in data.conditions]),
        actions=json.dumps([a.model_dump(exclude_none=True) for a in data.actions]),
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def get_rules(db: Session, user_id: int) -> List[AutomationRule]:
    return list(db.execute(
        select(AutomationRule).where(AutomationRule.user_id == user_id)
        .order_by(AutomationRule.priority.asc())
    ).scalars().all())


def get_rule(db: Session, rule_id: int, user_id: int) -> Optional[AutomationRule]:
    return db.execute(
        select(AutomationRule).where(
            and_(AutomationRule.id == rule_id, AutomationRule.user_id == user_id)
        )
    ).scalar_one_or_none()


def update_rule(
    db: Session, rule_id: int, user_id: int, data: AutomationRuleUpdate
) -> AutomationRule:
    from fastapi import HTTPException
    rule = get_rule(db, rule_id, user_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found.")
    if data.name is not None:
        rule.name = data.name
    if data.description is not None:
        rule.description = data.description
    if data.is_enabled is not None:
        rule.is_enabled = data.is_enabled
    if data.priority is not None:
        rule.priority = data.priority
    if data.trigger is not None:
        rule.trigger = data.trigger
    if data.condition_logic is not None:
        rule.condition_logic = data.condition_logic
    if data.conditions is not None:
        rule.conditions = json.dumps([c.model_dump() for c in data.conditions])
    if data.actions is not None:
        rule.actions = json.dumps([a.model_dump(exclude_none=True) for a in data.actions])
    db.commit()
    db.refresh(rule)
    return rule


def delete_rule(db: Session, rule_id: int, user_id: int):
    from fastapi import HTTPException
    rule = get_rule(db, rule_id, user_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found.")
    db.delete(rule)
    db.commit()


def toggle_rule(db: Session, rule_id: int, user_id: int, enabled: bool) -> AutomationRule:
    from fastapi import HTTPException
    rule = get_rule(db, rule_id, user_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found.")
    rule.is_enabled = enabled
    db.commit()
    db.refresh(rule)
    return rule


def get_executions(
    db: Session, user_id: int,
    rule_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0, limit: int = 50
) -> List[AutomationExecution]:
    q = select(AutomationExecution).where(AutomationExecution.user_id == user_id)
    if rule_id:
        q = q.where(AutomationExecution.rule_id == rule_id)
    if status:
        q = q.where(AutomationExecution.status == status)
    q = q.order_by(AutomationExecution.executed_at.desc()).offset(skip).limit(limit)
    return list(db.execute(q).scalars().all())


def get_stats(db: Session, user_id: int) -> Dict:
    from sqlalchemy import func
    rules = db.execute(
        select(AutomationRule).where(AutomationRule.user_id == user_id)
    ).scalars().all()

    executions = db.execute(
        select(AutomationExecution).where(AutomationExecution.user_id == user_id)
    ).scalars().all()

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    return {
        "total_rules": len(rules),
        "active_rules": sum(1 for r in rules if r.is_enabled),
        "total_executions": len(executions),
        "successful_executions": sum(1 for e in executions if e.status == "success"),
        "failed_executions": sum(1 for e in executions if e.status == "failed"),
        "skipped_executions": sum(1 for e in executions if e.status == "skipped"),
        "rules_run_today": sum(
            1 for e in executions
            if e.executed_at and e.executed_at.replace(tzinfo=None) >= today_start
            and e.status == "success"
        )
    }

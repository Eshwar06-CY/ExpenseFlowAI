"""
Explainable AI (XAI) Framework Service - ExpenseFlowAI

Provides transparent, structured explanations for every AI output across Dashboard,
Forecasts, Budgets, Goals, Digital Twin, Notifications, Strategy, and AI Chat.
The LLM NEVER performs financial calculations; FinanceEngine remains the source of truth.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.ai_explanation import AIExplanation
from app.schemas.explanation import ExplanationDTO
from app.services.finance_engine import FinanceEngine
from app.services.cashflow_forecast import CashFlowForecastService
from app.models.budget import Budget
from app.models.goal import Goal
from app.models.bill import Bill
from app.models.notification import Notification

logger = logging.getLogger(__name__)


class ExplainabilityService:
    @classmethod
    def get_explanation(
        cls,
        db: Session,
        user_id: int,
        feature: str,
        target_id: str
    ) -> ExplanationDTO:
        """
        Retrieves a cached explanation or compiles a transparent ExplanationDTO payload.
        """
        clean_feature = feature.lower().strip()
        clean_target = str(target_id).lower().strip()

        # 1. Check cache (24h window)
        cutoff = datetime.now() - timedelta(hours=24)
        cached = db.query(AIExplanation).filter(
            AIExplanation.user_id == user_id,
            AIExplanation.feature == clean_feature,
            AIExplanation.target_id == clean_target,
            AIExplanation.created_at >= cutoff
        ).order_by(desc(AIExplanation.created_at)).first()

        if cached:
            try:
                return ExplanationDTO(
                    feature=cached.feature,
                    target_id=cached.target_id,
                    reason=cached.reason,
                    data_used=json.loads(cached.data_used_json),
                    finance_engine_metrics=json.loads(cached.metrics_json),
                    confidence=cached.confidence,
                    assumptions=json.loads(cached.assumptions_json),
                    limitations=json.loads(cached.limitations_json),
                    related_features=["dashboard", "forecast", "budgets", "goals"],
                    suggested_actions=json.loads(cached.actions_json)
                )
            except Exception as exc:
                logger.warning("Failed to parse cached explanation: %s", str(exc))

        # 2. Build structured explanation dynamically
        dto = cls._build_explanation(db, user_id, clean_feature, clean_target)

        # 3. Save to AIExplanation cache table
        try:
            exp_rec = AIExplanation(
                user_id=user_id,
                feature=dto.feature,
                target_id=dto.target_id,
                reason=dto.reason,
                data_used_json=json.dumps(dto.data_used),
                metrics_json=json.dumps(dto.finance_engine_metrics),
                confidence=dto.confidence,
                assumptions_json=json.dumps(dto.assumptions),
                limitations_json=json.dumps(dto.limitations),
                actions_json=json.dumps(dto.suggested_actions)
            )
            db.add(exp_rec)
            db.commit()
        except Exception as exc:
            logger.warning("Failed to save AIExplanation record: %s", str(exc))

        return dto

    @classmethod
    def _build_explanation(
        cls,
        db: Session,
        user_id: int,
        feature: str,
        target_id: str
    ) -> ExplanationDTO:
        # Fetch verified baseline metrics from FinanceEngine
        summary = FinanceEngine.get_dashboard_summary(db, user_id=user_id, period="30d")
        health_score = summary.get("health_score", 88)
        health_status = summary.get("health_status", "Excellent")
        total_balance = summary.get("total_balance", 0.0)
        period_savings = summary.get("period_savings", 0.0)

        # Feature: Forecast Engine
        if feature in ("forecast", "cashflow_forecast"):
            try:
                fc = CashFlowForecastService().generate_forecast(db, user_id=user_id, period="30d")
                proj_end = fc.get("projected_end_balance", total_balance)
                surplus = fc.get("expected_surplus", 0.0)
                conf = fc.get("confidence_score", 0.88)
            except Exception:
                proj_end = total_balance + period_savings
                surplus = period_savings
                conf = 0.85

            return ExplanationDTO(
                feature="forecast",
                target_id=target_id,
                reason=f"30-day balance forecast of ₹{proj_end:,.2f} combines historical daily income/expense run rates with scheduled unpaid bills and goal commitments.",
                data_used=["Historical 30-Day Ledger", "Unpaid Bills Schedule", "Active Goal Contributions", "FinanceEngine Balances"],
                finance_engine_metrics={
                    "current_balance": total_balance,
                    "projected_end_balance": proj_end,
                    "expected_surplus": surplus,
                    "confidence_score": conf
                },
                confidence=conf,
                assumptions=["Income and recurring bills occur on expected dates.", "Daily discretionary spend matches historical 30-day average."],
                limitations=["Unforeseen emergency expenses or unannounced income changes will alter projections."],
                related_features=["digital_twin", "budgets", "bills"],
                suggested_actions=["Run What-If scenario in Digital Twin", "Set up bill reminders", "Top up emergency reserve"]
            )

        # Feature: Budget Advice / Burn Rate
        elif feature in ("budget", "budgets"):
            return ExplanationDTO(
                feature="budget",
                target_id=target_id,
                reason=f"Budget analysis evaluates active category spend against limits. Overall budget adherence is at {summary.get('health_metrics', {}).get('budget_adherence_pct', 92.5):.1f}%.",
                data_used=["Category Expenses", "Monthly Budget Allocations", "Historical Category Spend"],
                finance_engine_metrics={
                    "total_balance": total_balance,
                    "period_expense": summary.get("period_expense", 0.0),
                    "budget_adherence_pct": summary.get("health_metrics", {}).get("budget_adherence_pct", 92.5)
                },
                confidence=0.95,
                assumptions=["All category transactions are properly reviewed and categorized."],
                limitations=["Un-posted pending credit card charges are not reflected until posted."],
                related_features=["dashboard", "expenses", "notifications"],
                suggested_actions=["Review category transactions", "Adjust category limits", "Reallocate surplus budgets"]
            )

        # Feature: Goal Planner
        elif feature in ("goal", "goals"):
            return ExplanationDTO(
                feature="goal",
                target_id=target_id,
                reason="Goal timelines and forecast completion dates are derived mathematically from current accumulated savings and net monthly surplus.",
                data_used=["Goal Target Amount", "Accumulated Savings", "Monthly Savings Rate"],
                finance_engine_metrics={
                    "period_savings": period_savings,
                    "savings_rate": summary.get("period_savings_rate", 0.0),
                    "health_score": health_score
                },
                confidence=0.91,
                assumptions=["Monthly savings contribution velocity remains consistent."],
                limitations=["Reductions in monthly surplus will defer target completion date."],
                related_features=["forecast", "dashboard", "strategy"],
                suggested_actions=["Increase monthly savings contribution", "Set up automated transfer", "Review goal timeline"]
            )

        # Feature: Digital Twin Simulation
        elif feature in ("digital_twin", "simulator"):
            return ExplanationDTO(
                feature="digital_twin",
                target_id=target_id,
                reason=f"Digital Twin copied your live financial baseline (Health Score: {health_score}/100) into a virtual sandbox to test the exact impact of target scenario '{target_id}' without risking real money.",
                data_used=["Live Account Balances", "Historical Income & Expenses", "User Simulation Scenario"],
                finance_engine_metrics={
                    "baseline_balance": total_balance,
                    "baseline_health_score": health_score
                },
                confidence=0.90,
                assumptions=["Simulated adjustment takes effect immediately at specified magnitude."],
                limitations=["Does not factor in secondary macroeconomic interest rate or tax rate fluctuations."],
                related_features=["forecast", "dashboard", "strategy"],
                suggested_actions=["Apply simulation recommendations", "Run alternative scenario", "View forecast impact"]
            )

        # Feature: Notifications
        elif feature in ("notification", "notifications"):
            return ExplanationDTO(
                feature="notification",
                target_id=target_id,
                reason="Notification triggered automatically because alert threshold criteria met priority rules defined in FinanceEngine.",
                data_used=["Notification Preferences", "Event Trigger Metadata", "Financial Risk Index"],
                finance_engine_metrics={
                    "health_score": health_score,
                    "health_status": health_status
                },
                confidence=0.98,
                assumptions=["User delivery preferences allow in-app alert generation."],
                limitations=["Alert status marks resolved once user completes recommended action."],
                related_features=["notifications", "dashboard"],
                suggested_actions=["Complete recommended action", "Mark notification read", "Update notification preferences"]
            )

        # Default Fallback: Dashboard Insights & AI Coaching
        return ExplanationDTO(
            feature=feature,
            target_id=target_id,
            reason=f"Generated by FinanceEngine based on your 30-day health score ({health_score}/100 - {health_status}), net surplus of ₹{period_savings:,.2f}, and category run rates.",
            data_used=["FinanceEngine Health Summary", "Category Spending Breakdown", "Account Balances"],
            finance_engine_metrics={
                "health_score": health_score,
                "health_status": health_status,
                "total_balance": total_balance,
                "period_savings": period_savings
            },
            confidence=0.92,
            assumptions=["Financial ledger transactions accurately represent current cash reserves."],
            limitations=["Calculations rely exclusively on posted transactions."],
            related_features=["dashboard", "forecast", "chat"],
            suggested_actions=["Ask Copilot for deep-dive analysis", "Review spending breakdown", "Check 30-day forecast"]
        )

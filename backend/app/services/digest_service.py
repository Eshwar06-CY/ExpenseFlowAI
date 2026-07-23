"""
AI Financial Digest Service - ExpenseFlowAI

Compiles financial data from FinanceEngine, CashFlowForecastService, Strategy Planner,
and Digital Twin, caches generated reports, and manages PDF downloads.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.digest import FinancialDigest
from app.models.user import User
from app.services.dashboard_service import DashboardService
from app.services.pdf_generator import PDFGenerator, STORAGE_DIR

logger = logging.getLogger(__name__)


class DigestService:
    @classmethod
    def generate_digest(
        cls,
        db: Session,
        user_id: int,
        digest_type: str = "monthly"
    ) -> FinancialDigest:
        """
        Generates a new financial digest payload and ReportLab PDF document for the user.
        Reuses cached digest if generated within the last hour.
        """
        valid_types = ("daily", "weekly", "monthly", "yearly")
        if digest_type not in valid_types:
            digest_type = "monthly"

        # 1. Check for cached recent digest (1 hour window)
        cutoff = datetime.now() - timedelta(hours=1)
        cached = db.query(FinancialDigest).filter(
            FinancialDigest.user_id == user_id,
            FinancialDigest.digest_type == digest_type,
            FinancialDigest.generated_at >= cutoff
        ).order_by(desc(FinancialDigest.generated_at)).first()

        if cached and cached.pdf_path and os.path.exists(cached.pdf_path):
            return cached

        # 2. Compile unified financial overview
        period = "7d" if digest_type in ("daily", "weekly") else ("30d" if digest_type == "monthly" else "1y")
        overview = DashboardService.get_command_center_overview(db, user_id=user_id, period=period)
        overview["digest_type"] = digest_type

        # Fetch user
        user = db.query(User).filter(User.id == user_id).first()
        user_name = user.full_name if user and user.full_name else "Valued User"

        # 3. Generate PDF Report
        filename = f"digest_{user_id}_{digest_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = os.path.join(STORAGE_DIR, filename)

        try:
            PDFGenerator.generate_digest_pdf(user_name=user_name, digest_data=overview, output_path=pdf_path)
        except Exception as exc:
            logger.error("PDF generation failed: %s", str(exc), exc_info=True)
            pdf_path = None

        # 4. Save FinancialDigest DB record
        health_score = overview.get("financial_health", {}).get("score", 88)
        summary_text = overview.get("ai_executive_summary", f"{digest_type.capitalize()} financial summary compiled successfully.")

        digest = FinancialDigest(
            user_id=user_id,
            digest_type=digest_type,
            summary=summary_text,
            health_score=health_score,
            content_json=json.dumps(overview),
            pdf_path=pdf_path
        )
        db.add(digest)
        db.commit()
        db.refresh(digest)

        return digest

    @classmethod
    def list_digests(
        cls,
        db: Session,
        user_id: int,
        digest_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Lists past generated digests for the user with pagination and type filtering.
        """
        query = db.query(FinancialDigest).filter(FinancialDigest.user_id == user_id)
        if digest_type and digest_type != "all":
            query = query.filter(FinancialDigest.digest_type == digest_type)

        total_count = query.count()
        items = query.order_by(desc(FinancialDigest.generated_at)).offset(offset).limit(limit).all()

        return {
            "total_count": total_count,
            "items": [
                {
                    "id": d.id,
                    "digest_type": d.digest_type,
                    "summary": d.summary,
                    "health_score": d.health_score,
                    "has_pdf": bool(d.pdf_path and os.path.exists(d.pdf_path)),
                    "generated_at": d.generated_at.isoformat() if d.generated_at else None
                }
                for d in items
            ]
        }

    @classmethod
    def get_latest_digest(cls, db: Session, user_id: int) -> FinancialDigest:
        """
        Retrieves the most recent digest or generates a fresh monthly digest if none exists.
        """
        digest = db.query(FinancialDigest).filter(
            FinancialDigest.user_id == user_id
        ).order_by(desc(FinancialDigest.generated_at)).first()

        if not digest:
            digest = cls.generate_digest(db, user_id, digest_type="monthly")

        return digest

    @classmethod
    def get_digest_by_id(cls, db: Session, user_id: int, digest_id: int) -> Optional[FinancialDigest]:
        """
        Retrieves a specific digest by ID for the user.
        """
        return db.query(FinancialDigest).filter(
            FinancialDigest.id == digest_id,
            FinancialDigest.user_id == user_id
        ).first()

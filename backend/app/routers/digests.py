"""
Financial Digest API Router - ExpenseFlowAI

Endpoints:
- GET /api/v1/digests (List generated digests)
- GET /api/v1/digests/latest (Get latest digest payload)
- GET /api/v1/digests/{id} (Get digest details by ID)
- POST /api/v1/digests/generate (Generate digest on demand)
- GET /api/v1/digests/{id}/download (Download bank-grade PDF report)
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status, Body
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.routers.deps import get_current_user
from app.services.digest_service import DigestService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/digests", tags=["AI Financial Digest"])


@router.get("/", summary="List User Financial Digests")
def list_digests(
    digest_type: Optional[str] = Query(None, description="Filter by type: daily, weekly, monthly, yearly"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    return DigestService.list_digests(
        db=db,
        user_id=current_user.id,
        digest_type=digest_type,
        limit=limit,
        offset=offset
    )


@router.get("/latest", summary="Get Latest Digest Payload")
def get_latest_digest(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    digest = DigestService.get_latest_digest(db=db, user_id=current_user.id)
    content = json.loads(digest.content_json) if digest.content_json else {}
    return {
        "id": digest.id,
        "digest_type": digest.digest_type,
        "summary": digest.summary,
        "health_score": digest.health_score,
        "content": content,
        "has_pdf": bool(digest.pdf_path and os.path.exists(digest.pdf_path)),
        "generated_at": digest.generated_at.isoformat() if digest.generated_at else None
    }


@router.get("/{digest_id}", summary="Get Specific Digest Details")
def get_digest_details(
    digest_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    digest = DigestService.get_digest_by_id(db=db, user_id=current_user.id, digest_id=digest_id)
    if not digest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial digest not found."
        )
    content = json.loads(digest.content_json) if digest.content_json else {}
    return {
        "id": digest.id,
        "digest_type": digest.digest_type,
        "summary": digest.summary,
        "health_score": digest.health_score,
        "content": content,
        "has_pdf": bool(digest.pdf_path and os.path.exists(digest.pdf_path)),
        "generated_at": digest.generated_at.isoformat() if digest.generated_at else None
    }


@router.post("/generate", summary="Generate Financial Digest On-Demand")
def generate_digest(
    payload: Dict[str, Any] = Body(..., example={"digest_type": "monthly"}),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    digest_type = payload.get("digest_type", "monthly")
    digest = DigestService.generate_digest(db=db, user_id=current_user.id, digest_type=digest_type)
    content = json.loads(digest.content_json) if digest.content_json else {}
    return {
        "success": True,
        "id": digest.id,
        "digest_type": digest.digest_type,
        "summary": digest.summary,
        "health_score": digest.health_score,
        "content": content,
        "has_pdf": bool(digest.pdf_path and os.path.exists(digest.pdf_path)),
        "generated_at": digest.generated_at.isoformat() if digest.generated_at else None
    }


@router.get("/{digest_id}/download", summary="Download PDF Financial Report")
def download_digest_pdf(
    digest_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    digest = DigestService.get_digest_by_id(db=db, user_id=current_user.id, digest_id=digest_id)
    if not digest or not digest.pdf_path or not os.path.exists(digest.pdf_path):
        # Regenerate PDF if missing
        digest = DigestService.generate_digest(db=db, user_id=current_user.id, digest_type=digest.digest_type if digest else "monthly")

    if not digest.pdf_path or not os.path.exists(digest.pdf_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF report file is unavailable."
        )

    filename = f"ExpenseFlow_{digest.digest_type.capitalize()}_Digest_{digest.generated_at.strftime('%Y%m%d')}.pdf"
    return FileResponse(
        path=digest.pdf_path,
        media_type="application/pdf",
        filename=filename
    )

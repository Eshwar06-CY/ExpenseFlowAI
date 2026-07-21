"""
Collaboration Router — REST endpoints for Workspaces, Members, Comments, and Audit Logs.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.routers.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.models.audit_log import AuditLog
from app.models.comment import Comment
from app.schemas.collaboration_schemas import (
    WorkspaceCreate, WorkspaceUpdate, WorkspaceResponse,
    WorkspaceInvite, WorkspaceMemberResponse, WorkspaceMemberUpdate,
    CommentCreate, CommentResponse,
    AuditLogResponse
)
from app.services import collaboration_service as svc

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers — enrich model instances with user display info
# ---------------------------------------------------------------------------

def _member_to_response(member: WorkspaceMember, db: Session) -> dict:
    user = db.get(User, member.user_id)
    return {
        "id": member.id,
        "workspace_id": member.workspace_id,
        "user_id": member.user_id,
        "email": user.email if user else "",
        "full_name": getattr(user, "full_name", user.email if user else ""),
        "role": member.role,
        "is_accepted": member.is_accepted,
        "created_at": member.created_at,
    }


def _comment_to_response(comment: Comment, db: Session) -> dict:
    user = db.get(User, comment.user_id)
    return {
        "id": comment.id,
        "entity_type": comment.entity_type,
        "entity_id": comment.entity_id,
        "content": comment.content,
        "user_id": comment.user_id,
        "author_name": getattr(user, "full_name", user.email if user else ""),
        "created_at": comment.created_at,
    }


def _audit_to_response(log: AuditLog, db: Session) -> dict:
    user = db.get(User, log.user_id)
    return {
        "id": log.id,
        "workspace_id": log.workspace_id,
        "user_id": log.user_id,
        "user_name": getattr(user, "full_name", user.email if user else "Unknown"),
        "action": log.action,
        "entity_type": log.entity_type,
        "entity_id": log.entity_id,
        "description": log.description,
        "created_at": log.created_at,
    }


# ---------------------------------------------------------------------------
# Workspace Endpoints
# ---------------------------------------------------------------------------

@router.post("/", response_model=WorkspaceResponse, status_code=201)
def create_workspace(
    data: WorkspaceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new workspace. The creator becomes the owner."""
    ws = svc.create_workspace(db, current_user.id, data)
    return ws


@router.get("/", response_model=List[WorkspaceResponse])
def list_workspaces(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all workspaces the current user is a member of."""
    return svc.get_user_workspaces(db, current_user.id)


@router.get("/invitations", response_model=List[WorkspaceMemberResponse])
def list_invitations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List pending workspace invitations for the current user."""
    members = svc.get_pending_invitations(db, current_user.id)
    return [_member_to_response(m, db) for m in members]


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return svc.get_workspace_detail(db, workspace_id, current_user.id)


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
def update_workspace(
    workspace_id: int,
    data: WorkspaceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return svc.update_workspace(db, workspace_id, current_user.id, data)


@router.delete("/{workspace_id}", status_code=204)
def delete_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    svc.delete_workspace(db, workspace_id, current_user.id)


# ---------------------------------------------------------------------------
# Member Endpoints
# ---------------------------------------------------------------------------

@router.get("/{workspace_id}/members", response_model=List[WorkspaceMemberResponse])
def list_members(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    members = svc.list_members(db, workspace_id, current_user.id)
    return [_member_to_response(m, db) for m in members]


@router.post("/{workspace_id}/members/invite", response_model=WorkspaceMemberResponse, status_code=201)
def invite_member(
    workspace_id: int,
    data: WorkspaceInvite,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    member = svc.invite_member(db, workspace_id, current_user.id, data)
    return _member_to_response(member, db)


@router.post("/{workspace_id}/members/accept", response_model=WorkspaceMemberResponse)
def accept_invitation(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    member = svc.respond_to_invite(db, workspace_id, current_user.id, accept=True)
    return _member_to_response(member, db)


@router.post("/{workspace_id}/members/decline", status_code=204)
def decline_invitation(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    svc.respond_to_invite(db, workspace_id, current_user.id, accept=False)


@router.patch("/{workspace_id}/members/{member_user_id}", response_model=WorkspaceMemberResponse)
def update_member_role(
    workspace_id: int,
    member_user_id: int,
    data: WorkspaceMemberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    member = svc.update_member_role(db, workspace_id, current_user.id, member_user_id, data)
    return _member_to_response(member, db)


@router.delete("/{workspace_id}/members/{member_user_id}", status_code=204)
def remove_member(
    workspace_id: int,
    member_user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    svc.remove_member(db, workspace_id, current_user.id, member_user_id)


@router.post("/{workspace_id}/leave", status_code=204)
def leave_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    svc.leave_workspace(db, workspace_id, current_user.id)


@router.post("/{workspace_id}/transfer/{new_owner_id}", response_model=WorkspaceResponse)
def transfer_ownership(
    workspace_id: int,
    new_owner_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return svc.transfer_ownership(db, workspace_id, current_user.id, new_owner_id)


# ---------------------------------------------------------------------------
# Comment Endpoints
# ---------------------------------------------------------------------------

@router.post("/{workspace_id}/comments", response_model=CommentResponse, status_code=201)
def add_comment(
    workspace_id: int,
    data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    comment = svc.add_comment(db, workspace_id, current_user.id, data)
    return _comment_to_response(comment, db)


@router.get("/{workspace_id}/comments", response_model=List[CommentResponse])
def get_comments(
    workspace_id: int,
    entity_type: str = Query(...),
    entity_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    comments = svc.get_comments(db, workspace_id, current_user.id, entity_type, entity_id)
    return [_comment_to_response(c, db) for c in comments]


@router.delete("/{workspace_id}/comments/{comment_id}", status_code=204)
def delete_comment(
    workspace_id: int,
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    svc.delete_comment(db, workspace_id, current_user.id, comment_id)


# ---------------------------------------------------------------------------
# Audit Log Endpoints
# ---------------------------------------------------------------------------

@router.get("/{workspace_id}/audit-log", response_model=List[AuditLogResponse])
def get_audit_log(
    workspace_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    logs = svc.get_audit_log(db, workspace_id, current_user.id, skip=skip, limit=limit)
    return [_audit_to_response(log, db) for log in logs]

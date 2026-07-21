"""
Collaboration Service — Workspace, Member, Comment, and Audit Log operations.
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from fastapi import HTTPException, status

from app.models.workspace import Workspace, WorkspaceMember
from app.models.audit_log import AuditLog
from app.models.comment import Comment
from app.models.user import User
from app.models.notification import Notification
from app.schemas.collaboration_schemas import (
    WorkspaceCreate, WorkspaceUpdate,
    WorkspaceInvite, WorkspaceMemberUpdate,
    CommentCreate
)


# ---------------------------------------------------------------------------
# Role helpers
# ---------------------------------------------------------------------------

ROLE_HIERARCHY = {"owner": 4, "admin": 3, "editor": 2, "viewer": 1}

def _role_level(role: str) -> int:
    return ROLE_HIERARCHY.get(role, 0)


def _require_membership(db: Session, workspace_id: int, user_id: int, min_role: str = "viewer") -> WorkspaceMember:
    """Return the member record or raise 403/404."""
    member = db.execute(
        select(WorkspaceMember).where(
            and_(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
                WorkspaceMember.is_accepted == True
            )
        )
    ).scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this workspace.")
    if _role_level(member.role) < _role_level(min_role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"This action requires '{min_role}' role or higher.")
    return member


def _get_workspace(db: Session, workspace_id: int) -> Workspace:
    ws = db.get(Workspace, workspace_id)
    if not ws:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found.")
    return ws


def _log(db: Session, workspace_id: int, user_id: int, action: str, entity_type: str, description: str, entity_id: Optional[int] = None):
    entry = AuditLog(
        workspace_id=workspace_id,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        created_at=datetime.utcnow()
    )
    db.add(entry)


# ---------------------------------------------------------------------------
# Workspace CRUD
# ---------------------------------------------------------------------------

def create_workspace(db: Session, user_id: int, data: WorkspaceCreate) -> Workspace:
    ws = Workspace(
        name=data.name,
        description=data.description,
        owner_id=user_id,
        created_at=datetime.utcnow()
    )
    db.add(ws)
    db.flush()  # get ws.id before adding member

    # Auto-add owner as accepted member
    owner_member = WorkspaceMember(
        workspace_id=ws.id,
        user_id=user_id,
        role="owner",
        is_accepted=True,
        created_at=datetime.utcnow()
    )
    db.add(owner_member)
    _log(db, ws.id, user_id, "created", "workspace", f"Created workspace '{ws.name}'")
    db.commit()
    db.refresh(ws)
    return ws


def get_user_workspaces(db: Session, user_id: int) -> List[Workspace]:
    """All workspaces the user is an accepted member of."""
    rows = db.execute(
        select(Workspace).join(WorkspaceMember).where(
            and_(
                WorkspaceMember.user_id == user_id,
                WorkspaceMember.is_accepted == True
            )
        )
    ).scalars().all()
    return list(rows)


def get_workspace_detail(db: Session, workspace_id: int, user_id: int) -> Workspace:
    _require_membership(db, workspace_id, user_id)
    return _get_workspace(db, workspace_id)


def update_workspace(db: Session, workspace_id: int, user_id: int, data: WorkspaceUpdate) -> Workspace:
    _require_membership(db, workspace_id, user_id, min_role="admin")
    ws = _get_workspace(db, workspace_id)
    if data.name is not None:
        ws.name = data.name
    if data.description is not None:
        ws.description = data.description
    _log(db, workspace_id, user_id, "updated", "workspace", f"Updated workspace '{ws.name}'", ws.id)
    db.commit()
    db.refresh(ws)
    return ws


def delete_workspace(db: Session, workspace_id: int, user_id: int):
    ws = _get_workspace(db, workspace_id)
    if ws.owner_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can delete a workspace.")
    db.delete(ws)
    db.commit()


# ---------------------------------------------------------------------------
# Member Management
# ---------------------------------------------------------------------------

def invite_member(db: Session, workspace_id: int, inviter_id: int, data: WorkspaceInvite) -> WorkspaceMember:
    _require_membership(db, workspace_id, inviter_id, min_role="admin")
    ws = _get_workspace(db, workspace_id)

    # Find the user by email
    target_user = db.execute(select(User).where(User.email == data.email)).scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail=f"No user found with email '{data.email}'.")

    # Check if already a member
    existing = db.execute(
        select(WorkspaceMember).where(
            and_(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == target_user.id)
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="User is already a member or has a pending invitation.")

    member = WorkspaceMember(
        workspace_id=workspace_id,
        user_id=target_user.id,
        role=data.role,
        invited_by_id=inviter_id,
        is_accepted=False,
        created_at=datetime.utcnow()
    )
    db.add(member)

    # Notify the invited user
    note = Notification(
        user_id=target_user.id,
        title="Workspace Invitation",
        message=f"You have been invited to join '{ws.name}' as {data.role}.",
    )
    db.add(note)
    _log(db, workspace_id, inviter_id, "invited", "member", f"Invited {data.email} as {data.role}", target_user.id)
    db.commit()
    db.refresh(member)
    return member


def respond_to_invite(db: Session, workspace_id: int, user_id: int, accept: bool) -> WorkspaceMember:
    member = db.execute(
        select(WorkspaceMember).where(
            and_(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
                WorkspaceMember.is_accepted == False
            )
        )
    ).scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="No pending invitation found.")

    if accept:
        member.is_accepted = True
        _log(db, workspace_id, user_id, "joined", "member", "Accepted workspace invitation", user_id)
        db.commit()
        db.refresh(member)
        return member
    else:
        db.delete(member)
        _log(db, workspace_id, user_id, "declined", "member", "Declined workspace invitation", user_id)
        db.commit()
        return None


def get_pending_invitations(db: Session, user_id: int) -> List[WorkspaceMember]:
    rows = db.execute(
        select(WorkspaceMember).where(
            and_(WorkspaceMember.user_id == user_id, WorkspaceMember.is_accepted == False)
        )
    ).scalars().all()
    return list(rows)


def list_members(db: Session, workspace_id: int, user_id: int) -> List[WorkspaceMember]:
    _require_membership(db, workspace_id, user_id)
    rows = db.execute(
        select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id)
    ).scalars().all()
    return list(rows)


def update_member_role(db: Session, workspace_id: int, requester_id: int, target_user_id: int, data: WorkspaceMemberUpdate) -> WorkspaceMember:
    _require_membership(db, workspace_id, requester_id, min_role="admin")
    if data.role == "owner":
        raise HTTPException(status_code=400, detail="Cannot assign 'owner' role directly. Use transfer ownership.")
    member = db.execute(
        select(WorkspaceMember).where(
            and_(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == target_user_id)
        )
    ).scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found.")
    if member.role == "owner":
        raise HTTPException(status_code=403, detail="Cannot change the owner's role.")
    old_role = member.role
    member.role = data.role
    _log(db, workspace_id, requester_id, "role_changed", "member", f"Changed role from {old_role} to {data.role}", target_user_id)
    db.commit()
    db.refresh(member)
    return member


def remove_member(db: Session, workspace_id: int, requester_id: int, target_user_id: int):
    _require_membership(db, workspace_id, requester_id, min_role="admin")
    member = db.execute(
        select(WorkspaceMember).where(
            and_(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == target_user_id)
        )
    ).scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found.")
    if member.role == "owner":
        raise HTTPException(status_code=403, detail="Cannot remove the owner.")
    if target_user_id == requester_id:
        raise HTTPException(status_code=400, detail="Use the leave endpoint to leave a workspace.")
    db.delete(member)
    _log(db, workspace_id, requester_id, "removed", "member", f"Removed member (user_id={target_user_id})", target_user_id)
    db.commit()


def leave_workspace(db: Session, workspace_id: int, user_id: int):
    ws = _get_workspace(db, workspace_id)
    if ws.owner_id == user_id:
        raise HTTPException(status_code=400, detail="Owner cannot leave. Transfer ownership or delete the workspace.")
    member = db.execute(
        select(WorkspaceMember).where(
            and_(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == user_id)
        )
    ).scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="You are not a member of this workspace.")
    db.delete(member)
    _log(db, workspace_id, user_id, "left", "member", "Left workspace", user_id)
    db.commit()


def transfer_ownership(db: Session, workspace_id: int, owner_id: int, new_owner_id: int) -> Workspace:
    ws = _get_workspace(db, workspace_id)
    if ws.owner_id != owner_id:
        raise HTTPException(status_code=403, detail="Only the workspace owner can transfer ownership.")
    new_owner_member = db.execute(
        select(WorkspaceMember).where(
            and_(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == new_owner_id,
                WorkspaceMember.is_accepted == True
            )
        )
    ).scalar_one_or_none()
    if not new_owner_member:
        raise HTTPException(status_code=404, detail="Target user is not an accepted member of this workspace.")

    # Demote current owner to admin
    current_owner_member = db.execute(
        select(WorkspaceMember).where(
            and_(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == owner_id)
        )
    ).scalar_one_or_none()
    if current_owner_member:
        current_owner_member.role = "admin"

    new_owner_member.role = "owner"
    ws.owner_id = new_owner_id
    _log(db, workspace_id, owner_id, "ownership_transferred", "workspace", f"Ownership transferred to user_id={new_owner_id}", workspace_id)
    db.commit()
    db.refresh(ws)
    return ws


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------

def add_comment(db: Session, workspace_id: int, user_id: int, data: CommentCreate) -> Comment:
    _require_membership(db, workspace_id, user_id, min_role="viewer")
    comment = Comment(
        user_id=user_id,
        workspace_id=workspace_id,
        entity_type=data.entity_type,
        entity_id=data.entity_id,
        content=data.content,
        created_at=datetime.utcnow()
    )
    db.add(comment)
    _log(db, workspace_id, user_id, "commented", data.entity_type, f"Added comment on {data.entity_type} #{data.entity_id}", data.entity_id)
    db.commit()
    db.refresh(comment)
    return comment


def get_comments(db: Session, workspace_id: int, user_id: int, entity_type: str, entity_id: int) -> List[Comment]:
    _require_membership(db, workspace_id, user_id)
    rows = db.execute(
        select(Comment).where(
            and_(
                Comment.workspace_id == workspace_id,
                Comment.entity_type == entity_type,
                Comment.entity_id == entity_id
            )
        ).order_by(Comment.created_at)
    ).scalars().all()
    return list(rows)


def delete_comment(db: Session, workspace_id: int, user_id: int, comment_id: int):
    comment = db.get(Comment, comment_id)
    if not comment or comment.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Comment not found.")
    member = _require_membership(db, workspace_id, user_id, min_role="viewer")
    if comment.user_id != user_id and _role_level(member.role) < _role_level("admin"):
        raise HTTPException(status_code=403, detail="You can only delete your own comments.")
    db.delete(comment)
    db.commit()


# ---------------------------------------------------------------------------
# Audit Log
# ---------------------------------------------------------------------------

def get_audit_log(db: Session, workspace_id: int, user_id: int, skip: int = 0, limit: int = 50) -> List[AuditLog]:
    _require_membership(db, workspace_id, user_id)
    rows = db.execute(
        select(AuditLog).where(AuditLog.workspace_id == workspace_id)
        .order_by(AuditLog.created_at.desc())
        .offset(skip).limit(limit)
    ).scalars().all()
    return list(rows)

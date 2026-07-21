from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr

class WorkspaceBase(BaseModel):
    name: str
    description: Optional[str] = None

class WorkspaceCreate(WorkspaceBase):
    pass

class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class WorkspaceResponse(WorkspaceBase):
    id: int
    owner_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class WorkspaceMemberResponse(BaseModel):
    id: int
    workspace_id: int
    user_id: int
    email: str
    full_name: str
    role: str
    is_accepted: bool
    created_at: datetime

    class Config:
        from_attributes = True

class WorkspaceInvite(BaseModel):
    email: EmailStr
    role: str = "viewer"  # 'admin', 'editor', 'viewer'

class WorkspaceMemberUpdate(BaseModel):
    role: str

class CommentBase(BaseModel):
    entity_type: str  # 'transaction', 'goal', 'bill', 'budget'
    entity_id: int
    content: str

class CommentCreate(CommentBase):
    pass

class CommentResponse(CommentBase):
    id: int
    user_id: int
    author_name: str
    created_at: datetime

    class Config:
        from_attributes = True

class AuditLogResponse(BaseModel):
    id: int
    workspace_id: int
    user_id: int
    user_name: str
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    description: str
    created_at: datetime

    class Config:
        from_attributes = True

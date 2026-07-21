from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.database.session import get_db
from app.models.user import User
from app.routers.deps import get_current_user
from app.schemas.user import UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Get current logged-in user profile info.
    """
    return current_user

@router.put("/profile", response_model=UserResponse)
def update_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update profile details for the current authenticated user.
    Supports updating full name, email, profile picture, and password.
    """
    if user_update.email and user_update.email != current_user.email:
        existing_user = db.query(User).filter(User.email == user_update.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address already exists.",
            )
        current_user.email = user_update.email

    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
        
    if user_update.profile_picture is not None:
        current_user.profile_picture = user_update.profile_picture

    if user_update.password is not None:
        current_user.password_hash = get_password_hash(user_update.password)

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user

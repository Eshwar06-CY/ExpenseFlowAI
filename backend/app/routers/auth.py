from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe

from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    ALGORITHM,
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from app.database.session import get_db
from app.models.user import User
from app.models.password_reset import PasswordResetToken
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.schemas.user import UserCreate, UserResponse
from app.services.email_service import send_password_reset_email

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account.
    Checks for email conflicts and validates strength.
    """
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )
    
    new_user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        password_hash=get_password_hash(user_in.password),
        profile_picture=user_in.profile_picture,
        is_active=True,
        is_verified=False,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=TokenResponse)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user and generate access/refresh JWT tokens.
    """
    user = db.query(User).filter(User.email == login_data.email.lower().strip()).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is deactivated.",
        )
    
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

@router.post("/refresh", response_model=TokenResponse)
def refresh(refresh_data: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Refresh access token using a valid refresh token.
    Provides token rotation.
    """
    token = refresh_data.refresh_token
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        if user_id is None or token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token.",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
        )
        
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is deactivated.",
        )
        
    new_access_token = create_access_token(subject=user.id)
    new_refresh_token = create_refresh_token(subject=user.id)
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }

@router.post("/logout")
def logout():
    """
    Mock logout endpoint.
    """
    return {"success": True, "message": "Successfully logged out."}

@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Initiate password reset. Generates a secure token, stores it in the database,
    and sends (or logs) the reset link.
    Always returns success to prevent email enumeration attacks.
    """
    user = db.query(User).filter(User.email == payload.email).first()

    if user:
        # Invalidate any existing unused tokens for this user
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.is_used == False,
        ).update({"is_used": True})

        # Generate a new cryptographically secure token
        reset_token = token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
        )

        db_token = PasswordResetToken(
            user_id=user.id,
            token=reset_token,
            expires_at=expires_at,
            is_used=False,
        )
        db.add(db_token)
        db.commit()

        # Send email or log to console
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        send_password_reset_email(
            to_email=user.email,
            reset_token=reset_token,
            reset_url=reset_url,
        )

    # Always return success (prevents email enumeration)
    return {
        "success": True,
        "message": "If an account with that email exists, a password reset link has been sent.",
    }

@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Complete the password reset using a valid, unexpired token.
    Updates the user's password hash and marks the token as used.
    """
    db_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == payload.token,
        PasswordResetToken.is_used == False,
    ).first()

    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token.",
        )

    # Check expiry
    now = datetime.now(timezone.utc)
    token_expiry = db_token.expires_at
    # Ensure timezone-aware comparison
    if token_expiry.tzinfo is None:
        token_expiry = token_expiry.replace(tzinfo=timezone.utc)
    if now > token_expiry:
        db_token.is_used = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired. Please request a new one.",
        )

    # Fetch user
    user = db.query(User).filter(User.id == db_token.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    # Update password
    user.password_hash = get_password_hash(payload.new_password)
    db_token.is_used = True
    db.commit()

    return {
        "success": True,
        "message": "Password has been reset successfully. You can now log in with your new password.",
    }

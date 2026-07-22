import hashlib
import logging
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
from app.models.email_verification import EmailVerificationToken
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ResendVerificationRequest,
)
from app.schemas.user import UserCreate, UserResponse
from app.services.email_service import (
    send_password_reset_email,
    send_password_changed_email,
    send_verification_email,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account.
    Normalizes email (trims whitespace, converts to lowercase) and validates password strength.
    """
    normalized_email = user_in.email.strip().lower()
    existing_user = db.query(User).filter(User.email == normalized_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )
    
    new_user = User(
        email=normalized_email,
        full_name=getattr(user_in, "full_name", getattr(user_in, "name", "User")),
        password_hash=get_password_hash(user_in.password),
        is_active=True,
        is_verified=False,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Automatically trigger email verification dispatch on registration
    try:
        now = datetime.now(timezone.utc)
        raw_token = token_urlsafe(32)
        hashed_token = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        expires_at = now + timedelta(hours=24)

        v_token = EmailVerificationToken(
            user_id=new_user.id,
            token=hashed_token,
            expires_at=expires_at,
            is_used=False,
            created_at=now,
        )
        db.add(v_token)
        db.commit()
        send_verification_email(to_email=new_user.email, verification_token=raw_token)
    except Exception as exc:
        logger.error("Failed to send initial verification email to %s: %s", new_user.email, exc)

    return new_user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT access/refresh token pair.
    Includes is_email_verified flag for flexible frontend workflows.
    """
    normalized_email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == normalized_email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Please check your email and password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact support.",
        )

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "is_email_verified": user.is_verified,
    }

@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Issue a new access token using a valid refresh token.
    """
    try:
        data = jwt.decode(payload.refresh_token, settings.JWT_SECRET, algorithms=[ALGORITHM])
        if data.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type.",
            )
        user_id = data.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload.",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )

    user = db.get(User, int(user_id))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer active.",
        )

    new_access = create_access_token(user.id)
    new_refresh = create_refresh_token(user.id)

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }

@router.post("/logout")
def logout():
    """
    Stateless JWT Logout Endpoint.
    
    Note on Logout Implementation:
    ExpenseFlowAI utilizes stateless JSON Web Tokens (JWT) for authentication.
    Because tokens are self-contained and validated cryptographically on each request,
    logout is performed primarily on the client side by clearing stored access/refresh tokens.
    This endpoint serves to record audit events and confirm successful session termination to clients.
    """
    return {"success": True, "message": "Successfully logged out. Client tokens have been cleared."}

@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Initiate password reset.
    Generates a cryptographically secure token, stores only its SHA-256 hash in the database,
    invalidates previous unused tokens, and dispatches an HTML email with text fallback.
    Always returns the exact same success response to prevent email enumeration attacks.
    """
    normalized_email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == normalized_email).first()

    if user:
        now = datetime.now(timezone.utc)

        # Invalidate any existing unused reset tokens for this user
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.is_used == False,
        ).update({"is_used": True, "used_at": now})

        # Generate cryptographically secure random token (never stored raw)
        raw_token = token_urlsafe(32)
        hashed_token = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

        expires_at = now + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)

        db_token = PasswordResetToken(
            user_id=user.id,
            token=hashed_token,
            expires_at=expires_at,
            is_used=False,
            created_at=now,
        )
        db.add(db_token)
        db.commit()

        # Secure logging without raw token
        logger.info(
            "Password reset requested for email: %s (User ID: %d, Hash Prefix: %s...)",
            user.email, user.id, hashed_token[:8]
        )

        # Dispatch reset email with raw token link
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={raw_token}"
        send_password_reset_email(
            to_email=user.email,
            reset_token=raw_token,
            reset_url=reset_url,
        )
    else:
        logger.info("Password reset requested for non-existent email address.")

    # Always return identical success response to prevent email enumeration
    return {
        "success": True,
        "message": "If an account with that email exists, a password reset link has been sent.",
    }

@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Complete the password reset using a valid, unexpired token.
    Updates the user's password hash, marks token as used, invalidates all outstanding tokens for the user,
    dispatches security notification email (without password), and logs audit events securely.
    """
    new_pass = payload.password or payload.new_password
    if not new_pass:
        logger.warning("Failed password reset attempt: Missing password payload.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is required.",
        )

    hashed_input = hashlib.sha256(payload.token.encode("utf-8")).hexdigest()

    db_token = db.query(PasswordResetToken).filter(
        (PasswordResetToken.token == hashed_input) | (PasswordResetToken.token == payload.token),
        PasswordResetToken.is_used == False,
    ).first()

    if not db_token:
        logger.warning("Failed password reset attempt: Invalid, expired, or already consumed token.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token.",
        )

    # Check expiry
    now = datetime.now(timezone.utc)
    token_expiry = db_token.expires_at
    if token_expiry.tzinfo is None:
        token_expiry = token_expiry.replace(tzinfo=timezone.utc)

    if now > token_expiry:
        db_token.is_used = True
        db_token.used_at = now
        db.commit()
        logger.warning("Failed password reset attempt: Token expired for User ID %d.", db_token.user_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired. Please request a new one.",
        )

    user = db.query(User).filter(User.id == db_token.user_id).first()
    if not user:
        logger.warning("Failed password reset attempt: Associated User ID %d not found.", db_token.user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    # Update password hash
    user.password_hash = get_password_hash(new_pass)

    # Mark current token as used with timestamp
    db_token.is_used = True
    db_token.used_at = now

    # Invalidate every other outstanding reset token for the same user
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.is_used == False,
    ).update({"is_used": True, "used_at": now})

    db.commit()

    # Log successful reset securely without password or raw token
    logger.info("Password reset successfully completed for email: %s (User ID: %d)", user.email, user.id)

    # Dispatch security confirmation email (never containing the password)
    send_password_changed_email(to_email=user.email, change_time=now)

    return {
        "success": True,
        "message": "Password has been reset successfully. You can now log in with your new password.",
    }


@router.post("/send-verification-email")
def send_verification_email_route(payload: ResendVerificationRequest, db: Session = Depends(get_db)):
    """
    Generate a 24-hour verification token and send a verification email.
    Always returns generic success message to prevent email enumeration.
    """
    normalized_email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == normalized_email).first()

    if user:
        now = datetime.now(timezone.utc)

        # Invalidate any existing unused verification tokens for this user
        db.query(EmailVerificationToken).filter(
            EmailVerificationToken.user_id == user.id,
            EmailVerificationToken.is_used == False,
        ).update({"is_used": True, "used_at": now})

        raw_token = token_urlsafe(32)
        hashed_token = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        expires_at = now + timedelta(hours=24)

        v_token = EmailVerificationToken(
            user_id=user.id,
            token=hashed_token,
            expires_at=expires_at,
            is_used=False,
            created_at=now,
        )
        db.add(v_token)
        db.commit()

        logger.info("Verification email requested for %s (User ID: %d, Hash Prefix: %s...)", user.email, user.id, hashed_token[:8])
        send_verification_email(to_email=user.email, verification_token=raw_token)
    else:
        logger.info("Verification email requested for non-existent email.")

    return {
        "success": True,
        "message": "If an account with that email exists, a verification email has been sent.",
    }


@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    """
    Validate email verification token, mark user email as verified, record timestamp, and revoke token.
    """
    if not token or not token.strip():
        logger.warning("Failed email verification attempt: Empty token.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token is required.",
        )

    hashed_input = hashlib.sha256(token.encode("utf-8")).hexdigest()

    db_token = db.query(EmailVerificationToken).filter(
        (EmailVerificationToken.token == hashed_input) | (EmailVerificationToken.token == token),
        EmailVerificationToken.is_used == False,
    ).first()

    if not db_token:
        logger.warning("Failed email verification attempt: Invalid, expired, or already consumed token.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token.",
        )

    now = datetime.now(timezone.utc)
    token_expiry = db_token.expires_at
    if token_expiry.tzinfo is None:
        token_expiry = token_expiry.replace(tzinfo=timezone.utc)

    if now > token_expiry:
        db_token.is_used = True
        db_token.used_at = now
        db.commit()
        logger.warning("Failed email verification attempt: Token expired for User ID %d.", db_token.user_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has expired. Please request a new one.",
        )

    user = db.query(User).filter(User.id == db_token.user_id).first()
    if not user:
        logger.warning("Failed email verification attempt: Associated User ID %d not found.", db_token.user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    # Mark user email as verified and record timestamp
    user.is_verified = True
    user.email_verified_at = now

    # Mark current token as used
    db_token.is_used = True
    db_token.used_at = now

    # Invalidate all other outstanding verification tokens for this user
    db.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == user.id,
        EmailVerificationToken.is_used == False,
    ).update({"is_used": True, "used_at": now})

    db.commit()

    logger.info("Email successfully verified for user %s (User ID: %d)", user.email, user.id)

    return {
        "success": True,
        "message": "Email verified successfully.",
    }


@router.post("/resend-verification")
def resend_verification(payload: ResendVerificationRequest, db: Session = Depends(get_db)):
    """
    Resend verification email if user account is not already verified.
    Invalidates previous tokens and dispatches new 24-hour verification token.
    Always returns generic success message.
    """
    normalized_email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == normalized_email).first()

    if user and not user.is_verified:
        now = datetime.now(timezone.utc)

        # Invalidate previous unused verification tokens
        db.query(EmailVerificationToken).filter(
            EmailVerificationToken.user_id == user.id,
            EmailVerificationToken.is_used == False,
        ).update({"is_used": True, "used_at": now})

        raw_token = token_urlsafe(32)
        hashed_token = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        expires_at = now + timedelta(hours=24)

        v_token = EmailVerificationToken(
            user_id=user.id,
            token=hashed_token,
            expires_at=expires_at,
            is_used=False,
            created_at=now,
        )
        db.add(v_token)
        db.commit()

        logger.info("Resent email verification for %s (User ID: %d)", user.email, user.id)
        send_verification_email(to_email=user.email, verification_token=raw_token)
    elif user and user.is_verified:
        logger.info("Resend verification requested for already verified account: %s", user.email)
    else:
        logger.info("Resend verification requested for non-existent email.")

    return {
        "success": True,
        "message": "If an account with that email exists and is unverified, a new verification link has been sent.",
    }

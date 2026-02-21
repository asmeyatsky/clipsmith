import os
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from datetime import datetime, timedelta
import secrets
from slowapi import Limiter
from slowapi.util import get_remote_address
from ...infrastructure.adapters.email_adapter import EmailPort, get_email_adapter

limiter = Limiter(key_func=get_remote_address)
from ...infrastructure.repositories.sqlite_user_repo import SQLiteUserRepository
from ...application.use_cases.register_user import RegisterUserUseCase
from ...application.use_cases.authenticate_user import AuthenticateUserUseCase
from ...application.dtos.auth_dto import (
    RegisterRequestDTO,
    LoginRequestDTO,
    LoginResponseDTO,
    UserResponseDTO,
    PasswordResetRequestDTO,
    PasswordResetConfirmDTO,
)
from ...infrastructure.repositories.database import get_session
from ...infrastructure.security.jwt_adapter import JWTAdapter
from ...infrastructure.security.security_adapter import SecurityAdapter
from ...infrastructure.repositories.models import PasswordResetDB
from sqlmodel import Session, select
from ...domain.ports.repository_ports import UserRepositoryPort


router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# Dependency Injection Helper
def get_user_repo(session: Session = Depends(get_session)) -> UserRepositoryPort:
    return SQLiteUserRepository(session)


def get_email_service() -> EmailPort:
    return get_email_adapter()


def get_current_user(
    request: Request, user_repo: UserRepositoryPort = Depends(get_user_repo)
):
    token = request.cookies.get("access_token")
    if not token:
        token = request.headers.get("Authorization", "").replace("Bearer ", "")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = JWTAdapter.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in token",
        )

    user = user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    return user


@router.post(
    "/register", response_model=UserResponseDTO, status_code=status.HTTP_201_CREATED
)
@limiter.limit("5/minute")
def register(
    request: Request,
    dto: RegisterRequestDTO,
    repo: UserRepositoryPort = Depends(get_user_repo),
):
    try:
        use_case = RegisterUserUseCase(repo)
        return use_case.execute(dto)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=LoginResponseDTO)
@limiter.limit("10/minute")
def login(
    request: Request,
    response: Response,
    dto: LoginRequestDTO,
    repo: UserRepositoryPort = Depends(get_user_repo),
):
    use_case = AuthenticateUserUseCase(repo)
    result = use_case.execute(dto)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    response.set_cookie(
        key="access_token",
        value=result.access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=30 * 60,
    )

    return result


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponseDTO)
def get_me(current_user=Depends(get_current_user)):
    return UserResponseDTO(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        is_active=current_user.is_active,
    )


@router.post("/password-reset/request")
@limiter.limit("2/minute")
def request_password_reset(
    request: Request,
    dto: PasswordResetRequestDTO,
    repo: UserRepositoryPort = Depends(get_user_repo),
    session: Session = Depends(get_session),
    email_service: EmailPort = Depends(get_email_service),
):
    user = repo.get_by_email(dto.email)
    if not user:
        # Return success even if email not found (security best practice)
        return {
            "message": "If an account with that email exists, a password reset link has been sent."
        }

    # Generate a secure token
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(hours=1)

    # Store the token
    reset_token = PasswordResetDB(user_id=user.id, token=token, expires_at=expires_at)
    session.add(reset_token)
    session.commit()

    # Send password reset email
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    reset_url = f"{frontend_url}/reset-password?token={token}"

    email_body = f"""Hi {user.username},

You requested a password reset for your Clipsmith account.

Click the link below to reset your password:
{reset_url}

This link will expire in 1 hour.

If you didn't request this, you can safely ignore this email.

Best,
The Clipsmith Team"""

    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #333;">Password Reset Request</h2>
        <p>Hi {user.username},</p>
        <p>You requested a password reset for your Clipsmith account.</p>
        <p>Click the button below to reset your password:</p>
        <a href="{reset_url}" style="display: inline-block; background-color: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; margin: 16px 0;">Reset Password</a>
        <p style="color: #666; font-size: 14px;">This link will expire in 1 hour.</p>
        <p style="color: #666; font-size: 14px;">If you didn't request this, you can safely ignore this email.</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;">
        <p style="color: #999; font-size: 12px;">Best,<br>The Clipsmith Team</p>
    </div>
    """

    email_service.send_email(
        to=user.email,
        subject="Reset your Clipsmith password",
        body=email_body,
        html_body=html_body,
    )

    return {
        "message": "If an account with that email exists, a password reset link has been sent."
    }


@router.post("/password-reset/confirm")
@limiter.limit("5/minute")
def confirm_password_reset(
    request: Request,
    dto: PasswordResetConfirmDTO,
    repo: UserRepositoryPort = Depends(get_user_repo),
    session: Session = Depends(get_session),
):
    # Find the reset token
    statement = select(PasswordResetDB).where(
        PasswordResetDB.token == dto.token,
        PasswordResetDB.used == False,
        PasswordResetDB.expires_at > datetime.now(),
    )
    reset_record = session.exec(statement).first()

    if not reset_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    # Get the user
    user = repo.get_by_id(reset_record.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User not found"
        )

    # Hash the new password and update
    hashed_password = SecurityAdapter.hash_password(dto.new_password)

    # Update user password directly through the session
    from ...infrastructure.repositories.models import UserDB

    user_db = session.get(UserDB, user.id)
    if user_db:
        user_db.hashed_password = hashed_password
        user_db.updated_at = datetime.now()
        session.add(user_db)

    # Mark token as used
    reset_record.used = True
    session.add(reset_record)
    session.commit()

    return {"message": "Password has been reset successfully"}


@router.get("/2fa/status", response_model=dict)
def get_2fa_status(
    current_user=Depends(get_current_user), session: Session = Depends(get_session)
):
    from ...infrastructure.repositories.models import TwoFactorSecretDB

    statement = select(TwoFactorSecretDB).where(
        TwoFactorSecretDB.user_id == current_user.id,
        TwoFactorSecretDB.is_active == True,
    )
    secret = session.exec(statement).first()

    if not secret:
        return {"enabled": False, "method": None}

    return {"enabled": True, "method": secret.method}


@router.post("/2fa/setup")
def setup_2fa(
    request: Request,
    method: str = "totp",
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    from ...infrastructure.repositories.models import TwoFactorSecretDB
    from ...application.services.two_factor_service import TwoFactorService

    existing = session.exec(
        select(TwoFactorSecretDB).where(
            TwoFactorSecretDB.user_id == current_user.id,
            TwoFactorSecretDB.is_active == True,
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=400, detail="2FA is already enabled. Disable it first."
        )

    two_factor_service = TwoFactorService(user_repo=None)

    try:
        secret, qr_code, backup_codes = two_factor_service.setup_2fa(
            user_id=current_user.id, method=method, email=current_user.email
        )

        temp_secret = TwoFactorSecretDB(
            user_id=current_user.id,
            method=method,
            secret=secret,
            backup_codes=",".join(backup_codes),
            is_active=False,
        )
        session.add(temp_secret)
        session.commit()

        return {
            "secret": secret,
            "qr_code": f"data:image/png;base64,{qr_code}",
            "backup_codes": backup_codes,
            "message": "Save these backup codes! They won't be shown again.",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/2fa/verify")
def verify_2fa(
    request: Request,
    code: str,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    from ...infrastructure.repositories.models import TwoFactorSecretDB
    from ...application.services.two_factor_service import TwoFactorService

    statement = select(TwoFactorSecretDB).where(
        TwoFactorSecretDB.user_id == current_user.id,
        TwoFactorSecretDB.is_active == False,
    )
    temp_secret = session.exec(statement).first()

    if not temp_secret:
        raise HTTPException(
            status_code=400, detail="No pending 2FA setup. Start setup first."
        )

    two_factor_service = TwoFactorService(user_repo=None)

    if two_factor_service.verify_totp_code(temp_secret.secret, code):
        temp_secret.is_active = True
        session.add(temp_secret)
        session.commit()
        return {"message": "2FA enabled successfully"}

    raise HTTPException(status_code=400, detail="Invalid verification code")


@router.post("/2fa/disable")
def disable_2fa(
    request: Request,
    password: str,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    from ...infrastructure.repositories.models import TwoFactorSecretDB, UserDB
    from ...infrastructure.security.security_adapter import SecurityAdapter

    user = session.exec(select(UserDB).where(UserDB.id == current_user.id)).first()

    if not user or not SecurityAdapter.verify_password(password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid password")

    session.exec(
        select(TwoFactorSecretDB).where(TwoFactorSecretDB.user_id == current_user.id)
    )

    session.query(TwoFactorSecretDB).filter(
        TwoFactorSecretDB.user_id == current_user.id
    ).delete()
    session.commit()

    return {"message": "2FA disabled successfully"}


@router.post("/2fa/login-verify")
def verify_2fa_login(
    request: Request, code: str, user_id: str, session: Session = Depends(get_session)
):
    from ...infrastructure.repositories.models import TwoFactorSecretDB
    from ...application.services.two_factor_service import TwoFactorService

    statement = select(TwoFactorSecretDB).where(
        TwoFactorSecretDB.user_id == user_id, TwoFactorSecretDB.is_active == True
    )
    secret_data = session.exec(statement).first()

    if not secret_data:
        return {"verified": False, "detail": "2FA not enabled"}

    two_factor_service = TwoFactorService(user_repo=None)

    if two_factor_service.verify_totp_code(secret_data.secret, code):
        return {"verified": True}

    return {"verified": False, "detail": "Invalid code"}

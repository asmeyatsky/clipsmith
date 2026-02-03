from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class EmailVerificationStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    EXPIRED = "expired"
    USED = "used"


@dataclass(frozen=True, kw_only=True)
class EmailVerification:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    email: str
    token: str
    status: EmailVerificationStatus = EmailVerificationStatus.PENDING
    expires_at: datetime
    created_at: datetime = field(default_factory=datetime.utcnow)
    verified_at: Optional[datetime] = None

    def verify(self) -> "EmailVerification":
        """Mark email as verified."""
        from ..domain.entities.email_verification import EmailVerificationStatus

        return replace(
            self, status=EmailVerificationStatus.VERIFIED, verified_at=datetime.utcnow()
        )

    def mark_as_expired(self) -> "EmailVerification":
        """Mark verification as expired."""
        from ..domain.entities.email_verification import EmailVerificationStatus

        return replace(self, status=EmailVerificationStatus.EXPIRED)

    def mark_as_used(self) -> "EmailVerification":
        """Mark verification as used."""
        from ..domain.entities.email_verification import EmailVerificationStatus

        return replace(self, status=EmailVerificationStatus.USED)


class TwoFactorMethod(str, Enum):
    TOTP = "totp"  # Time-based one-time password (Google Authenticator, Authy)
    EMAIL = "email"  # Email code verification
    SMS = "sms"  # SMS verification (not implemented yet)


@dataclass(frozen=True, kw_only=True)
class TwoFactorSecret:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    method: TwoFactorMethod
    secret: str  # Encrypted secret key
    backup_codes: Optional[str] = None  # Backup codes for recovery
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow())
    last_used_at: Optional[datetime] = None

    def deactivate(self) -> "TwoFactorSecret":
        """Deactivate 2FA method."""
        return replace(self, is_active=False, last_used_at=datetime.utcnow())


@dataclass(frozen=True, kw_only=True)
class TwoFactorVerification:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    secret_id: str
    code: str
    expires_at: datetime
    created_at: datetime = field(default_factory=datetime.utcnow())
    used_at: Optional[datetime] = None
    is_verified: bool = False

    def verify(self) -> "TwoFactorVerification":
        """Mark verification as successful."""
        return replace(self, is_verified=True, used_at=datetime.utcnow())

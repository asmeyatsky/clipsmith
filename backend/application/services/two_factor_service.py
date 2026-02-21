import secrets
import pyotp
import qrcode
import io
import base64
from datetime import datetime, timedelta
from typing import Optional
from ...domain.entities.auth_security import TwoFactorMethod


class TwoFactorService:
    def __init__(self, user_repo, two_factor_repo=None):
        self.user_repo = user_repo
        self.two_factor_repo = two_factor_repo

    def generate_totp_secret(self) -> str:
        """Generate a new TOTP secret."""
        return pyotp.random_base32()

    def get_totp_uri(self, secret: str, email: str) -> str:
        """Get the TOTP provisioning URI for QR code generation."""
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=email, issuer_name="Clipsmith")

    def generate_qr_code(self, uri: str) -> str:
        """Generate QR code as base64 string."""
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode()

    def generate_backup_codes(self, count: int = 10) -> list[str]:
        """Generate backup codes for 2FA recovery."""
        return [secrets.token_hex(4) for _ in range(count)]

    def verify_totp_code(self, secret: str, code: str) -> bool:
        """Verify a TOTP code."""
        totp = pyotp.TOTP(secret)
        return totp.verify(code)

    def setup_2fa(
        self, user_id: str, method: TwoFactorMethod, email: str
    ) -> tuple[str, str, list[str]]:
        """Setup 2FA for a user. Returns (secret, qr_code, backup_codes)."""
        if method == TwoFactorMethod.TOTP:
            secret = self.generate_totp_secret()
            uri = self.get_totp_uri(secret, email)
            qr_code = self.generate_qr_code(uri)
            backup_codes = self.generate_backup_codes()

            return secret, qr_code, backup_codes
        else:
            raise ValueError(f"Unsupported 2FA method: {method}")

    def verify_2fa(self, user_id: str, code: str) -> bool:
        """Verify a 2FA code."""
        if not self.two_factor_repo:
            return False

        secret_data = self.two_factor_repo.get_active_secret(user_id)
        if not secret_data:
            return False

        if secret_data.method == TwoFactorMethod.TOTP.value:
            return self.verify_totp_code(secret_data.secret, code)

        return False

    def disable_2fa(self, user_id: str) -> bool:
        """Disable 2FA for a user."""
        if not self.two_factor_repo:
            return False

        return self.two_factor_repo.deactivate_2fa(user_id)

    def get_2fa_status(self, user_id: str) -> dict:
        """Get 2FA status for a user."""
        if not self.two_factor_repo:
            return {"enabled": False, "method": None}

        secret_data = self.two_factor_repo.get_active_secret(user_id)
        if not secret_data:
            return {"enabled": False, "method": None}

        return {"enabled": secret_data.is_active, "method": secret_data.method}

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum
import uuid


class GDPRRequestType(str, Enum):
    DATA_EXPORT = "data_export"
    DATA_DELETION = "data_deletion"
    CONSENT_WITHDRAWAL = "consent_withdrawal"
    ACCESS_REQUEST = "access_request"
    RECTIFICATION = "rectification"
    PORTABILITY = "portability"


class ConsentType(str, Enum):
    MARKETING = "marketing"
    ANALYTICS = "analytics"
    PERSONALIZATION = "personalization"
    THIRD_PARTY = "third_party"
    COOKIES = "cookies"
    EMAIL_COMMUNICATIONS = "email_communications"


class DataCategory(str, Enum):
    PERSONAL_INFO = "personal_info"
    CONTACT_INFO = "contact_info"
    CONTENT_DATA = "content_data"
    ANALYTICS_DATA = "analytics_data"
    PAYMENT_DATA = "payment_data"
    DEVICE_DATA = "device_data"
    LOCATION_DATA = "location_data"


class RequestStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


@dataclass(frozen=True, kw_only=True)
class ConsentRecord:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    consent_type: ConsentType
    granted: bool
    granted_at: datetime = field(default_factory=lambda: datetime.utcnow())
    revoked_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    consent_text: Optional[str] = None  # The exact consent text shown to user
    version: str = "1.0"

    def revoke(self) -> "ConsentRecord":
        """Revoke consent."""
        return self.replace(granted=False, revoked_at=datetime.utcnow())


@dataclass(frozen=True, kw_only=True)
class GDPRRequest:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    request_type: GDPRRequestType
    status: RequestStatus = RequestStatus.PENDING
    data_categories: List[DataCategory] = field(default_factory=list)
    description: Optional[str] = None
    admin_notes: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())
    updated_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    verification_token: Optional[str] = None
    processed_by: Optional[str] = None  # Admin user ID

    def start_processing(self, admin_id: str) -> "GDPRRequest":
        """Mark request as being processed."""
        return self.replace(
            status=RequestStatus.PROCESSING,
            updated_at=datetime.utcnow(),
            processed_by=admin_id,
        )

    def complete(self, notes: Optional[str] = None) -> "GDPRRequest":
        """Mark request as completed."""
        return self.replace(
            status=RequestStatus.COMPLETED,
            updated_at=datetime.utcnow(),
            processed_at=datetime.utcnow(),
            admin_notes=notes,
        )

    def fail(self, reason: str) -> "GDPRRequest":
        """Mark request as failed."""
        return self.replace(
            status=RequestStatus.FAILED,
            updated_at=datetime.utcnow(),
            admin_notes=reason,
        )

    def cancel(self) -> "GDPRRequest":
        """Cancel the request."""
        return self.replace(
            status=RequestStatus.CANCELLED, updated_at=datetime.utcnow()
        )


@dataclass(frozen=True, kw_only=True)
class DataExport:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    gdpr_request_id: str
    export_format: str = "json"  # json, csv, xml
    data_categories: List[DataCategory] = field(default_factory=list)
    file_path: Optional[str] = None
    download_url: Optional[str] = None
    file_size: Optional[int] = None
    checksum: Optional[str] = None  # For integrity verification
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())
    downloaded_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    def set_expiry(self, days: int = 30) -> "DataExport":
        """Set expiry date for download link."""
        return self.replace(expires_at=datetime.utcnow() + timedelta(days=days))


@dataclass(frozen=True, kw_only=True)
class DataDeletion:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    gdpr_request_id: str
    data_categories: List[DataCategory] = field(default_factory=list)
    deletion_status: str = "pending"  # pending, in_progress, completed, failed
    deleted_items: List[str] = field(default_factory=list)  # List of deleted data types
    failed_items: List[str] = field(
        default_factory=list
    )  # Items that couldn't be deleted
    verification_required: bool = True
    verification_token: Optional[str] = None
    verification_sent_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())
    completed_at: Optional[datetime] = None

    def start_deletion(self) -> "DataDeletion":
        """Start the deletion process."""
        return self.replace(deletion_status="in_progress")

    def complete_deletion(self, deleted_items: List[str]) -> "DataDeletion":
        """Complete the deletion process."""
        return self.replace(
            deletion_status="completed",
            deleted_items=deleted_items,
            completed_at=datetime.utcnow(),
        )


@dataclass(frozen=True, kw_only=True)
class CookieConsent:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    consent_categories: List[ConsentType] = field(default_factory=list)
    analytics_consent: bool = False
    marketing_consent: bool = False
    personalization_consent: bool = False
    third_party_consent: bool = False
    essential_cookies: bool = True  # Always required for functionality
    consent_version: str = "1.0"
    granted_at: datetime = field(default_factory=lambda: datetime.utcnow())
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    last_updated: datetime = field(default_factory=lambda: datetime.utcnow())

    def update_consent(self, **consent_updates) -> "CookieConsent":
        """Update specific consent categories."""
        current_consent = {
            "analytics_consent": self.analytics_consent,
            "marketing_consent": self.marketing_consent,
            "personalization_consent": self.personalization_consent,
            "third_party_consent": self.third_party_consent,
        }

        # Update with new values
        current_consent.update(consent_updates)

        return self.replace(**current_consent, last_updated=datetime.utcnow())


@dataclass(frozen=True, kw_only=True)
class PrivacySettings:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    profile_visibility: str = "public"  # public, private, friends_only
    data_sharing: bool = True
    analytics_tracking: bool = True
    personalized_content: bool = True
    email_communications: bool = True
    push_notifications: bool = True
    third_party_sharing: bool = False
    data_retention_days: int = 365  # How long to retain user data
    auto_delete_inactive: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())
    updated_at: Optional[datetime] = None

    def update_setting(self, **settings) -> "PrivacySettings":
        """Update privacy settings."""
        return self.replace(**settings, updated_at=datetime.utcnow())

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime
from ..entities.gdpr import (
    ConsentRecord,
    GDPRRequest,
    DataExport,
    DataDeletion,
    CookieConsent,
    PrivacySettings,
    GDPRRequestType,
    ConsentType,
    DataCategory,
    RequestStatus,
)


class GDPRRepositoryPort(ABC):
    """Repository port for GDPR compliance operations."""

    # Consent Records
    @abstractmethod
    def save_consent_record(self, consent: ConsentRecord) -> ConsentRecord:
        """Save or update consent record."""
        pass

    @abstractmethod
    def get_user_consents(
        self, user_id: str, consent_type: Optional[ConsentType] = None
    ) -> List[ConsentRecord]:
        """Get user's consent records."""
        pass

    @abstractmethod
    def get_active_consents(self, user_id: str) -> List[ConsentRecord]:
        """Get user's currently active consents."""
        pass

    @abstractmethod
    def revoke_consent(self, consent_id: str) -> Optional[ConsentRecord]:
        """Revoke a specific consent."""
        pass

    # GDPR Requests
    @abstractmethod
    def save_gdpr_request(self, request: GDPRRequest) -> GDPRRequest:
        """Save or update GDPR request."""
        pass

    @abstractmethod
    def get_gdpr_request(self, request_id: str) -> Optional[GDPRRequest]:
        """Get GDPR request by ID."""
        pass

    @abstractmethod
    def get_user_gdpr_requests(
        self, user_id: str, request_type: Optional[GDPRRequestType] = None
    ) -> List[GDPRRequest]:
        """Get user's GDPR requests."""
        pass

    @abstractmethod
    def get_pending_requests(
        self, request_type: Optional[GDPRRequestType] = None
    ) -> List[GDPRRequest]:
        """Get all pending GDPR requests."""
        pass

    @abstractmethod
    def update_gdpr_request(self, request: GDPRRequest) -> GDPRRequest:
        """Update GDPR request status."""
        pass

    # Data Exports
    @abstractmethod
    def save_data_export(self, export: DataExport) -> DataExport:
        """Save or update data export."""
        pass

    @abstractmethod
    def get_data_export(self, export_id: str) -> Optional[DataExport]:
        """Get data export by ID."""
        pass

    @abstractmethod
    def get_user_data_exports(self, user_id: str) -> List[DataExport]:
        """Get user's data exports."""
        pass

    @abstractmethod
    def get_expired_exports(self) -> List[DataExport]:
        """Get expired data exports for cleanup."""
        pass

    @abstractmethod
    def delete_expired_exports(self) -> int:
        """Delete expired export files and records."""
        pass

    # Data Deletions
    @abstractmethod
    def save_data_deletion(self, deletion: DataDeletion) -> DataDeletion:
        """Save or update data deletion."""
        pass

    @abstractmethod
    def get_data_deletion(self, deletion_id: str) -> Optional[DataDeletion]:
        """Get data deletion by ID."""
        pass

    @abstractmethod
    def get_user_data_deletions(self, user_id: str) -> List[DataDeletion]:
        """Get user's data deletions."""
        pass

    @abstractmethod
    def update_data_deletion(self, deletion: DataDeletion) -> DataDeletion:
        """Update data deletion status."""
        pass

    # Cookie Consent
    @abstractmethod
    def save_cookie_consent(self, consent: CookieConsent) -> CookieConsent:
        """Save or update cookie consent."""
        pass

    @abstractmethod
    def get_cookie_consent(self, user_id: str) -> Optional[CookieConsent]:
        """Get user's cookie consent."""
        pass

    @abstractmethod
    def update_cookie_consent(self, consent: CookieConsent) -> CookieConsent:
        """Update cookie consent."""
        pass

    # Privacy Settings
    @abstractmethod
    def save_privacy_settings(self, settings: PrivacySettings) -> PrivacySettings:
        """Save or update privacy settings."""
        pass

    @abstractmethod
    def get_privacy_settings(self, user_id: str) -> Optional[PrivacySettings]:
        """Get user's privacy settings."""
        pass

    @abstractmethod
    def update_privacy_settings(self, settings: PrivacySettings) -> PrivacySettings:
        """Update privacy settings."""
        pass

    # Data Management
    @abstractmethod
    def collect_user_data(
        self, user_id: str, data_categories: List[DataCategory]
    ) -> Dict[str, Any]:
        """Collect user data for export/deletion."""
        pass

    @abstractmethod
    def delete_user_data(
        self, user_id: str, data_categories: List[DataCategory]
    ) -> Dict[str, bool]:
        """Delete specific user data categories."""
        pass

    @abstractmethod
    def anonymize_user_data(self, user_id: str) -> bool:
        """Anonymize user data instead of full deletion."""
        pass

    # Audit and Compliance
    @abstractmethod
    def get_consent_audit_log(
        self, user_id: str, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get audit log for consent changes."""
        pass

    @abstractmethod
    def get_gdpr_statistics(self) -> Dict[str, Any]:
        """Get GDPR compliance statistics."""
        pass

    @abstractmethod
    def get_data_retention_report(self) -> List[Dict[str, Any]]:
        """Get report of data retention across all users."""
        pass


class GDPRServicePort(ABC):
    """Service port for GDPR compliance operations."""

    # Data Export Service
    @abstractmethod
    async def generate_data_export(
        self,
        user_id: str,
        data_categories: List[DataCategory],
        export_format: str = "json",
    ) -> Dict[str, Any]:
        """Generate data export for user."""
        pass

    @abstractmethod
    async def create_export_download_url(self, export_id: str) -> str:
        """Create secure download URL for data export."""
        pass

    # Data Deletion Service
    @abstractmethod
    async def process_data_deletion(self, deletion_id: str) -> Dict[str, Any]:
        """Process data deletion request."""
        pass

    @abstractmethod
    async def verify_deletion_request(self, token: str) -> Dict[str, Any]:
        """Verify deletion request token."""
        pass

    # Consent Management Service
    @abstractmethod
    async def record_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
        granted: bool,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Record user consent."""
        pass

    @abstractmethod
    async def withdraw_consent(
        self, user_id: str, consent_type: ConsentType, reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Withdraw user consent."""
        pass

    # Notification Service
    @abstractmethod
    async def send_gdpr_notification(
        self, user_id: str, request_type: GDPRRequestType, details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send GDPR-related notifications to user."""
        pass

    @abstractmethod
    async def send_admin_notification(
        self, request_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send notification to administrators about GDPR requests."""
        pass

    # Compliance Checking Service
    @abstractmethod
    async def check_compliance_status(self, user_id: str) -> Dict[str, Any]:
        """Check if user account is compliant with GDPR requirements."""
        pass

    @abstractmethod
    async def generate_compliance_report(self) -> Dict[str, Any]:
        """Generate overall GDPR compliance report."""
        pass

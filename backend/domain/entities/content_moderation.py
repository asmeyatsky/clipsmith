from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
import uuid


class ModerationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FLAGGED = "flagged"
    UNDER_REVIEW = "under_review"


class ModerationType(str, Enum):
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    USER_REPORT = "user_report"


class ModerationSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ModerationReason(str, Enum):
    # AI-detected reasons
    INAPPROPRIATE_CONTENT = "inappropriate_content"
    SPAM = "spam"
    HATE_SPEECH = "hate_speech"
    VIOLENCE = "violence"
    COPYRIGHT_VIOLATION = "copyright_violation"
    HARASSMENT = "harassment"
    SELF_HARM = "self_harm"
    MISINFORMATION = "misinformation"

    # Manual review reasons
    COMMUNITY_GUIDELINE_VIOLATION = "community_guideline_violation"
    TERMS_OF_SERVICE_VIOLATION = "terms_of_service_violation"
    LEGAL_ISSUE = "legal_issue"
    QUALITY_ISSUE = "quality_issue"
    DUPLICATE_CONTENT = "duplicate_content"


@dataclass(frozen=True, kw_only=True)
class ContentModeration:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content_type: str  # "video", "comment", "user_profile", etc.
    content_id: str  # ID of the content being moderated
    user_id: Optional[str] = None  # Content creator (if applicable)
    reporter_id: Optional[str] = None  # User who reported (if applicable)
    status: ModerationStatus = ModerationStatus.PENDING
    moderation_type: ModerationType
    severity: ModerationSeverity = ModerationSeverity.LOW
    reason: Optional[ModerationReason] = None
    confidence_score: Optional[float] = None  # AI confidence score (0.0-1.0)
    ai_labels: Optional[Dict[str, Any]] = None  # AI classification details
    human_reviewer_id: Optional[str] = None  # ID of human moderator
    human_notes: Optional[str] = None  # Human moderator notes
    auto_action: Optional[str] = None  # Action taken by AI (reject, approve, etc.)
    created_at: datetime = field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def approve(
        self, reviewer_id: str, notes: Optional[str] = None
    ) -> "ContentModeration":
        """Mark content as approved."""
        return replace(
            self,
            status=ModerationStatus.APPROVED,
            human_reviewer_id=reviewer_id,
            human_notes=notes,
            reviewed_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )

    def reject(
        self,
        reviewer_id: str,
        reason: ModerationReason,
        severity: ModerationSeverity,
        notes: Optional[str] = None,
    ) -> "ContentModeration":
        """Mark content as rejected."""
        return replace(
            self,
            status=ModerationStatus.REJECTED,
            human_reviewer_id=reviewer_id,
            reason=reason,
            severity=severity,
            human_notes=notes,
            reviewed_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )

    def escalate_to_human(self) -> "ContentModeration":
        """Escalate to human review."""
        return replace(
            self, status=ModerationStatus.UNDER_REVIEW, reviewed_at=datetime.utcnow()
        )

    def auto_approve(self, confidence: float = 1.0) -> "ContentModeration":
        """Auto-approve content with high AI confidence."""
        return replace(
            self,
            status=ModerationStatus.APPROVED,
            confidence_score=confidence,
            auto_action="auto_approve",
            reviewed_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )

    def auto_reject(
        self,
        reason: ModerationReason,
        confidence: float,
        severity: ModerationSeverity,
        labels: Optional[Dict[str, Any]] = None,
    ) -> "ContentModeration":
        """Auto-reject content based on AI analysis."""
        return replace(
            self,
            status=ModerationStatus.REJECTED,
            reason=reason,
            severity=severity,
            confidence_score=confidence,
            ai_labels=labels,
            auto_action=f"auto_reject_{reason.value}",
            reviewed_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )

    def flag_for_review(
        self, confidence: float, labels: Optional[Dict[str, Any]] = None
    ) -> "ContentModeration":
        """Flag content that needs human review."""
        return replace(
            self,
            status=ModerationStatus.FLAGGED,
            confidence_score=confidence,
            ai_labels=labels,
            auto_action="flag_for_review",
            reviewed_at=datetime.utcnow(),
        )

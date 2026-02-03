import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from ..domain.entities.content_moderation import (
    ContentModeration,
    ModerationStatus,
    ModerationType,
    ModerationSeverity,
    ModerationReason,
)
from ..domain.ports.repository_ports import ContentModerationRepositoryPort

logger = logging.getLogger(__name__)


class AIModerationService:
    """AI-powered content moderation service."""

    def __init__(self, moderation_repo: ContentModerationRepositoryPort):
        self.moderation_repo = moderation_repo

        # Configure moderation thresholds
        self.approval_threshold = 0.9  # Confidence threshold for auto-approval
        self.rejection_threshold = 0.7  # Minimum confidence for auto-rejection
        self.flag_threshold = 0.6  # Below this confidence, flag for human review

    def analyze_video(
        self,
        video_id: str,
        title: str,
        description: str,
        thumbnail_url: Optional[str] = None,
    ) -> ContentModeration:
        """Analyze video content for moderation."""
        # Simulate AI analysis (in production, would call real AI service)
        analysis_result = self._simulate_video_ai_analysis(title, description)

        # Create moderation record
        moderation = ContentModeration(
            content_type="video",
            content_id=video_id,
            moderation_type=ModerationType.AUTOMATIC,
            severity=analysis_result["severity"],
            reason=analysis_result["reason"],
            confidence_score=analysis_result["confidence"],
            ai_labels=analysis_result["labels"],
        )

        # Determine action based on confidence
        if analysis_result["confidence"] >= self.approval_threshold:
            return moderation.auto_approve(analysis_result["confidence"])
        elif analysis_result["confidence"] <= self.rejection_threshold:
            return moderation.auto_reject(
                analysis_result["reason"],
                analysis_result["confidence"],
                analysis_result["severity"],
                analysis_result["labels"],
            )
        else:
            return moderation.flag_for_review(
                analysis_result["confidence"], analysis_result["labels"]
            )

    def analyze_comment(
        self, comment_id: str, content: str, user_id: str
    ) -> ContentModeration:
        """Analyze comment content for moderation."""
        analysis_result = self._simulate_comment_ai_analysis(content)

        # Create moderation record
        moderation = ContentModeration(
            content_type="comment",
            content_id=comment_id,
            user_id=user_id,  # Comment author
            moderation_type=ModerationType.AUTOMATIC,
            severity=analysis_result["severity"],
            reason=analysis_result["reason"],
            confidence_score=analysis_result["confidence"],
            ai_labels=analysis_result["labels"],
        )

        # Comments are more sensitive - require higher confidence
        if analysis_result["confidence"] >= 0.95:
            return moderation.auto_approve(analysis_result["confidence"])
        elif analysis_result["confidence"] <= 0.8:
            return moderation.auto_reject(
                analysis_result["reason"],
                analysis_result["confidence"],
                analysis_result["severity"],
                analysis_result["labels"],
            )
        else:
            return moderation.flag_for_review(
                analysis_result["confidence"], analysis_result["labels"]
            )

    def analyze_user_profile(
        self, user_id: str, profile_data: Dict[str, Any]
    ) -> ContentModeration:
        """Analyze user profile for moderation."""
        analysis_result = self._simulate_profile_ai_analysis(profile_data)

        moderation = ContentModeration(
            content_type="user_profile",
            content_id=user_id,
            user_id=user_id,
            moderation_type=ModerationType.AUTOMATIC,
            severity=analysis_result["severity"],
            reason=analysis_result["reason"],
            confidence_score=analysis_result["confidence"],
            ai_labels=analysis_result["labels"],
        )

        if analysis_result["confidence"] >= 0.85:
            return moderation.auto_approve(analysis_result["confidence"])
        elif analysis_result["confidence"] <= 0.7:
            return moderation.auto_reject(
                analysis_result["reason"],
                analysis_result["confidence"],
                analysis_result["severity"],
                analysis_result["labels"],
            )
        else:
            return moderation.flag_for_review(
                analysis_result["confidence"], analysis_result["labels"]
            )

    def _simulate_video_ai_analysis(
        self, title: str, description: str
    ) -> Dict[str, Any]:
        """
        Simulate AI video content analysis.
        In production, this would call real AI services like:
        - AWS Rekognition
        - Google Cloud Vision API
        - Azure Content Moderator
        - OpenAI CLIP
        """

        text_content = f"{title} {description}".lower()

        # Check for policy violations
        violations = []
        confidence = 1.0
        severity = ModerationSeverity.LOW
        reason = None
        labels = {}

        # Inappropriate content detection
        inappropriate_words = ["explicit", "nsfw", "adult", "sexual", "nude", "porn"]
        if any(word in text_content for word in inappropriate_words):
            violations.append("inappropriate_content")
            confidence *= 0.7
            severity = ModerationSeverity.HIGH
            reason = ModerationReason.INAPPROPRIATE_CONTENT

        # Hate speech detection
        hate_words = [
            "hate",
            "racist",
            "homophobic",
            "transphobic",
            "sexist",
            "nazi",
            "terrorist",
        ]
        if any(word in text_content for word in hate_words):
            violations.append("hate_speech")
            confidence *= 0.6
            severity = ModerationSeverity.CRITICAL
            reason = ModerationReason.HATE_SPEECH

        # Spam detection
        spam_indicators = [
            "click here",
            "buy now",
            "limited offer",
            "free money",
            "bitcoin",
            "crypto",
        ]
        if len([word for word in spam_indicators if word in text_content]) >= 2:
            violations.append("spam")
            confidence *= 0.8
            severity = ModerationSeverity.MEDIUM
            reason = ModerationReason.SPAM

        # Violence detection
        violence_words = [
            "kill",
            "murder",
            "violence",
            "weapon",
            "gun",
            "fight",
            "attack",
        ]
        if any(word in text_content for word in violence_words):
            violations.append("violence")
            confidence *= 0.5
            severity = ModerationSeverity.HIGH
            reason = ModerationReason.VIOLENCE

        # Self harm detection
        self_harm_words = [
            "suicide",
            "self harm",
            "depression",
            "anxiety",
            "cut",
            "hurt",
        ]
        if any(word in text_content for word in self_harm_words):
            violations.append("self_harm")
            confidence *= 0.4
            severity = ModerationSeverity.CRITICAL
            reason = ModerationReason.SELF_HARM

        # Adjust confidence based on number of violations
        if len(violations) > 1:
            confidence *= 0.8

        labels.update(
            {
                "violations": violations,
                "text_length": len(text_content),
                "has_url": "http" in text_content.lower()
                or "www." in text_content.lower(),
                "has_excessive_caps": sum(1 for c in text_content if c.isupper())
                > len(text_content) * 0.7,
            }
        )

        if violations:
            return {
                "reason": reason,
                "severity": severity,
                "confidence": confidence,
                "labels": labels,
            }
        else:
            return {
                "reason": None,
                "severity": ModerationSeverity.LOW,
                "confidence": 0.95,  # High confidence for clean content
                "labels": {"clean": True, "text_analysis": "passed_all_checks"},
            }

    def _simulate_comment_ai_analysis(self, content: str) -> Dict[str, Any]:
        """Simulate AI comment analysis."""
        text_content = content.lower()
        violations = []
        confidence = 1.0
        severity = ModerationSeverity.LOW
        reason = None
        labels = {}

        # Check for toxic behavior
        toxic_words = [
            "idiot",
            "stupid",
            "moron",
            "dumb",
            "loser",
            "hate",
            "kill yourself",
        ]
        if any(word in text_content for word in toxic_words):
            violations.append("toxic_behavior")
            confidence *= 0.6
            severity = ModerationSeverity.MEDIUM
            reason = ModerationReason.HARASSMENT

        # Check for spam patterns
        spam_patterns = ["http", "www.", "click here", "buy now", "free money"]
        if any(pattern in text_content for pattern in spam_patterns):
            violations.append("spam")
            confidence *= 0.7
            severity = ModerationSeverity.MEDIUM
            reason = ModerationReason.SPAM

        # Excessive punctuation/caps
        exclamation_count = text_content.count("!")
        question_count = text_content.count("?")
        caps_ratio = sum(1 for c in text_content if c.isupper()) / max(
            len(text_content), 1
        )

        if exclamation_count > 3 or question_count > 3 or caps_ratio > 0.7:
            violations.append("aggressive_language")
            confidence *= 0.8
            severity = ModerationSeverity.MEDIUM

        labels.update(
            {
                "toxic_score": len(toxic_words) / len(text_content.split()),
                "spam_indicators": len(spam_patterns) / len(text_content.split()),
                "exclamation_count": exclamation_count,
                "caps_ratio": caps_ratio,
            }
        )

        if violations:
            return {
                "reason": reason,
                "severity": severity,
                "confidence": confidence,
                "labels": labels,
            }
        else:
            return {
                "reason": None,
                "severity": ModerationSeverity.LOW,
                "confidence": 0.9,  # Slightly lower threshold for comments
                "labels": {"clean": True, "comment_analysis": "passed_all_checks"},
            }

    def _simulate_profile_ai_analysis(
        self, profile_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate AI user profile analysis."""
        violations = []
        confidence = 1.0
        severity = ModerationSeverity.LOW
        reason = None
        labels = {}

        # Check username
        username = profile_data.get("username", "").lower()
        if any(
            word in username
            for word in ["admin", "official", "support", "fake", "spam", "bot"]
        ):
            violations.append("suspicious_username")
            confidence *= 0.7
            severity = ModerationSeverity.MEDIUM
            reason = ModerationReason.SPAM

        # Check bio/description
        bio = profile_data.get("bio", "").lower()
        if len(bio) > 0:
            bio_words = bio.split()
            suspicious_words = ["scam", "fraud", "fake", "imposter", "clickbait"]
            if any(word in bio_words for word in suspicious_words):
                violations.append("suspicious_profile_content")
                confidence *= 0.6
                severity = ModerationSeverity.HIGH
                reason = ModerationReason.TERMS_OF_SERVICE_VIOLATION

        labels.update(
            {
                "username_suspicious": "suspicious_username" in violations,
                "bio_suspicious": "suspicious_profile_content" in violations,
                "profile_length": len(bio),
            }
        )

        if violations:
            return {
                "reason": reason,
                "severity": severity,
                "confidence": confidence,
                "labels": labels,
            }
        else:
            return {
                "reason": None,
                "severity": ModerationSeverity.LOW,
                "confidence": 0.9,
                "labels": {"clean": True, "profile_analysis": "passed_all_checks"},
            }


class HumanModerationService:
    """Human moderation review service."""

    def __init__(self, moderation_repo: ContentModerationRepositoryPort):
        self.moderation_repo = moderation_repo

    def review_pending_content(
        self, reviewer_id: str, limit: int = 20
    ) -> List[ContentModeration]:
        """Get content pending human review."""
        return self.moderation_repo.get_pending_moderations(limit)

    def approve_content(
        self, moderation_id: str, reviewer_id: str, notes: Optional[str] = None
    ) -> Optional[ContentModeration]:
        """Approve content after human review."""
        moderation = self.moderation_repo.get_by_id(moderation_id)
        if not moderation:
            return None

        if moderation.status != ModerationStatus.PENDING:
            logger.warning(f"Content {moderation_id} is not pending review")
            return None

        approved_moderation = moderation.approve(reviewer_id, notes)
        return self.moderation_repo.save(approved_moderation)

    def reject_content(
        self,
        moderation_id: str,
        reviewer_id: str,
        reason: ModerationReason,
        severity: ModerationSeverity,
        notes: Optional[str] = None,
    ) -> Optional[ContentModeration]:
        """Reject content after human review."""
        moderation = self.moderation_repo.get_by_id(moderation_id)
        if not moderation:
            return None

        if moderation.status != ModerationStatus.PENDING:
            logger.warning(f"Content {moderation_id} is not pending review")
            return None

        rejected_moderation = moderation.reject(reviewer_id, reason, severity, notes)
        return self.moderation_repo.save(rejected_moderation)

    def get_reviewer_statistics(
        self, reviewer_id: str, days: int = 30
    ) -> Dict[str, Any]:
        """Get statistics for a specific reviewer."""
        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        moderations = self.moderation_repo.get_moderations_by_reviewer(reviewer_id)

        # Filter by date range
        recent_moderations = [
            m for m in moderations if m.completed_at and m.completed_at >= cutoff_date
        ]

        total_reviews = len(recent_moderations)
        approved_count = sum(
            1 for m in recent_moderations if m.status == ModerationStatus.APPROVED.value
        )
        rejected_count = sum(
            1 for m in recent_moderations if m.status == ModerationStatus.REJECTED.value
        )

        # Calculate average time to review
        if recent_moderations:
            review_times = [
                (m.completed_at - m.created_at).total_seconds() / 3600
                for m in recent_moderations
                if m.completed_at and m.created_at
            ]
            avg_review_time = sum(review_times) / len(review_times)
        else:
            avg_review_time = 0

        return {
            "reviewer_id": reviewer_id,
            "period_days": days,
            "total_reviews": total_reviews,
            "approved_count": approved_count,
            "rejected_count": rejected_count,
            "approval_rate": round(approved_count / total_reviews * 100, 2)
            if total_reviews > 0
            else 0,
            "average_review_time_hours": round(avg_review_time, 2),
            "reviews_per_day": round(total_reviews / days, 2) if days > 0 else 0,
        }

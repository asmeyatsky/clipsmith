from typing import List, Optional
from sqlmodel import Session, select, func, and_, desc
from ...domain.entities.content_moderation import (
    ContentModeration,
    ModerationStatus,
    ModerationType,
    ModerationSeverity,
)
from ...domain.ports.repository_ports import ContentModerationRepositoryPort
from .database import engine
from .models import ContentModerationDB


class SQLiteContentModerationRepository(ContentModerationRepositoryPort):
    def __init__(self, session: Session):
        self.session = session

    def save(self, moderation: ContentModeration) -> ContentModeration:
        moderation_db = ContentModerationDB.model_validate(moderation)
        moderation_db = self.session.merge(moderation_db)
        self.session.commit()
        self.session.refresh(moderation_db)
        return ContentModeration(**moderation_db.model_dump())

    def get_by_id(self, moderation_id: str) -> Optional[ContentModeration]:
        moderation_db = self.session.get(ContentModerationDB, moderation_id)
        if moderation_db:
            return ContentModeration(**moderation_db.model_dump())
        return None

    def get_pending_moderations(self, limit: int = 50) -> List[ContentModeration]:
        """Get content pending human review."""
        statement = (
            select(ContentModerationDB)
            .where(ContentModerationDB.status == ModerationStatus.PENDING.value)
            .order_by(ContentModerationDB.created_at.desc())
            .limit(limit)
        )
        results = self.session.exec(statement).all()
        return [ContentModeration(**m.model_dump()) for m in results]

    def get_moderations_by_content_id(
        self, content_id: str, content_type: Optional[str] = None
    ) -> List[ContentModeration]:
        """Get all moderation records for specific content."""
        query = select(ContentModerationDB).where(
            ContentModerationDB.content_id == content_id
        )

        if content_type:
            query = query.where(ContentModerationDB.content_type == content_type)

        query = query.order_by(ContentModerationDB.created_at.desc())

        results = self.session.exec(query).all()
        return [ContentModeration(**m.model_dump()) for m in results]

    def get_moderations_by_status(
        self, status: ModerationStatus, limit: int = 100
    ) -> List[ContentModeration]:
        """Get moderations by status."""
        statement = (
            select(ContentModerationDB)
            .where(ContentModerationDB.status == status.value)
            .order_by(ContentModerationDB.created_at.desc())
            .limit(limit)
        )
        results = self.session.exec(statement).all()
        return [ContentModeration(**m.model_dump()) for m in results]

    def get_moderations_by_reviewer(
        self, reviewer_id: str, limit: int = 100
    ) -> List[ContentModeration]:
        """Get moderations reviewed by specific reviewer."""
        statement = (
            select(ContentModerationDB)
            .where(ContentModerationDB.human_reviewer_id == reviewer_id)
            .order_by(ContentModerationDB.completed_at.desc())
            .limit(limit)
        )
        results = self.session.exec(statement).all()
        return [ContentModeration(**m.model_dump()) for m in results]

    def get_flagged_content(
        self, severity: Optional[ModerationSeverity] = None, limit: int = 50
    ) -> List[ContentModeration]:
        """Get flagged content that needs attention."""
        query = select(ContentModerationDB).where(
            ContentModerationDB.status == ModerationStatus.FLAGGED.value
        )

        if severity:
            query = query.where(ContentModerationDB.severity == severity.value)

        query = query.order_by(
            desc(ContentModerationDB.severity), ContentModerationDB.created_at.desc()
        ).limit(limit)

        results = self.session.exec(query).all()
        return [ContentModeration(**m.model_dump()) for m in results]

    def get_statistics(self, days: int = 30) -> Dict[str, int]:
        """Get moderation statistics for the last N days."""
        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Total moderated
        total_query = (
            select(func.count())
            .select_from(ContentModerationDB)
            .where(ContentModerationDB.created_at >= cutoff_date)
        )
        total_count = self.session.exec(total_query).one()

        # By status
        approved_query = (
            select(func.count())
            .select_from(ContentModerationDB)
            .where(
                and_(
                    ContentModerationDB.created_at >= cutoff_date,
                    ContentModerationDB.status == ModerationStatus.APPROVED.value,
                )
            )
        )
        approved_count = self.session.exec(approved_query).one()

        rejected_query = (
            select(func.count())
            .select_from(ContentModerationDB)
            .where(
                and_(
                    ContentModerationDB.created_at >= cutoff_date,
                    ContentModerationDB.status == ModerationStatus.REJECTED.value,
                )
            )
        )
        rejected_count = self.session.exec(rejected_query).one()

        flagged_query = (
            select(func.count())
            .select_from(ContentModerationDB)
            .where(
                and_(
                    ContentModerationDB.created_at >= cutoff_date,
                    ContentModerationDB.status == ModerationStatus.FLAGGED.value,
                )
            )
        )
        flagged_count = self.session.exec(flagged_query).one()

        # By severity
        high_severity_query = (
            select(func.count())
            .select_from(ContentModerationDB)
            .where(
                and_(
                    ContentModerationDB.created_at >= cutoff_date,
                    ContentModerationDB.severity == ModerationSeverity.HIGH.value,
                )
            )
        )
        high_severity_count = self.session.exec(high_severity_query).one()

        critical_severity_query = (
            select(func.count())
            .select_from(ContentModerationDB)
            .where(
                and_(
                    ContentModerationDB.created_at >= cutoff_date,
                    ContentModerationDB.severity == ModerationSeverity.CRITICAL.value,
                )
            )
        )
        critical_severity_count = self.session.exec(critical_severity_query).one()

        return {
            "total_moderated": total_count,
            "approved": approved_count,
            "rejected": rejected_count,
            "flagged": flagged_count,
            "high_severity": high_severity_count,
            "critical_severity": critical_severity_count,
            "approval_rate": round(approved_count / total_count * 100, 2)
            if total_count > 0
            else 0,
            "rejection_rate": round(rejected_count / total_count * 100, 2)
            if total_count > 0
            else 0,
        }

    def delete_old_records(self, days: int = 90) -> int:
        """Clean up old moderation records."""
        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        statement = select(ContentModerationDB).where(
            ContentModerationDB.completed_at < cutoff_date
        )

        old_records = self.session.exec(statement).all()

        deleted_count = 0
        for record in old_records:
            self.session.delete(record)
            deleted_count += 1

        self.session.commit()
        return deleted_count

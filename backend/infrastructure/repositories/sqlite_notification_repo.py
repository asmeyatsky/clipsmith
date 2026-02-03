from typing import List, Optional
from sqlmodel import Session, select, func, and_
from ...domain.entities.notification import Notification, NotificationStatus
from ...domain.ports.repository_ports import NotificationRepositoryPort
from .database import engine
from .models import NotificationDB


class SQLiteNotificationRepository(NotificationRepositoryPort):
    def __init__(self, session: Session):
        self.session = session

    def save(self, notification: Notification) -> Notification:
        notification_db = NotificationDB.model_validate(notification)
        notification_db = self.session.merge(notification_db)
        self.session.commit()
        self.session.refresh(notification_db)
        return Notification(**notification_db.model_dump())

    def get_by_id(self, notification_id: str) -> Optional[Notification]:
        notification_db = self.session.get(NotificationDB, notification_id)
        if notification_db:
            return Notification(**notification_db.model_dump())
        return None

    def get_user_notifications(
        self,
        user_id: str,
        status: Optional[NotificationStatus] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> List[Notification]:
        query = select(NotificationDB).where(NotificationDB.user_id == user_id)

        if status:
            query = query.where(NotificationDB.status == status.value)

        query = (
            query.order_by(NotificationDB.created_at.desc()).offset(offset).limit(limit)
        )

        results = self.session.exec(query).all()
        return [Notification(**n.model_dump()) for n in results]

    def count_user_notifications(
        self, user_id: str, status: Optional[NotificationStatus] = None
    ) -> int:
        query = (
            select(func.count())
            .select_from(NotificationDB)
            .where(NotificationDB.user_id == user_id)
        )

        if status:
            query = query.where(NotificationDB.status == status.value)

        return self.session.exec(query).one()

    def mark_as_read(self, notification_id: str) -> Optional[Notification]:
        notification_db = self.session.get(NotificationDB, notification_id)
        if notification_db:
            notification_db.status = NotificationStatus.READ.value
            notification_db.read_at = datetime.utcnow()
            self.session.add(notification_db)
            self.session.commit()
            self.session.refresh(notification_db)
            return Notification(**notification_db.model_dump())
        return None

    def mark_all_as_read(self, user_id: str) -> int:
        """Mark all unread notifications for a user as read."""
        from datetime import datetime

        # Get all unread notifications
        query = select(NotificationDB).where(
            and_(
                NotificationDB.user_id == user_id,
                NotificationDB.status == NotificationStatus.UNREAD.value,
            )
        )

        unread_notifications = self.session.exec(query).all()

        # Mark as read
        count = 0
        for notification_db in unread_notifications:
            notification_db.status = NotificationStatus.READ.value
            notification_db.read_at = datetime.utcnow()
            self.session.add(notification_db)
            count += 1

        self.session.commit()
        return count

    def delete_notification(self, notification_id: str) -> bool:
        notification_db = self.session.get(NotificationDB, notification_id)
        if notification_db:
            self.session.delete(notification_db)
            self.session.commit()
            return True
        return False

    def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications for a user."""
        query = (
            select(func.count())
            .select_from(NotificationDB)
            .where(
                and_(
                    NotificationDB.user_id == user_id,
                    NotificationDB.status == NotificationStatus.UNREAD.value,
                )
            )
        )
        return self.session.exec(query).one()

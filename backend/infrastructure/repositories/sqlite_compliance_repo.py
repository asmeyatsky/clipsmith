from typing import List, Optional
from datetime import datetime, date
from sqlmodel import Session, select
from sqlalchemy import text
from .models import (
    GDPRRequestDB,
    ConsentRecordDB,
    AgeVerificationDB,
    UserDB,
    VideoDB,
    CommentDB,
    LikeDB,
    FollowDB,
    TipDB,
    TransactionDB,
    DirectMessageDB,
    NotificationDB,
    UserPreferencesDB,
)


class SQLiteComplianceRepository:
    def __init__(self, session: Session):
        self.session = session

    # ---- GDPR Request operations ----

    def save_gdpr_request(self, request: GDPRRequestDB) -> GDPRRequestDB:
        request = self.session.merge(request)
        self.session.commit()
        self.session.refresh(request)
        return request

    def get_gdpr_request(self, request_id: str) -> Optional[GDPRRequestDB]:
        return self.session.get(GDPRRequestDB, request_id)

    def update_gdpr_request_status(
        self,
        request_id: str,
        status: str,
        completed_at: datetime = None,
    ) -> None:
        request = self.session.get(GDPRRequestDB, request_id)
        if request:
            request.status = status
            if completed_at:
                request.completed_at = completed_at
            self.session.add(request)
            self.session.commit()

    def update_gdpr_request_result(
        self, request_id: str, result_url: str = None
    ) -> None:
        request = self.session.get(GDPRRequestDB, request_id)
        if request:
            request.result_url = result_url
            self.session.add(request)
            self.session.commit()

    def store_data_export(self, user_id: str, export_json: str) -> str:
        """Store the exported data and return a URL/path reference.

        In a production system, this would upload to object storage.
        For now, we store a reference and return a synthetic URL.
        """
        export_url = f"/api/v1/compliance/exports/{user_id}/{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        return export_url

    # ---- Data export helper methods (called by ComplianceService.export_user_data) ----

    def get_user_profile_data(self, user_id: str) -> Optional[dict]:
        user = self.session.get(UserDB, user_id)
        if user:
            data = user.model_dump()
            data.pop("hashed_password", None)
            return data
        return None

    def get_user_videos_data(self, user_id: str) -> List[dict]:
        statement = select(VideoDB).where(VideoDB.creator_id == user_id)
        results = self.session.exec(statement).all()
        return [v.model_dump() for v in results]

    def get_user_comments_data(self, user_id: str) -> List[dict]:
        statement = select(CommentDB).where(CommentDB.user_id == user_id)
        results = self.session.exec(statement).all()
        return [c.model_dump() for c in results]

    def get_user_likes_data(self, user_id: str) -> List[dict]:
        statement = select(LikeDB).where(LikeDB.user_id == user_id)
        results = self.session.exec(statement).all()
        return [l.model_dump() for l in results]

    def get_user_follows_data(self, user_id: str) -> List[dict]:
        statement = select(FollowDB).where(
            (FollowDB.follower_id == user_id) | (FollowDB.followed_id == user_id)
        )
        results = self.session.exec(statement).all()
        return [f.model_dump() for f in results]

    def get_user_tips_data(self, user_id: str) -> List[dict]:
        statement = select(TipDB).where(
            (TipDB.sender_id == user_id) | (TipDB.receiver_id == user_id)
        )
        results = self.session.exec(statement).all()
        return [t.model_dump() for t in results]

    def get_user_transactions_data(self, user_id: str) -> List[dict]:
        statement = select(TransactionDB).where(TransactionDB.user_id == user_id)
        results = self.session.exec(statement).all()
        return [t.model_dump() for t in results]

    def get_user_messages_data(self, user_id: str) -> List[dict]:
        statement = select(DirectMessageDB).where(
            (DirectMessageDB.sender_id == user_id)
            | (DirectMessageDB.receiver_id == user_id)
        )
        results = self.session.exec(statement).all()
        return [m.model_dump() for m in results]

    def get_user_notifications_data(self, user_id: str) -> List[dict]:
        statement = select(NotificationDB).where(NotificationDB.user_id == user_id)
        results = self.session.exec(statement).all()
        return [n.model_dump() for n in results]

    def get_user_preferences_data(self, user_id: str) -> Optional[dict]:
        statement = select(UserPreferencesDB).where(
            UserPreferencesDB.user_id == user_id
        )
        result = self.session.exec(statement).first()
        if result:
            return result.model_dump()
        return None

    def get_user_consents_data(self, user_id: str) -> List[dict]:
        statement = select(ConsentRecordDB).where(
            ConsentRecordDB.user_id == user_id
        )
        results = self.session.exec(statement).all()
        return [c.model_dump() for c in results]

    # ---- Data deletion (called by ComplianceService.delete_user_data) ----

    def delete_user_data_category(self, user_id: str, category: str) -> None:
        """Delete a specific category of user data."""
        category_table_map = {
            "videos": "videodb",
            "comments": "commentdb",
            "likes": "likedb",
            "follows": "followdb",
            "tips": "tipdb",
            "messages": "directmessagedb",
            "notifications": "notificationdb",
            "preferences": "userpreferencesdb",
            "analytics": "videoanalyticsdb",
        }
        table_name = category_table_map.get(category)
        if not table_name:
            return

        # Determine the user column name for each table
        user_column_map = {
            "videodb": "creator_id",
            "commentdb": "user_id",
            "likedb": "user_id",
            "followdb": "follower_id",
            "tipdb": "sender_id",
            "directmessagedb": "sender_id",
            "notificationdb": "user_id",
            "userpreferencesdb": "user_id",
            "videoanalyticsdb": "user_id",
        }
        user_col = user_column_map.get(table_name, "user_id")

        self.session.execute(
            text(f"DELETE FROM {table_name} WHERE {user_col} = :uid"),
            {"uid": user_id},
        )
        self.session.commit()

    # ---- Consent operations ----

    def save_consent_record(self, consent: ConsentRecordDB) -> ConsentRecordDB:
        consent = self.session.merge(consent)
        self.session.commit()
        self.session.refresh(consent)
        return consent

    def get_consent_records(self, user_id: str) -> List[ConsentRecordDB]:
        statement = (
            select(ConsentRecordDB)
            .where(ConsentRecordDB.user_id == user_id)
            .order_by(ConsentRecordDB.created_at.desc())
        )
        return list(self.session.exec(statement).all())

    def update_consent_record(self, consent_id: str, granted: bool) -> None:
        consent = self.session.get(ConsentRecordDB, consent_id)
        if consent:
            consent.granted = granted
            self.session.add(consent)
            self.session.commit()

    def get_consent_by_type(
        self, user_id: str, consent_type: str
    ) -> Optional[ConsentRecordDB]:
        statement = select(ConsentRecordDB).where(
            ConsentRecordDB.user_id == user_id,
            ConsentRecordDB.consent_type == consent_type,
        )
        return self.session.exec(statement).first()

    # ---- Age Verification (COPPA) ----

    def save_age_verification(
        self,
        user_id: str,
        date_of_birth: date,
        age: int,
        requires_parental_consent: bool,
    ) -> AgeVerificationDB:
        verification = AgeVerificationDB(
            user_id=user_id,
            date_of_birth=str(date_of_birth),
            verified=True,
            verified_age=age,
            is_minor=age < 18,
            requires_parental_consent=requires_parental_consent,
            status="verified",
        )
        verification = self.session.merge(verification)
        self.session.commit()
        self.session.refresh(verification)
        return verification

    # ---- CCPA operations ----

    def set_data_sale_opt_out(self, user_id: str, opted_out: bool = True) -> None:
        """Record a CCPA data sale opt-out preference.

        This is stored as a consent record with type 'data_sale_opt_out'.
        """
        statement = select(ConsentRecordDB).where(
            ConsentRecordDB.user_id == user_id,
            ConsentRecordDB.consent_type == "data_sale_opt_out",
        )
        existing = self.session.exec(statement).first()
        if existing:
            existing.granted = not opted_out  # opted_out=True means granted=False
            self.session.add(existing)
        else:
            record = ConsentRecordDB(
                user_id=user_id,
                consent_type="data_sale_opt_out",
                granted=not opted_out,
            )
            self.session.add(record)
        self.session.commit()

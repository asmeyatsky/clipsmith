from typing import List, Optional
from datetime import datetime
from sqlmodel import Session, select
from sqlalchemy import text
from .models import (
    DuetDB,
    CollaborativeVideoDB,
    VideoCollaboratorDB,
    LiveStreamDB,
    LiveStreamGuestDB,
    WatchPartyDB,
    WatchPartyParticipantDB,
    DirectMessageDB,
    ConversationDB,
)


class SQLiteSocialRepository:
    def __init__(self, session: Session):
        self.session = session

    # ---- Duet operations ----

    def save_duet(self, duet: DuetDB) -> DuetDB:
        duet = self.session.merge(duet)
        self.session.commit()
        self.session.refresh(duet)
        return duet

    def get_duet(self, duet_id: str) -> Optional[DuetDB]:
        return self.session.get(DuetDB, duet_id)

    def get_duets_by_video(self, video_id: str) -> List[DuetDB]:
        statement = (
            select(DuetDB)
            .where(DuetDB.original_video_id == video_id)
            .order_by(DuetDB.created_at.desc())
        )
        return list(self.session.exec(statement).all())

    def get_duets_by_creator(self, creator_id: str) -> List[DuetDB]:
        statement = (
            select(DuetDB)
            .where(DuetDB.creator_id == creator_id)
            .order_by(DuetDB.created_at.desc())
        )
        return list(self.session.exec(statement).all())

    def delete_duet(self, duet_id: str) -> bool:
        duet = self.session.get(DuetDB, duet_id)
        if duet:
            self.session.delete(duet)
            self.session.commit()
            return True
        return False

    # ---- Collaborative Video operations ----

    def save_collaborative_video(
        self, collab: CollaborativeVideoDB
    ) -> CollaborativeVideoDB:
        collab = self.session.merge(collab)
        self.session.commit()
        self.session.refresh(collab)
        return collab

    def get_collaborative_video(
        self, collab_id: str
    ) -> Optional[CollaborativeVideoDB]:
        return self.session.get(CollaborativeVideoDB, collab_id)

    def get_video_collaborators(
        self, collaborative_video_id: str
    ) -> List[VideoCollaboratorDB]:
        statement = select(VideoCollaboratorDB).where(
            VideoCollaboratorDB.collaborative_video_id == collaborative_video_id
        )
        return list(self.session.exec(statement).all())

    def save_video_collaborator(
        self, collaborator: VideoCollaboratorDB
    ) -> VideoCollaboratorDB:
        collaborator = self.session.merge(collaborator)
        self.session.commit()
        self.session.refresh(collaborator)
        return collaborator

    def remove_video_collaborator(
        self, collaborative_video_id: str, user_id: str
    ) -> bool:
        statement = select(VideoCollaboratorDB).where(
            VideoCollaboratorDB.collaborative_video_id == collaborative_video_id,
            VideoCollaboratorDB.user_id == user_id,
        )
        collaborator = self.session.exec(statement).first()
        if collaborator:
            self.session.delete(collaborator)
            self.session.commit()
            return True
        return False

    # ---- Live Stream operations ----

    def save_live_stream(self, stream: LiveStreamDB) -> LiveStreamDB:
        stream = self.session.merge(stream)
        self.session.commit()
        self.session.refresh(stream)
        return stream

    def get_live_stream(self, stream_id: str) -> Optional[LiveStreamDB]:
        return self.session.get(LiveStreamDB, stream_id)

    def get_active_live_streams(self, limit: int = 20) -> List[LiveStreamDB]:
        statement = (
            select(LiveStreamDB)
            .where(LiveStreamDB.status == "live")
            .order_by(LiveStreamDB.started_at.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def update_live_stream_status(
        self,
        stream_id: str,
        status: str,
        ended_at: datetime = None,
    ) -> None:
        stream = self.session.get(LiveStreamDB, stream_id)
        if stream:
            stream.status = status
            if ended_at:
                stream.ended_at = ended_at
            self.session.add(stream)
            self.session.commit()

    def save_live_stream_guest(self, guest: LiveStreamGuestDB) -> LiveStreamGuestDB:
        guest = self.session.merge(guest)
        self.session.commit()
        self.session.refresh(guest)
        return guest

    def get_live_stream_guests(self, stream_id: str) -> List[LiveStreamGuestDB]:
        statement = select(LiveStreamGuestDB).where(
            LiveStreamGuestDB.stream_id == stream_id
        )
        return list(self.session.exec(statement).all())

    # ---- Watch Party operations ----

    def save_watch_party(self, party: WatchPartyDB) -> WatchPartyDB:
        party = self.session.merge(party)
        self.session.commit()
        self.session.refresh(party)
        return party

    def get_watch_party(self, party_id: str) -> Optional[WatchPartyDB]:
        return self.session.get(WatchPartyDB, party_id)

    def get_active_watch_parties(self, limit: int = 20) -> List[WatchPartyDB]:
        statement = (
            select(WatchPartyDB)
            .where(WatchPartyDB.status.in_(["waiting", "playing"]))
            .order_by(WatchPartyDB.created_at.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def save_watch_party_participant(
        self, participant: WatchPartyParticipantDB
    ) -> WatchPartyParticipantDB:
        participant = self.session.merge(participant)
        self.session.commit()
        self.session.refresh(participant)
        return participant

    def remove_watch_party_participant(
        self, party_id: str, user_id: str
    ) -> bool:
        statement = select(WatchPartyParticipantDB).where(
            WatchPartyParticipantDB.party_id == party_id,
            WatchPartyParticipantDB.user_id == user_id,
        )
        participant = self.session.exec(statement).first()
        if participant:
            self.session.delete(participant)
            self.session.commit()
            return True
        return False

    def increment_watch_party_participant_count(self, party_id: str) -> None:
        self.session.execute(
            text(
                "UPDATE watchpartydb SET participant_count = COALESCE(participant_count, 0) + 1 WHERE id = :pid"
            ),
            {"pid": party_id},
        )
        self.session.commit()

    # ---- Direct Message operations ----

    def save_direct_message(self, message: DirectMessageDB) -> DirectMessageDB:
        message = self.session.merge(message)
        self.session.commit()
        self.session.refresh(message)
        return message

    def get_conversation(
        self, sender_id: str, receiver_id: str
    ) -> Optional[ConversationDB]:
        statement = select(ConversationDB).where(
            (
                (ConversationDB.participant_1_id == sender_id)
                & (ConversationDB.participant_2_id == receiver_id)
            )
            | (
                (ConversationDB.participant_1_id == receiver_id)
                & (ConversationDB.participant_2_id == sender_id)
            )
        )
        return self.session.exec(statement).first()

    def update_conversation_last_message(
        self, conversation_id: str, last_message_at: datetime
    ) -> None:
        conversation = self.session.get(ConversationDB, conversation_id)
        if conversation:
            conversation.last_message_at = last_message_at
            self.session.add(conversation)
            self.session.commit()

    def save_conversation(self, conversation: ConversationDB) -> ConversationDB:
        conversation = self.session.merge(conversation)
        self.session.commit()
        self.session.refresh(conversation)
        return conversation

    def get_conversation_by_id(
        self, conversation_id: str
    ) -> Optional[ConversationDB]:
        return self.session.get(ConversationDB, conversation_id)

    def get_user_conversations(self, user_id: str) -> List[ConversationDB]:
        statement = (
            select(ConversationDB)
            .where(
                (ConversationDB.participant_1_id == user_id)
                | (ConversationDB.participant_2_id == user_id)
            )
            .order_by(ConversationDB.last_message_at.desc())
        )
        return list(self.session.exec(statement).all())

    def get_conversation_messages(
        self, conversation_id: str, limit: int = 50
    ) -> List[DirectMessageDB]:
        statement = (
            select(DirectMessageDB)
            .where(DirectMessageDB.conversation_id == conversation_id)
            .order_by(DirectMessageDB.created_at.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def mark_messages_as_read(
        self, conversation_id: str, user_id: str
    ) -> None:
        """Mark all messages in a conversation as read for a specific user."""
        self.session.execute(
            text(
                "UPDATE directmessagedb SET read_at = :now "
                "WHERE conversation_id = :cid AND receiver_id = :uid AND read_at IS NULL"
            ),
            {"now": datetime.utcnow(), "cid": conversation_id, "uid": user_id},
        )
        self.session.commit()

from typing import List, Optional
from sqlmodel import Session, select
from sqlalchemy import text
from .models import (
    CircleDB,
    CircleMemberDB,
    CommunityGroupDB,
    CommunityMemberDB,
    DiscussionPostDB,
    EventDB,
    EventAttendeeDB,
)


class SQLiteCommunityRepository:
    def __init__(self, session: Session):
        self.session = session

    # ---- Circle operations ----

    def save_circle(self, circle: CircleDB) -> CircleDB:
        circle = self.session.merge(circle)
        self.session.commit()
        self.session.refresh(circle)
        return circle

    def get_circle(self, circle_id: str) -> Optional[CircleDB]:
        return self.session.get(CircleDB, circle_id)

    def get_circles_by_user(self, user_id: str) -> List[CircleDB]:
        statement = (
            select(CircleDB)
            .where(CircleDB.user_id == user_id)
            .order_by(CircleDB.created_at.desc())
        )
        return list(self.session.exec(statement).all())

    def delete_circle(self, circle_id: str) -> bool:
        circle = self.session.get(CircleDB, circle_id)
        if circle:
            self.session.delete(circle)
            self.session.commit()
            return True
        return False

    def add_circle_member(self, circle_id: str, member_id: str) -> CircleMemberDB:
        member = CircleMemberDB(circle_id=circle_id, member_id=member_id)
        self.session.add(member)
        self.session.commit()
        self.session.refresh(member)
        return member

    def remove_circle_member(self, circle_id: str, member_id: str) -> bool:
        statement = select(CircleMemberDB).where(
            CircleMemberDB.circle_id == circle_id,
            CircleMemberDB.member_id == member_id,
        )
        member = self.session.exec(statement).first()
        if member:
            self.session.delete(member)
            self.session.commit()
            return True
        return False

    def get_circle_members(self, circle_id: str) -> List[CircleMemberDB]:
        statement = select(CircleMemberDB).where(
            CircleMemberDB.circle_id == circle_id
        )
        return list(self.session.exec(statement).all())

    # ---- Community Group operations ----

    def save_group(self, group: CommunityGroupDB) -> CommunityGroupDB:
        group = self.session.merge(group)
        self.session.commit()
        self.session.refresh(group)
        return group

    def get_group(self, group_id: str) -> Optional[CommunityGroupDB]:
        return self.session.get(CommunityGroupDB, group_id)

    def list_public_groups(
        self, limit: int = 20, offset: int = 0
    ) -> List[CommunityGroupDB]:
        statement = (
            select(CommunityGroupDB)
            .where(CommunityGroupDB.is_public == True)
            .order_by(CommunityGroupDB.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def add_group_member(
        self, group_id: str, user_id: str, role: str = "member"
    ) -> CommunityMemberDB:
        member = CommunityMemberDB(group_id=group_id, user_id=user_id, role=role)
        self.session.add(member)
        self.session.commit()
        self.session.refresh(member)
        return member

    def remove_group_member(self, group_id: str, user_id: str) -> bool:
        statement = select(CommunityMemberDB).where(
            CommunityMemberDB.group_id == group_id,
            CommunityMemberDB.user_id == user_id,
        )
        member = self.session.exec(statement).first()
        if member:
            self.session.delete(member)
            self.session.commit()
            return True
        return False

    def get_group_member(
        self, group_id: str, user_id: str
    ) -> Optional[CommunityMemberDB]:
        statement = select(CommunityMemberDB).where(
            CommunityMemberDB.group_id == group_id,
            CommunityMemberDB.user_id == user_id,
        )
        return self.session.exec(statement).first()

    def get_group_members(self, group_id: str) -> List[CommunityMemberDB]:
        statement = select(CommunityMemberDB).where(
            CommunityMemberDB.group_id == group_id
        )
        return list(self.session.exec(statement).all())

    def increment_group_member_count(self, group_id: str) -> None:
        self.session.execute(
            text(
                "UPDATE communitygroupdb SET member_count = COALESCE(member_count, 0) + 1 WHERE id = :gid"
            ),
            {"gid": group_id},
        )
        self.session.commit()

    def decrement_group_member_count(self, group_id: str) -> None:
        self.session.execute(
            text(
                "UPDATE communitygroupdb SET member_count = MAX(COALESCE(member_count, 0) - 1, 0) WHERE id = :gid"
            ),
            {"gid": group_id},
        )
        self.session.commit()

    def get_user_groups(self, user_id: str) -> List[CommunityGroupDB]:
        statement = select(CommunityMemberDB).where(
            CommunityMemberDB.user_id == user_id
        )
        memberships = self.session.exec(statement).all()
        group_ids = [m.group_id for m in memberships]
        if not group_ids:
            return []
        statement = select(CommunityGroupDB).where(
            CommunityGroupDB.id.in_(group_ids)
        )
        return list(self.session.exec(statement).all())

    # ---- Discussion Post operations ----

    def save_discussion_post(self, post: DiscussionPostDB) -> DiscussionPostDB:
        post = self.session.merge(post)
        self.session.commit()
        self.session.refresh(post)
        return post

    def get_discussion_post(self, post_id: str) -> Optional[DiscussionPostDB]:
        return self.session.get(DiscussionPostDB, post_id)

    def get_discussion_posts(
        self, group_id: str, limit: int = 20, offset: int = 0
    ) -> List[DiscussionPostDB]:
        statement = (
            select(DiscussionPostDB)
            .where(DiscussionPostDB.group_id == group_id)
            .order_by(DiscussionPostDB.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    # ---- Event operations ----

    def save_event(self, event: EventDB) -> EventDB:
        event = self.session.merge(event)
        self.session.commit()
        self.session.refresh(event)
        return event

    def get_event(self, event_id: str) -> Optional[EventDB]:
        return self.session.get(EventDB, event_id)

    def get_events_by_group(self, group_id: str, limit: int = 20) -> List[EventDB]:
        statement = (
            select(EventDB)
            .where(EventDB.group_id == group_id)
            .order_by(EventDB.start_time.asc())
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def get_upcoming_events(self, limit: int = 20) -> List[EventDB]:
        statement = (
            select(EventDB)
            .where(EventDB.status == "upcoming")
            .order_by(EventDB.start_time.asc())
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def upsert_event_attendee(
        self, event_id: str, user_id: str, rsvp_status: str = "going"
    ) -> EventAttendeeDB:
        statement = select(EventAttendeeDB).where(
            EventAttendeeDB.event_id == event_id,
            EventAttendeeDB.user_id == user_id,
        )
        existing = self.session.exec(statement).first()
        if existing:
            existing.rsvp_status = rsvp_status
            self.session.add(existing)
            self.session.commit()
            self.session.refresh(existing)
            return existing
        attendee = EventAttendeeDB(
            event_id=event_id, user_id=user_id, rsvp_status=rsvp_status
        )
        self.session.add(attendee)
        self.session.commit()
        self.session.refresh(attendee)
        return attendee

    def increment_event_attendee_count(self, event_id: str) -> None:
        self.session.execute(
            text(
                "UPDATE eventdb SET attendee_count = COALESCE(attendee_count, 0) + 1 WHERE id = :eid"
            ),
            {"eid": event_id},
        )
        self.session.commit()

    def get_event_attendees(self, event_id: str) -> List[EventAttendeeDB]:
        statement = select(EventAttendeeDB).where(
            EventAttendeeDB.event_id == event_id
        )
        return list(self.session.exec(statement).all())

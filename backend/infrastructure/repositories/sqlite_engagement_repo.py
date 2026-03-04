from typing import List, Optional
from sqlmodel import Session, select
from sqlalchemy import text
from .models import (
    PollDB,
    PollOptionDB,
    PollVoteDB,
    ChapterMarkerDB,
    ProductTagDB,
    VideoLinkDB,
    ChallengeDB,
    ChallengeParticipantDB,
    BadgeDB,
    UserBadgeDB,
)


class SQLiteEngagementRepository:
    def __init__(self, session: Session):
        self.session = session

    # ---- Poll operations ----

    def save_poll(self, poll: PollDB) -> PollDB:
        poll = self.session.merge(poll)
        self.session.commit()
        self.session.refresh(poll)
        return poll

    def get_poll(self, poll_id: str) -> Optional[PollDB]:
        return self.session.get(PollDB, poll_id)

    def get_polls_by_video(self, video_id: str) -> List[PollDB]:
        statement = (
            select(PollDB)
            .where(PollDB.video_id == video_id)
            .order_by(PollDB.start_time.asc())
        )
        return list(self.session.exec(statement).all())

    def save_poll_option(self, option: PollOptionDB) -> PollOptionDB:
        option = self.session.merge(option)
        self.session.commit()
        self.session.refresh(option)
        return option

    def get_poll_options(self, poll_id: str) -> List[PollOptionDB]:
        statement = select(PollOptionDB).where(PollOptionDB.poll_id == poll_id)
        return list(self.session.exec(statement).all())

    def save_poll_vote(self, vote: PollVoteDB) -> PollVoteDB:
        vote = self.session.merge(vote)
        self.session.commit()
        self.session.refresh(vote)
        return vote

    def get_poll_vote(self, poll_id: str, user_id: str) -> Optional[PollVoteDB]:
        statement = select(PollVoteDB).where(
            PollVoteDB.poll_id == poll_id,
            PollVoteDB.user_id == user_id,
        )
        return self.session.exec(statement).first()

    def has_user_voted(self, poll_id: str, user_id: str) -> bool:
        return self.get_poll_vote(poll_id, user_id) is not None

    def increment_poll_option_vote_count(self, option_id: str) -> None:
        self.session.execute(
            text(
                "UPDATE polloptiondb SET vote_count = COALESCE(vote_count, 0) + 1 WHERE id = :oid"
            ),
            {"oid": option_id},
        )
        self.session.commit()

    def increment_poll_total_votes(self, poll_id: str) -> None:
        self.session.execute(
            text(
                "UPDATE polldb SET total_votes = COALESCE(total_votes, 0) + 1 WHERE id = :pid"
            ),
            {"pid": poll_id},
        )
        self.session.commit()

    # ---- Chapter Marker operations ----

    def save_chapter_marker(self, marker: ChapterMarkerDB) -> ChapterMarkerDB:
        marker = self.session.merge(marker)
        self.session.commit()
        self.session.refresh(marker)
        return marker

    def get_chapter_markers_by_video(self, video_id: str) -> List[ChapterMarkerDB]:
        statement = (
            select(ChapterMarkerDB)
            .where(ChapterMarkerDB.video_id == video_id)
            .order_by(ChapterMarkerDB.start_time.asc())
        )
        return list(self.session.exec(statement).all())

    def delete_chapter_marker(self, marker_id: str) -> bool:
        marker = self.session.get(ChapterMarkerDB, marker_id)
        if marker:
            self.session.delete(marker)
            self.session.commit()
            return True
        return False

    # ---- Product Tag operations ----

    def save_product_tag(self, tag: ProductTagDB) -> ProductTagDB:
        tag = self.session.merge(tag)
        self.session.commit()
        self.session.refresh(tag)
        return tag

    def get_product_tags_by_video(self, video_id: str) -> List[ProductTagDB]:
        statement = (
            select(ProductTagDB)
            .where(ProductTagDB.video_id == video_id)
            .order_by(ProductTagDB.start_time.asc())
        )
        return list(self.session.exec(statement).all())

    def delete_product_tag(self, tag_id: str) -> bool:
        tag = self.session.get(ProductTagDB, tag_id)
        if tag:
            self.session.delete(tag)
            self.session.commit()
            return True
        return False

    def increment_product_tag_click_count(self, tag_id: str) -> None:
        self.session.execute(
            text(
                "UPDATE producttagdb SET click_count = COALESCE(click_count, 0) + 1 WHERE id = :tid"
            ),
            {"tid": tag_id},
        )
        self.session.commit()

    # ---- Video Link operations ----

    def save_video_link(self, link: VideoLinkDB) -> VideoLinkDB:
        link = self.session.merge(link)
        self.session.commit()
        self.session.refresh(link)
        return link

    def get_video_links_by_video(self, video_id: str) -> List[VideoLinkDB]:
        statement = (
            select(VideoLinkDB)
            .where(VideoLinkDB.video_id == video_id)
            .order_by(VideoLinkDB.position.asc())
        )
        return list(self.session.exec(statement).all())

    def delete_video_link(self, link_id: str) -> bool:
        link = self.session.get(VideoLinkDB, link_id)
        if link:
            self.session.delete(link)
            self.session.commit()
            return True
        return False

    def increment_video_link_click_count(self, link_id: str) -> None:
        self.session.execute(
            text(
                "UPDATE videolinkdb SET click_count = COALESCE(click_count, 0) + 1 WHERE id = :lid"
            ),
            {"lid": link_id},
        )
        self.session.commit()

    # ---- Challenge operations ----

    def save_challenge(self, challenge: ChallengeDB) -> ChallengeDB:
        challenge = self.session.merge(challenge)
        self.session.commit()
        self.session.refresh(challenge)
        return challenge

    def get_challenge(self, challenge_id: str) -> Optional[ChallengeDB]:
        return self.session.get(ChallengeDB, challenge_id)

    def get_active_challenges(self, limit: int = 20) -> List[ChallengeDB]:
        statement = (
            select(ChallengeDB)
            .where(ChallengeDB.status == "active")
            .order_by(ChallengeDB.created_at.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def save_challenge_participant(
        self, participant: ChallengeParticipantDB
    ) -> ChallengeParticipantDB:
        participant = self.session.merge(participant)
        self.session.commit()
        self.session.refresh(participant)
        return participant

    def increment_challenge_participant_count(self, challenge_id: str) -> None:
        self.session.execute(
            text(
                "UPDATE challengedb SET participant_count = COALESCE(participant_count, 0) + 1 WHERE id = :cid"
            ),
            {"cid": challenge_id},
        )
        self.session.commit()

    def get_challenge_participants(
        self, challenge_id: str
    ) -> List[ChallengeParticipantDB]:
        statement = select(ChallengeParticipantDB).where(
            ChallengeParticipantDB.challenge_id == challenge_id
        )
        return list(self.session.exec(statement).all())

    # ---- Badge operations ----

    def save_badge(self, badge: BadgeDB) -> BadgeDB:
        badge = self.session.merge(badge)
        self.session.commit()
        self.session.refresh(badge)
        return badge

    def get_badge_by_id(self, badge_id: str) -> Optional[BadgeDB]:
        return self.session.get(BadgeDB, badge_id)

    def get_all_badges(self) -> List[BadgeDB]:
        statement = select(BadgeDB)
        return list(self.session.exec(statement).all())

    def save_user_badge(self, user_badge: UserBadgeDB) -> UserBadgeDB:
        user_badge = self.session.merge(user_badge)
        self.session.commit()
        self.session.refresh(user_badge)
        return user_badge

    def get_user_badge(self, user_id: str, badge_id: str) -> Optional[UserBadgeDB]:
        statement = select(UserBadgeDB).where(
            UserBadgeDB.user_id == user_id,
            UserBadgeDB.badge_id == badge_id,
        )
        return self.session.exec(statement).first()

    def get_user_badges(self, user_id: str) -> List[UserBadgeDB]:
        statement = select(UserBadgeDB).where(UserBadgeDB.user_id == user_id)
        return list(self.session.exec(statement).all())

    def get_badge_by_type(self, badge_type: str) -> Optional[BadgeDB]:
        statement = select(BadgeDB).where(BadgeDB.badge_type == badge_type)
        return self.session.exec(statement).first()

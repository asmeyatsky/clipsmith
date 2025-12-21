from typing import List, Optional
from sqlmodel import Session, select
from ...domain.entities.follow import Follow
from ...domain.ports.repository_ports import FollowRepositoryPort
from .models import FollowDB

class SQLiteFollowRepository(FollowRepositoryPort):
    def __init__(self, session: Session):
        self.session = session

    def follow(self, follower_id: str, followed_id: str) -> Follow:
        follow_db = FollowDB(follower_id=follower_id, followed_id=followed_id)
        self.session.add(follow_db)
        self.session.commit()
        self.session.refresh(follow_db)
        return Follow(**follow_db.model_dump())

    def unfollow(self, follower_id: str, followed_id: str) -> bool:
        statement = select(FollowDB).where(
            FollowDB.follower_id == follower_id,
            FollowDB.followed_id == followed_id
        )
        follow_db = self.session.exec(statement).first()
        if follow_db:
            self.session.delete(follow_db)
            self.session.commit()
            return True
        return False

    def is_following(self, follower_id: str, followed_id: str) -> bool:
        statement = select(FollowDB).where(
            FollowDB.follower_id == follower_id,
            FollowDB.followed_id == followed_id
        )
        follow_db = self.session.exec(statement).first()
        return follow_db is not None

    def get_followers(self, user_id: str) -> List[Follow]:
        statement = select(FollowDB).where(FollowDB.followed_id == user_id).order_by(FollowDB.created_at.desc())
        results = self.session.exec(statement).all()
        return [Follow(**f.model_dump()) for f in results]

    def get_following(self, user_id: str) -> List[Follow]:
        statement = select(FollowDB).where(FollowDB.follower_id == user_id).order_by(FollowDB.created_at.desc())
        results = self.session.exec(statement).all()
        return [Follow(**f.model_dump()) for f in results]

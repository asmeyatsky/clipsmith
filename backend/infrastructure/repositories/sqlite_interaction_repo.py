from typing import List, Optional
from sqlmodel import Session, select, col
from .database import engine # Keep for now
from .models import LikeDB, CommentDB, VideoDB
from datetime import datetime

class SQLiteInteractionRepository:
    def __init__(self, session: Session):
        self.session = session

    # LIKES
    def toggle_like(self, user_id: str, video_id: str) -> bool:
        """
        Toggles like. Returns True if liked, False if unliked.
        Updates VideoDB.likes count.
        """
        # Check existing like
        statement = select(LikeDB).where(
            LikeDB.user_id == user_id, 
            LikeDB.video_id == video_id
        )
        existing_like = self.session.exec(statement).first()

        video = self.session.get(VideoDB, video_id)
        if not video:
            return False # Or raise error

        if existing_like:
            # Unlike
            self.session.delete(existing_like)
            video.likes = max(0, video.likes - 1)
            is_liked = False
        else:
            # Like
            new_like = LikeDB(user_id=user_id, video_id=video_id)
            self.session.add(new_like)
            video.likes += 1
            is_liked = True
        
        self.session.add(video)
        self.session.commit()
        return is_liked

    def has_user_liked(self, user_id: str, video_id: str) -> bool:
        statement = select(LikeDB).where(
            LikeDB.user_id == user_id, 
            LikeDB.video_id == video_id
        )
        return self.session.exec(statement).first() is not None

    # COMMENTS
    def add_comment(self, user_id: str, username: str, video_id: str, content: str) -> CommentDB:
        comment = CommentDB(
            user_id=user_id,
            video_id=video_id,
            username=username,
            content=content
        )
        self.session.add(comment)
        self.session.commit()
        self.session.refresh(comment)
        return comment

    def list_comments(self, video_id: str) -> List[CommentDB]:
        statement = select(CommentDB).where(CommentDB.video_id == video_id).order_by(col(CommentDB.created_at).desc())
        return list(self.session.exec(statement).all())

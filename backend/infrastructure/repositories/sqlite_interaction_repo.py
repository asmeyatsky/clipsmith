from typing import List, Optional
from sqlmodel import Session, select, col
from .database import engine
from .models import LikeDB, CommentDB, VideoDB
from datetime import datetime

class SQLiteInteractionRepository:
    # LIKES
    async def toggle_like(self, user_id: str, video_id: str) -> bool:
        """
        Toggles like. Returns True if liked, False if unliked.
        Updates VideoDB.likes count.
        """
        with Session(engine) as session:
            # Check existing like
            statement = select(LikeDB).where(
                LikeDB.user_id == user_id, 
                LikeDB.video_id == video_id
            )
            existing_like = session.exec(statement).first()

            video = session.get(VideoDB, video_id)
            if not video:
                return False # Or raise error

            if existing_like:
                # Unlike
                session.delete(existing_like)
                video.likes = max(0, video.likes - 1)
                is_liked = False
            else:
                # Like
                new_like = LikeDB(user_id=user_id, video_id=video_id)
                session.add(new_like)
                video.likes += 1
                is_liked = True
            
            session.add(video)
            session.commit()
            return is_liked

    async def has_user_liked(self, user_id: str, video_id: str) -> bool:
        with Session(engine) as session:
            statement = select(LikeDB).where(
                LikeDB.user_id == user_id, 
                LikeDB.video_id == video_id
            )
            return session.exec(statement).first() is not None

    # COMMENTS
    async def add_comment(self, user_id: str, username: str, video_id: str, content: str) -> CommentDB:
        with Session(engine) as session:
            comment = CommentDB(
                user_id=user_id,
                video_id=video_id,
                username=username,
                content=content
            )
            session.add(comment)
            session.commit()
            session.refresh(comment)
            return comment

    async def list_comments(self, video_id: str) -> List[CommentDB]:
        with Session(engine) as session:
            statement = select(CommentDB).where(CommentDB.video_id == video_id).order_by(col(CommentDB.created_at).desc())
            return list(session.exec(statement).all())

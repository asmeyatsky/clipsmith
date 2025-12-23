import pytest
from backend.infrastructure.repositories.models import UserDB, VideoDB
import uuid


class TestInteractionRepository:
    def _create_user(self, session, username="testuser"):
        user = UserDB(
            id=str(uuid.uuid4()),
            username=username,
            email=f"{username}@example.com",
            hashed_password="hashedpassword"
        )
        session.add(user)
        session.commit()
        return user

    def _create_video(self, session, creator_id, title="Test Video"):
        video = VideoDB(
            id=str(uuid.uuid4()),
            title=title,
            description="A test video",
            creator_id=creator_id,
            status="READY",
            views=0,
            likes=0,
            duration=60.0
        )
        session.add(video)
        session.commit()
        return video

    def test_toggle_like(self, session, interaction_repo):
        user = self._create_user(session)
        video = self._create_video(session, user.id)

        # Like the video
        is_liked = interaction_repo.toggle_like(user.id, video.id)
        assert is_liked is True

        # Unlike the video
        is_liked = interaction_repo.toggle_like(user.id, video.id)
        assert is_liked is False

        # Like again
        is_liked = interaction_repo.toggle_like(user.id, video.id)
        assert is_liked is True

    def test_has_user_liked(self, session, interaction_repo):
        user = self._create_user(session)
        video = self._create_video(session, user.id)

        # Initially not liked
        assert interaction_repo.has_user_liked(user.id, video.id) is False

        # Like it
        interaction_repo.toggle_like(user.id, video.id)
        assert interaction_repo.has_user_liked(user.id, video.id) is True

    def test_add_comment(self, session, interaction_repo):
        user = self._create_user(session, "commenter")
        video = self._create_video(session, user.id)

        comment = interaction_repo.add_comment(
            user_id=user.id,
            username=user.username,
            video_id=video.id,
            content="Great video!"
        )

        assert comment.content == "Great video!"
        assert comment.username == "commenter"
        assert comment.video_id == video.id

    def test_list_comments(self, session, interaction_repo):
        user = self._create_user(session, "multicommenter")
        video = self._create_video(session, user.id)

        # Add multiple comments
        for i in range(5):
            interaction_repo.add_comment(
                user_id=user.id,
                username=user.username,
                video_id=video.id,
                content=f"Comment {i}"
            )

        comments = interaction_repo.list_comments(video.id)
        assert len(comments) == 5

    def test_comments_ordered_by_time(self, session, interaction_repo):
        user = self._create_user(session, "orderuser")
        video = self._create_video(session, user.id)

        interaction_repo.add_comment(user.id, user.username, video.id, "First")
        interaction_repo.add_comment(user.id, user.username, video.id, "Second")
        interaction_repo.add_comment(user.id, user.username, video.id, "Third")

        comments = interaction_repo.list_comments(video.id)
        # Should be ordered by created_at desc (newest first)
        assert len(comments) == 3

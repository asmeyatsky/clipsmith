import pytest
from backend.infrastructure.repositories.sqlite_follow_repo import SQLiteFollowRepository
from backend.infrastructure.repositories.models import UserDB
import uuid


@pytest.fixture(name="follow_repo")
def follow_repo_fixture(session):
    return SQLiteFollowRepository(session)


class TestFollowRepository:
    def _create_user(self, session, username):
        user = UserDB(
            id=str(uuid.uuid4()),
            username=username,
            email=f"{username}@example.com",
            hashed_password="hashedpassword"
        )
        session.add(user)
        session.commit()
        return user

    def test_follow_user(self, session, follow_repo):
        user1 = self._create_user(session, "follower")
        user2 = self._create_user(session, "followed")

        follow = follow_repo.follow(user1.id, user2.id)

        assert follow.follower_id == user1.id
        assert follow.followed_id == user2.id

    def test_unfollow_user(self, session, follow_repo):
        user1 = self._create_user(session, "unfollower")
        user2 = self._create_user(session, "unfollowed")

        # Follow first
        follow_repo.follow(user1.id, user2.id)
        assert follow_repo.is_following(user1.id, user2.id) is True

        # Unfollow
        result = follow_repo.unfollow(user1.id, user2.id)
        assert result is True
        assert follow_repo.is_following(user1.id, user2.id) is False

    def test_is_following(self, session, follow_repo):
        user1 = self._create_user(session, "checkfollower")
        user2 = self._create_user(session, "checkfollowed")

        # Initially not following
        assert follow_repo.is_following(user1.id, user2.id) is False

        # Follow
        follow_repo.follow(user1.id, user2.id)
        assert follow_repo.is_following(user1.id, user2.id) is True

    def test_get_followers(self, session, follow_repo):
        popular = self._create_user(session, "popular")
        fan1 = self._create_user(session, "fan1")
        fan2 = self._create_user(session, "fan2")
        fan3 = self._create_user(session, "fan3")

        follow_repo.follow(fan1.id, popular.id)
        follow_repo.follow(fan2.id, popular.id)
        follow_repo.follow(fan3.id, popular.id)

        followers = follow_repo.get_followers(popular.id)
        assert len(followers) == 3

    def test_get_following(self, session, follow_repo):
        fan = self._create_user(session, "superfan")
        celeb1 = self._create_user(session, "celeb1")
        celeb2 = self._create_user(session, "celeb2")

        follow_repo.follow(fan.id, celeb1.id)
        follow_repo.follow(fan.id, celeb2.id)

        following = follow_repo.get_following(fan.id)
        assert len(following) == 2

from typing import Dict, Optional, List
from ...domain.entities.video import Video
from ...domain.entities.user import User
from ...domain.ports.repository_ports import VideoRepositoryPort, UserRepositoryPort

class InMemoryVideoRepository(VideoRepositoryPort):
    def __init__(self):
        self._videos: Dict[str, Video] = {}

    async def save(self, video: Video) -> Video:
        self._videos[video.id] = video
        return video

    async def get_by_id(self, video_id: str) -> Optional[Video]:
        return self._videos.get(video_id)

    async def list_by_creator(self, creator_id: str) -> List[Video]:
        return [v for v in self._videos.values() if v.creator_id == creator_id]

class InMemoryUserRepository(UserRepositoryPort):
    def __init__(self):
        self._users: Dict[str, User] = {}

    async def save(self, user: User) -> User:
        self._users[user.id] = user
        return user

    async def get_by_email(self, email: str) -> Optional[User]:
        return next((u for u in self._users.values() if u.email == email), None)

    async def get_by_id(self, user_id: str) -> Optional[User]:
        return self._users.get(user_id)

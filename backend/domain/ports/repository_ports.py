from abc import ABC, abstractmethod
from typing import Optional, List
from ..entities.video import Video
from ..entities.user import User

class VideoRepositoryPort(ABC):
    @abstractmethod
    async def save(self, video: Video) -> Video:
        pass

    @abstractmethod
    async def get_by_id(self, video_id: str) -> Optional[Video]:
        pass

    @abstractmethod
    async def find_all(self) -> List[Video]:
        pass

    @abstractmethod
    async def list_by_creator(self, creator_id: str) -> List[Video]:
        pass

class UserRepositoryPort(ABC):
    @abstractmethod
    async def save(self, user: User) -> User:
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        pass

    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[User]:
        pass

    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        pass

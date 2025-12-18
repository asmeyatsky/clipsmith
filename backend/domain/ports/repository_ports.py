from abc import ABC, abstractmethod
from typing import Optional, List
from ..entities.video import Video
from ..entities.user import User

class VideoRepositoryPort(ABC):
    @abstractmethod
    def save(self, video: Video) -> Video:
        pass

    @abstractmethod
    def get_by_id(self, video_id: str) -> Optional[Video]:
        pass

    @abstractmethod
    def find_all(self, offset: int = 0, limit: int = 20) -> List[Video]:
        pass

    @abstractmethod
    def count_all(self) -> int:
        pass

    @abstractmethod
    def list_by_creator(self, creator_id: str) -> List[Video]:
        pass

    @abstractmethod
    def delete(self, video_id: str) -> bool:
        pass

class UserRepositoryPort(ABC):
    @abstractmethod
    def save(self, user: User) -> User:
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        pass

    @abstractmethod
    def get_by_id(self, user_id: str) -> Optional[User]:
        pass

    @abstractmethod
    def get_by_username(self, username: str) -> Optional[User]:
        pass

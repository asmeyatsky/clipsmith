from abc import ABC, abstractmethod
from typing import Optional, List
from ..entities.video import Video
from ..entities.user import User
from ..entities.caption import Caption # Import Caption entity
from ..entities.tip import Tip # Import Tip entity
from ..entities.follow import Follow # Import Follow entity

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

class CaptionRepositoryPort(ABC):
    @abstractmethod
    def save(self, caption: Caption) -> Caption:
        pass

    @abstractmethod
    def get_by_video_id(self, video_id: str) -> List[Caption]:
        pass

    @abstractmethod
    def delete_by_video_id(self, video_id: str) -> bool:
        pass

class TipRepositoryPort(ABC):
    @abstractmethod
    def save(self, tip: Tip) -> Tip:
        pass

    @abstractmethod
    def get_tips_by_receiver_id(self, receiver_id: str) -> List[Tip]:
        pass

    @abstractmethod
    def get_tips_by_sender_id(self, sender_id: str) -> List[Tip]:
        pass

    @abstractmethod
    def get_tips_by_video_id(self, video_id: str) -> List[Tip]:
        pass

class FollowRepositoryPort(ABC):
    @abstractmethod
    def follow(self, follower_id: str, followed_id: str) -> Follow:
        pass

    @abstractmethod
    def unfollow(self, follower_id: str, followed_id: str) -> bool:
        pass

    @abstractmethod
    def is_following(self, follower_id: str, followed_id: str) -> bool:
        pass

    @abstractmethod
    def get_followers(self, user_id: str) -> List[Follow]:
        pass

    @abstractmethod
    def get_following(self, user_id: str) -> List[Follow]:
        pass



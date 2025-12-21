from ...domain.ports.repository_ports import UserRepositoryPort, FollowRepositoryPort
from ...domain.entities.follow import Follow
from ..dtos.follow_dto import FollowResponseDTO, FollowStatusDTO

class ManageFollowsUseCase:
    def __init__(self, user_repo: UserRepositoryPort, follow_repo: FollowRepositoryPort):
        self._user_repo = user_repo
        self._follow_repo = follow_repo

    def follow(self, follower_id: str, followed_id: str) -> FollowResponseDTO:
        if follower_id == followed_id:
            raise ValueError("Cannot follow yourself.")

        follower = self._user_repo.get_by_id(follower_id)
        if not follower:
            raise ValueError(f"Follower with ID {follower_id} not found.")

        followed = self._user_repo.get_by_id(followed_id)
        if not followed:
            raise ValueError(f"User to follow with ID {followed_id} not found.")

        if self._follow_repo.is_following(follower_id, followed_id):
            raise ValueError(f"User {follower_id} is already following {followed_id}.")

        follow = self._follow_repo.follow(follower_id, followed_id)
        return FollowResponseDTO(
            follower_id=follow.follower_id,
            followed_id=follow.followed_id,
            created_at=follow.created_at
        )

    def unfollow(self, follower_id: str, followed_id: str) -> bool:
        if follower_id == followed_id:
            raise ValueError("Cannot unfollow yourself.")

        if not self._follow_repo.is_following(follower_id, followed_id):
            raise ValueError(f"User {follower_id} is not following {followed_id}.")

        return self._follow_repo.unfollow(follower_id, followed_id)

    def get_follow_status(self, viewer_id: str, target_id: str) -> FollowStatusDTO:
        is_following = self._follow_repo.is_following(viewer_id, target_id)
        return FollowStatusDTO(is_following=is_following)

from ...domain.ports.repository_ports import UserRepositoryPort, VideoRepositoryPort
from ..dtos.profile_dto import ProfileResponseDTO, PublicProfileDTO
from ..dtos.video_dto import VideoResponseDTO

class GetUserProfileUseCase:
    def __init__(self, user_repo: UserRepositoryPort, video_repo: VideoRepositoryPort):
        self._user_repo = user_repo
        self._video_repo = video_repo

    def execute(self, username: str) -> ProfileResponseDTO:
        # Get User
        user = self._user_repo.get_by_username(username)
        if not user:
            raise ValueError(f"User {username} not found")

        # Get User's Videos
        videos = self._video_repo.list_by_creator(user.id)

        # Build DTO
        return ProfileResponseDTO(
            user=PublicProfileDTO(
                id=user.id,
                username=user.username
            ),
            videos=[
                VideoResponseDTO(
                    id=v.id,
                    title=v.title,
                    description=v.description,
                    status=v.status,
                    url=v.url,
                    thumbnail_url=v.thumbnail_url, # Add thumbnail_url
                    views=v.views,
                    likes=v.likes,
                    duration=v.duration
                ) for v in videos
            ]
        )

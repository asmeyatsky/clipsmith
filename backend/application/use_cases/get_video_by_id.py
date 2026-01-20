from ...domain.ports.repository_ports import VideoRepositoryPort
from ..dtos.video_dto import VideoResponseDTO

class GetVideoByIdUseCase:
    def __init__(self, video_repo: VideoRepositoryPort):
        self._video_repo = video_repo

    def execute(self, video_id: str) -> VideoResponseDTO | None:
        video = self._video_repo.get_by_id(video_id)
        if not video:
            return None # Or raise a specific exception

        return VideoResponseDTO(
            id=video.id,
            title=video.title,
            description=video.description,
            creator_id=video.creator_id,
            status=video.status,
            url=video.url,
            thumbnail_url=video.thumbnail_url,
            views=video.views,
            likes=video.likes,
            duration=video.duration
        )

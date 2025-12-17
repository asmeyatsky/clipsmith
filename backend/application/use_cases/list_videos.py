from typing import List
from ...domain.ports.repository_ports import VideoRepositoryPort
from ..dtos.video_dto import VideoResponseDTO

class ListVideosUseCase:
    def __init__(self, video_repo: VideoRepositoryPort):
        self._video_repo = video_repo

    async def execute(self) -> List[VideoResponseDTO]:
        videos = await self._video_repo.find_all()
        
        # Convert to DTOs
        return [
            VideoResponseDTO(
                id=v.id,
                title=v.title,
                description=v.description,
                status=v.status,
                url=v.url,
                views=v.views,
                likes=v.likes
            )
            for v in videos
        ]

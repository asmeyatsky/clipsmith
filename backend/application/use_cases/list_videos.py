from typing import List
import math
from ...domain.ports.repository_ports import VideoRepositoryPort
from ..dtos.video_dto import VideoResponseDTO, PaginatedVideoResponseDTO

class ListVideosUseCase:
    def __init__(self, video_repo: VideoRepositoryPort):
        self._video_repo = video_repo

    def execute(self, page: int = 1, page_size: int = 20) -> PaginatedVideoResponseDTO:
        # Ensure valid page and page_size
        page = max(1, page)
        page_size = min(max(1, page_size), 100)  # Cap at 100 items per page

        offset = (page - 1) * page_size
        videos = self._video_repo.find_all(offset=offset, limit=page_size)
        total = self._video_repo.count_all()
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        # Convert to DTOs
        items = [
            VideoResponseDTO(
                id=v.id,
                title=v.title,
                description=v.description,
                creator_id=v.creator_id,
                status=v.status,
                url=v.url,
                thumbnail_url=v.thumbnail_url,
                views=v.views,
                likes=v.likes,
                duration=v.duration
            )
            for v in videos
        ]

        return PaginatedVideoResponseDTO(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

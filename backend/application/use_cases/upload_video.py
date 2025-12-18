from ...domain.ports.repository_ports import VideoRepositoryPort
from ...domain.ports.storage_port import StoragePort
from ...domain.entities.video import Video, VideoStatus
from ..dtos.video_dto import VideoCreateDTO, VideoResponseDTO
from typing import BinaryIO
import uuid

from backend.infrastructure.queue import get_video_queue
from backend.application.tasks import process_video_task

class UploadVideoUseCase:
    def __init__(self, video_repo: VideoRepositoryPort, storage_adapter: StoragePort):
        self._video_repo = video_repo
        self._storage_adapter = storage_adapter
        self._video_queue = get_video_queue() # Get the video processing queue

    def execute(self, dto: VideoCreateDTO, file_data: BinaryIO, filename: str) -> VideoResponseDTO:
        # Generate unique filename to prevent collisions
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        # Save file to storage (this is the original uploaded file)
        uploaded_file_path = self._storage_adapter.save(unique_filename, file_data)
        
        # Create domain entity with UPLOADING status, URL will be set after processing
        video = Video(
            title=dto.title,
            description=dto.description,
            creator_id=dto.creator_id,
            status=VideoStatus.UPLOADING # Default status is UPLOADING
        )
        
        # Save to repo - the ID is generated here
        saved_video = self._video_repo.save(video)

        # Enqueue the video processing task
        self._video_queue.enqueue(
            process_video_task, 
            saved_video.id, 
            uploaded_file_path,
            job_timeout=3600 # 1 hour timeout for processing
        )
        
        # Return DTO, status will be UPLOADING, url will be None
        return VideoResponseDTO(
            id=saved_video.id,
            title=saved_video.title,
            description=saved_video.description,
            status=saved_video.status,
            url=None, # URL is not available yet
            thumbnail_url=None, # Thumbnail URL is not available yet
            views=saved_video.views,
            likes=saved_video.likes
        )

import pytest
from unittest.mock import MagicMock, patch
from io import BytesIO

from backend.application.use_cases.upload_video import UploadVideoUseCase
from backend.application.use_cases.get_video_by_id import GetVideoByIdUseCase
from backend.application.use_cases.list_videos import ListVideosUseCase
from backend.domain.entities.video import Video, VideoStatus
from backend.application.dtos.video_dto import VideoCreateDTO


class TestUploadVideoUseCase:
    def test_upload_video_creates_video_with_uploading_status(self, session, video_repo):
        mock_storage_adapter = MagicMock()
        mock_storage_adapter.save.return_value = "path/to/uploaded_video.mp4"

        with patch('backend.infrastructure.queue.get_video_queue') as mock_queue:
            mock_video_queue = MagicMock()
            mock_queue.return_value = mock_video_queue

            use_case = UploadVideoUseCase(video_repo, mock_storage_adapter)

            video_dto = VideoCreateDTO(
                title="Test Video",
                description="A description",
                creator_id="test_user_id"
            )
            file_data = BytesIO(b"dummy video content")
            filename = "test_video.mp4"

            response_dto = use_case.execute(video_dto, file_data, filename)

            assert response_dto.status == VideoStatus.UPLOADING
            assert response_dto.title == "Test Video"
            mock_storage_adapter.save.assert_called_once()


class TestGetVideoByIdUseCase:
    def test_get_video_by_id_returns_video(self, session, video_repo):
        # Setup: Add a video to the repo
        video_entity = Video(
            id="video_id_123",
            title="Existing Video",
            description="Desc",
            creator_id="user_id_456",
            status=VideoStatus.READY,
            url="/uploads/existing_video.mp4",
            thumbnail_url="/uploads/thumbnails/existing_video.jpg"
        )
        video_repo.save(video_entity)

        use_case = GetVideoByIdUseCase(video_repo)
        result = use_case.execute("video_id_123")

        assert result is not None
        assert result.id == "video_id_123"
        assert result.status == VideoStatus.READY
        assert result.url == "/uploads/existing_video.mp4"
        assert result.thumbnail_url == "/uploads/thumbnails/existing_video.jpg"

    def test_get_video_by_id_returns_none_for_nonexistent(self, video_repo):
        use_case = GetVideoByIdUseCase(video_repo)
        result = use_case.execute("non_existent_id")
        assert result is None


class TestListVideosUseCase:
    def test_list_videos_returns_paginated_results(self, session, video_repo):
        # Create some test videos
        for i in range(5):
            video = Video(
                id=f"video_{i}",
                title=f"Video {i}",
                description=f"Description {i}",
                creator_id="user_1",
                status=VideoStatus.READY,
                url=f"/uploads/video_{i}.mp4",
                thumbnail_url=f"/uploads/thumbnails/video_{i}.jpg"
            )
            video_repo.save(video)

        use_case = ListVideosUseCase(video_repo)
        result = use_case.execute(page=1, page_size=3)

        assert result.total == 5
        assert len(result.items) == 3
        assert result.page == 1
        assert result.page_size == 3
        assert result.total_pages == 2

    def test_list_videos_second_page(self, session, video_repo):
        # Create some test videos
        for i in range(5):
            video = Video(
                id=f"video_{i}",
                title=f"Video {i}",
                description=f"Description {i}",
                creator_id="user_1",
                status=VideoStatus.READY,
                url=f"/uploads/video_{i}.mp4",
                thumbnail_url=f"/uploads/thumbnails/video_{i}.jpg"
            )
            video_repo.save(video)

        use_case = ListVideosUseCase(video_repo)
        result = use_case.execute(page=2, page_size=3)

        assert result.total == 5
        assert len(result.items) == 2  # Remaining 2 videos
        assert result.page == 2

    def test_list_videos_empty(self, video_repo):
        use_case = ListVideosUseCase(video_repo)
        result = use_case.execute(page=1, page_size=10)

        assert result.total == 0
        assert len(result.items) == 0
        assert result.total_pages == 1


class TestVideoRepository:
    def test_save_and_get_video(self, video_repo):
        video = Video(
            id="test_id",
            title="Test Video",
            description="Test Description",
            creator_id="creator_1",
            status=VideoStatus.UPLOADING
        )

        saved = video_repo.save(video)
        assert saved.id == "test_id"

        retrieved = video_repo.get_by_id("test_id")
        assert retrieved is not None
        assert retrieved.title == "Test Video"

    def test_delete_video(self, video_repo):
        video = Video(
            id="to_delete",
            title="Delete Me",
            description="Will be deleted",
            creator_id="creator_1",
            status=VideoStatus.READY
        )
        video_repo.save(video)

        result = video_repo.delete("to_delete")
        assert result is True

        retrieved = video_repo.get_by_id("to_delete")
        assert retrieved is None

    def test_delete_nonexistent_video(self, video_repo):
        result = video_repo.delete("nonexistent")
        assert result is False

    def test_count_all(self, video_repo):
        for i in range(3):
            video = Video(
                id=f"count_video_{i}",
                title=f"Video {i}",
                description="Desc",
                creator_id="creator_1",
                status=VideoStatus.READY
            )
            video_repo.save(video)

        count = video_repo.count_all()
        assert count == 3

    def test_list_by_creator(self, video_repo):
        # Videos by creator_1
        for i in range(2):
            video = Video(
                id=f"creator1_video_{i}",
                title=f"Video {i}",
                description="Desc",
                creator_id="creator_1",
                status=VideoStatus.READY
            )
            video_repo.save(video)

        # Video by creator_2
        video = Video(
            id="creator2_video",
            title="Creator 2 Video",
            description="Desc",
            creator_id="creator_2",
            status=VideoStatus.READY
        )
        video_repo.save(video)

        creator1_videos = video_repo.list_by_creator("creator_1")
        assert len(creator1_videos) == 2

        creator2_videos = video_repo.list_by_creator("creator_2")
        assert len(creator2_videos) == 1

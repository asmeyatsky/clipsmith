import pytest
from backend.domain.entities.video import Video
from backend.domain.entities.caption import Caption
import uuid


class TestVideoRepository:
    def test_save_and_get_video(self, video_repo):
        video = Video(
            id=str(uuid.uuid4()),
            title="Test Video",
            description="A test video description",
            creator_id="user123",
            status="READY",
            url="/uploads/test.mp4",
            thumbnail_url="/uploads/test_thumb.jpg",
            views=0,
            likes=0,
            duration=120.5
        )

        saved = video_repo.save(video)
        assert saved.id == video.id
        assert saved.title == "Test Video"

        retrieved = video_repo.get_by_id(video.id)
        assert retrieved is not None
        assert retrieved.title == "Test Video"
        assert retrieved.description == "A test video description"

    def test_find_all_videos(self, video_repo):
        for i in range(5):
            video = Video(
                id=str(uuid.uuid4()),
                title=f"Video {i}",
                description=f"Description {i}",
                creator_id="user123",
                status="READY",
                views=0,
                likes=0,
                duration=60.0
            )
            video_repo.save(video)

        videos = video_repo.find_all(offset=0, limit=10)
        assert len(videos) == 5

    def test_list_by_creator(self, video_repo):
        creator_id = "creator_abc"
        for i in range(3):
            video = Video(
                id=str(uuid.uuid4()),
                title=f"Creator Video {i}",
                description="Test",
                creator_id=creator_id,
                status="READY",
                views=0,
                likes=0,
                duration=30.0
            )
            video_repo.save(video)

        # Add video from different creator
        other_video = Video(
            id=str(uuid.uuid4()),
            title="Other Video",
            description="Test",
            creator_id="other_creator",
            status="READY",
            views=0,
            likes=0,
            duration=30.0
        )
        video_repo.save(other_video)

        creator_videos = video_repo.list_by_creator(creator_id)
        assert len(creator_videos) == 3

    def test_increment_views(self, video_repo):
        video = Video(
            id=str(uuid.uuid4()),
            title="View Test",
            description="Test",
            creator_id="user123",
            status="READY",
            views=0,
            likes=0,
            duration=60.0
        )
        video_repo.save(video)

        updated = video_repo.increment_views(video.id)
        assert updated.views == 1

        updated = video_repo.increment_views(video.id)
        assert updated.views == 2

    def test_search_videos(self, video_repo):
        video1 = Video(
            id=str(uuid.uuid4()),
            title="Python Tutorial",
            description="Learn Python basics",
            creator_id="user123",
            status="READY",
            views=0,
            likes=0,
            duration=60.0
        )
        video2 = Video(
            id=str(uuid.uuid4()),
            title="JavaScript Guide",
            description="Master JavaScript",
            creator_id="user123",
            status="READY",
            views=0,
            likes=0,
            duration=60.0
        )
        video3 = Video(
            id=str(uuid.uuid4()),
            title="Cooking Show",
            description="Make delicious Python... I mean pasta",
            creator_id="user123",
            status="READY",
            views=0,
            likes=0,
            duration=60.0
        )
        video_repo.save(video1)
        video_repo.save(video2)
        video_repo.save(video3)

        # Search for Python
        results = video_repo.search("Python")
        assert len(results) == 2  # Title match and description match

        # Search for JavaScript
        results = video_repo.search("JavaScript")
        assert len(results) == 1

    def test_count_search(self, video_repo):
        for i in range(10):
            video = Video(
                id=str(uuid.uuid4()),
                title=f"Tutorial {i}",
                description="Programming tutorial",
                creator_id="user123",
                status="READY",
                views=0,
                likes=0,
                duration=60.0
            )
            video_repo.save(video)

        count = video_repo.count_search("Tutorial")
        assert count == 10

    def test_delete_video(self, video_repo):
        video = Video(
            id=str(uuid.uuid4()),
            title="To Delete",
            description="Will be deleted",
            creator_id="user123",
            status="READY",
            views=0,
            likes=0,
            duration=60.0
        )
        video_repo.save(video)

        result = video_repo.delete(video.id)
        assert result is True

        retrieved = video_repo.get_by_id(video.id)
        assert retrieved is None


class TestCaptionRepository:
    def test_save_and_get_captions(self, caption_repo):
        video_id = str(uuid.uuid4())

        caption1 = Caption(
            id=str(uuid.uuid4()),
            video_id=video_id,
            text="Hello world",
            start_time=0.0,
            end_time=2.0,
            language="en"
        )
        caption2 = Caption(
            id=str(uuid.uuid4()),
            video_id=video_id,
            text="This is a test",
            start_time=2.0,
            end_time=4.0,
            language="en"
        )

        caption_repo.save(caption1)
        caption_repo.save(caption2)

        captions = caption_repo.get_by_video_id(video_id)
        assert len(captions) == 2
        assert captions[0].start_time < captions[1].start_time

    def test_delete_captions_by_video(self, caption_repo):
        video_id = str(uuid.uuid4())

        for i in range(3):
            caption = Caption(
                id=str(uuid.uuid4()),
                video_id=video_id,
                text=f"Caption {i}",
                start_time=float(i),
                end_time=float(i + 1),
                language="en"
            )
            caption_repo.save(caption)

        result = caption_repo.delete_by_video_id(video_id)
        assert result is True

        captions = caption_repo.get_by_video_id(video_id)
        assert len(captions) == 0

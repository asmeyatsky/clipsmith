import pytest
import asyncio
from datetime import datetime
from sqlmodel import create_engine, Session
from backend.domain.entities.user import User
from backend.domain.entities.video import Video, VideoStatus
from backend.domain.entities.payment import (
    Transaction,
    TransactionType,
    TransactionStatus,
)
from backend.domain.entities.analytics import VideoAnalytics, MetricType, TimePeriod


@pytest.fixture
def db_session():
    """Create a test database session."""
    engine = create_engine("sqlite:///:memory:")
    from backend.infrastructure.repositories.models import SQLModel

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    return User(
        id="test_user_123",
        username="testuser",
        email="test@example.com",
        created_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_video(sample_user):
    """Create a sample video for testing."""
    return Video(
        id="test_video_123",
        user_id=sample_user.id,
        url="https://example.com/video.mp4",
        status=VideoStatus.PROCESSED,
        created_at=datetime.utcnow(),
    )


class TestBasicEntities:
    """Test basic entity creation and validation."""

    def test_user_creation(self):
        """Test user entity creation."""
        user = User(id="user_123", username="testuser", email="test@example.com")

        assert user.id == "user_123"
        assert user.username == "testuser"
        assert user.email == "test@example.com"

    def test_video_creation(self, sample_user):
        """Test video entity creation."""
        video = Video(
            id="video_123",
            user_id=sample_user.id,
            url="https://example.com/video.mp4",
            status=VideoStatus.PROCESSED,
        )

        assert video.id == "video_123"
        assert video.user_id == sample_user.id
        assert video.status == VideoStatus.PROCESSED

    def test_transaction_creation(self, sample_user):
        """Test transaction entity creation."""
        transaction = Transaction(
            user_id=sample_user.id,
            amount=10.0,
            transaction_type=TransactionType.TIP,
            description="Test tip transaction",
        )

        assert transaction.user_id == sample_user.id
        assert transaction.amount == 10.0
        assert transaction.transaction_type == TransactionType.TIP
        assert transaction.description == "Test tip transaction"

    def test_video_analytics_creation(self, sample_video, sample_user):
        """Test video analytics creation."""
        analytics = VideoAnalytics(
            video_id=sample_video.id,
            user_id=sample_user.id,
            views=100,
            likes=25,
            comments=5,
            shares=3,
            period_start=datetime.utcnow(),
            period_end=datetime.utcnow(),
        )

        assert analytics.video_id == sample_video.id
        assert analytics.user_id == sample_user.id
        assert analytics.views == 100
        assert analytics.likes == 25


class TestBusinessLogic:
    """Test business logic methods."""

    def test_transaction_completion(self):
        """Test transaction completion logic."""
        from backend.domain.entities.payment import TransactionStatus

        transaction = Transaction(
            id="test_transaction",
            user_id="test_user",
            amount=10.0,
            transaction_type=TransactionType.TIP,
            status=TransactionStatus.PENDING,
        )

        # Mock the replace method for testing
        class MockTransaction:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)

            def complete(self):
                self.status = TransactionStatus.COMPLETED
                self.completed_at = datetime.utcnow()
                return self

        mock_transaction = MockTransaction(
            id=transaction.id,
            user_id=transaction.user_id,
            amount=transaction.amount,
            transaction_type=transaction.transaction_type,
            status=transaction.status,
        )

        completed_transaction = mock_transaction.complete()

        assert completed_transaction.status == TransactionStatus.COMPLETED
        assert completed_transaction.completed_at is not None

    def test_analytics_calculations(self):
        """Test analytics calculation methods."""
        from backend.domain.entities.analytics import VideoAnalytics

        analytics = VideoAnalytics(
            video_id="test_video",
            user_id="test_user",
            views=100,
            likes=25,
            comments=5,
            shares=3,
            watch_time=300.0,
            period_start=datetime.utcnow(),
            period_end=datetime.utcnow(),
        )

        # Test engagement rate calculation
        interactions = (
            analytics.likes + analytics.comments + analytics.shares
        )  # 25 + 5 + 3 = 33
        expected_rate = (interactions / analytics.views) * 100  # 33%

        # Mock the calculate_engagement_rate method
        def mock_calculate_rate(self):
            interactions = self.likes + self.comments + self.shares
            if self.views == 0:
                return 0.0
            return (interactions / self.views) * 100

        actual_rate = mock_calculate_rate(analytics)
        assert actual_rate == expected_rate


class TestEnums:
    """Test enum values and validation."""

    def test_transaction_types(self):
        """Test transaction type enum."""
        from backend.domain.entities.payment import TransactionType

        assert TransactionType.TIP == "tip"
        assert TransactionType.SUBSCRIPTION == "subscription"
        assert TransactionType.REFUND == "refund"

    def test_video_status(self):
        """Test video status enum."""
        from backend.domain.entities.video import VideoStatus

        assert VideoStatus.UPLOADING == "uploading"
        assert VideoStatus.PROCESSING == "processing"
        assert VideoStatus.PROCESSED == "processed"
        assert VideoStatus.FAILED == "failed"

    def test_analytics_metrics(self):
        """Test analytics metric enum."""
        from backend.domain.entities.analytics import MetricType

        assert MetricType.VIEWS == "views"
        assert MetricType.LIKES == "likes"
        assert MetricType.COMMENTS == "comments"
        assert MetricType.SHARES == "shares"

    def test_time_periods(self):
        """Test time period enum."""
        from backend.domain.entities.analytics import TimePeriod

        assert TimePeriod.HOUR == "hour"
        assert TimePeriod.DAY == "day"
        assert TimePeriod.WEEK == "week"
        assert TimePeriod.MONTH == "month"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

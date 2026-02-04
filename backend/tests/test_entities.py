import pytest
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
from backend.infrastructure.repositories.models import SQLModel


@pytest.fixture
def db_session():
    """Create a test database session."""
    engine = create_engine("sqlite:///:memory:")
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
        assert transaction.status == TransactionStatus.PENDING

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


class TestEntityMethods:
    """Test entity methods and business logic."""

    def test_transaction_completion(self, sample_user):
        """Test transaction completion method."""
        transaction = Transaction(
            user_id=sample_user.id,
            amount=10.0,
            transaction_type=TransactionType.TIP,
            status=TransactionStatus.PENDING,
        )

        completed_transaction = transaction.complete()

        assert completed_transaction.status == TransactionStatus.COMPLETED
        assert completed_transaction.completed_at is not None

    def test_transaction_failure(self, sample_user):
        """Test transaction failure method."""
        transaction = Transaction(
            user_id=sample_user.id,
            amount=10.0,
            transaction_type=TransactionType.TIP,
            status=TransactionStatus.PENDING,
        )

        failed_transaction = transaction.fail()

        assert failed_transaction.status == TransactionStatus.FAILED

    def test_analytics_engagement_calculation(self, sample_video, sample_user):
        """Test analytics engagement rate calculation."""
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

        engagement_rate = analytics.calculate_engagement_rate()
        expected_rate = (25 + 5 + 3) / 100 * 100  # 33%

        assert engagement_rate == expected_rate

    def test_analytics_watch_time_calculation(self, sample_video, sample_user):
        """Test analytics average watch time calculation."""
        analytics = VideoAnalytics(
            video_id=sample_video.id,
            user_id=sample_user.id,
            views=10,
            watch_time=300.0,  # 5 minutes total
            period_start=datetime.utcnow(),
            period_end=datetime.utcnow(),
        )

        avg_watch_time = analytics.calculate_average_watch_time()
        expected_time = 300.0 / 10  # 30 seconds average

        assert avg_watch_time == expected_time


class TestEnums:
    """Test enum values and validation."""

    def test_transaction_types(self):
        """Test transaction type enum."""
        assert TransactionType.TIP == "tip"
        assert TransactionType.SUBSCRIPTION == "subscription"
        assert TransactionType.REFUND == "refund"

    def test_video_status(self):
        """Test video status enum."""
        assert VideoStatus.UPLOADING == "uploading"
        assert VideoStatus.PROCESSING == "processing"
        assert VideoStatus.PROCESSED == "processed"
        assert VideoStatus.FAILED == "failed"

    def test_analytics_metrics(self):
        """Test analytics metric type enum."""
        assert MetricType.VIEWS == "views"
        assert MetricType.LIKES == "likes"
        assert MetricType.COMMENTS == "comments"
        assert MetricType.SHARES == "shares"

    def test_time_periods(self):
        """Test time period enum."""
        assert TimePeriod.HOUR == "hour"
        assert TimePeriod.DAY == "day"
        assert TimePeriod.WEEK == "week"
        assert TimePeriod.MONTH == "month"


class TestDatabaseModels:
    """Test database model creation and relationships."""

    def test_database_session_creation(self, db_session):
        """Test database session creation."""
        assert db_session is not None
        assert isinstance(db_session, Session)

    def test_user_model_creation(self, db_session):
        """Test user database model creation."""
        from backend.infrastructure.repositories.models import UserDB

        user_db = UserDB(
            id="test_user_123", username="testuser", email="test@example.com"
        )

        db_session.add(user_db)
        db_session.commit()
        db_session.refresh(user_db)

        assert user_db.id == "test_user_123"
        assert user_db.username == "testuser"
        assert user_db.email == "test@example.com"

    def test_video_model_creation(self, db_session, sample_user):
        """Test video database model creation."""
        from backend.infrastructure.repositories.models import VideoDB, UserDB

        # Create user first
        user_db = UserDB(
            id=sample_user.id, username=sample_user.username, email=sample_user.email
        )
        db_session.add(user_db)
        db_session.commit()

        # Create video
        video_db = VideoDB(
            id="test_video_123",
            user_id=sample_user.id,
            url="https://example.com/video.mp4",
            status="processed",
        )

        db_session.add(video_db)
        db_session.commit()
        db_session.refresh(video_db)

        assert video_db.id == "test_video_123"
        assert video_db.user_id == sample_user.id
        assert video_db.status == "processed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

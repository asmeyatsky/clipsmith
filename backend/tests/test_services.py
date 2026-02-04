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
from backend.infrastructure.repositories.database import get_session
from backend.application.services.payment_service import PaymentService
from backend.application.services.analytics_service import AnalyticsService
from backend.infrastructure.repositories.sqlite_payment_repo import (
    SQLitePaymentRepository,
)
from backend.infrastructure.repositories.sqlite_analytics_repo import (
    SQLiteAnalyticsRepository,
)


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


class TestPaymentService:
    """Test suite for Payment Service."""

    def test_create_wallet(self, db_session, sample_user):
        """Test wallet creation."""
        repository = SQLitePaymentRepository(db_session)
        service = PaymentService(repository, None)

        wallet = asyncio.run(service.create_wallet(sample_user.id))

        assert wallet.user_id == sample_user.id
        assert wallet.balance == 0.0
        assert wallet.status == "active"

    def test_tip_transaction(self, db_session, sample_user):
        """Test tip transaction creation."""
        repository = SQLitePaymentRepository(db_session)
        service = PaymentService(repository, None)

        result = asyncio.run(
            service.create_tip_transaction(
                sender_id=sample_user.id, receiver_id="creator_123", amount=5.0
            )
        )

        assert result["success"] == True
        assert "payment_intent_id" in result
        assert "client_secret" in result
        assert "transaction_id" in result

    def test_invalid_tip_amount(self, db_session, sample_user):
        """Test tip with invalid amount."""
        repository = SQLitePaymentRepository(db_session)
        service = PaymentService(repository, None)

        result = asyncio.run(
            service.create_tip_transaction(
                sender_id=sample_user.id, receiver_id="creator_123", amount=-5.0
            )
        )

        assert result["success"] == False
        assert "error" in result


class TestAnalyticsService:
    """Test suite for Analytics Service."""

    def test_track_video_view(self, db_session, sample_video, sample_user):
        """Test video view tracking."""
        repository = SQLiteAnalyticsRepository(db_session)
        service = AnalyticsService(repository)

        result = asyncio.run(
            service.track_video_view(
                video_id=sample_video.id, user_id=sample_user.id, watch_time=30.0
            )
        )

        assert result["success"] == True
        assert result["analytics"].video_id == sample_video.id
        assert result["analytics"].views == 1
        assert result["analytics"].watch_time == 30.0

    def test_track_video_engagement(self, db_session, sample_video, sample_user):
        """Test video engagement tracking."""
        repository = SQLiteAnalyticsRepository(db_session)
        service = AnalyticsService(repository)

        # Test like tracking
        result = asyncio.run(
            service.track_video_engagement(
                video_id=sample_video.id, user_id=sample_user.id, engagement_type="like"
            )
        )

        assert result["success"] == True
        assert result["analytics"].likes == 1

        # Test comment tracking
        result = asyncio.run(
            service.track_video_engagement(
                video_id=sample_video.id,
                user_id=sample_user.id,
                engagement_type="comment",
            )
        )

        assert result["success"] == True
        assert result["analytics"].comments == 1

    def test_generate_creator_analytics(self, db_session, sample_user):
        """Test creator analytics generation."""
        repository = SQLiteAnalyticsRepository(db_session)
        service = AnalyticsService(repository)

        result = asyncio.run(
            service.generate_creator_analytics(
                user_id=sample_user.id, period=TimePeriod.MONTH
            )
        )

        assert result["success"] == True
        assert "analytics" in result
        assert "engagement_metrics" in result
        assert "growth_metrics" in result
        assert "revenue_metrics" in result

    def test_generate_time_series_data(self, db_session, sample_user):
        """Test time series data generation."""
        repository = SQLiteAnalyticsRepository(db_session)
        service = AnalyticsService(repository)

        result = asyncio.run(
            service.generate_time_series_data(
                user_id=sample_user.id,
                metric_type=MetricType.VIEWS,
                time_period=TimePeriod.WEEK,
            )
        )

        assert result["success"] == True
        assert "time_series" in result
        assert "data_points" in result
        assert len(result["data_points"]) == 7  # 7 days in a week


class TestPaymentRepository:
    """Test suite for Payment Repository."""

    def test_save_transaction(self, db_session, sample_user):
        """Test transaction saving."""
        repository = SQLitePaymentRepository(db_session)

        transaction = Transaction(
            user_id=sample_user.id,
            amount=10.0,
            transaction_type=TransactionType.TIP,
            description="Test transaction",
        )

        saved_transaction = repository.save_transaction(transaction)

        assert saved_transaction.id is not None
        assert saved_transaction.user_id == sample_user.id
        assert saved_transaction.amount == 10.0

    def test_get_user_transactions(self, db_session, sample_user):
        """Test getting user transactions."""
        repository = SQLitePaymentRepository(db_session)

        # Save some test transactions
        for i in range(3):
            transaction = Transaction(
                user_id=sample_user.id,
                amount=float(i + 1) * 10.0,
                transaction_type=TransactionType.TIP,
                description=f"Test transaction {i + 1}",
            )
            repository.save_transaction(transaction)

        transactions = repository.get_user_transactions(sample_user.id)

        assert len(transactions) == 3
        assert all(t.user_id == sample_user.id for t in transactions)

    def test_transaction_by_reference(self, db_session, sample_user):
        """Test getting transactions by reference ID."""
        repository = SQLitePaymentRepository(db_session)

        transaction = Transaction(
            user_id=sample_user.id,
            amount=10.0,
            transaction_type=TransactionType.TIP,
            reference_id="ref_123",
        )
        repository.save_transaction(transaction)

        found_transactions = repository.get_transactions_by_reference("ref_123")

        assert len(found_transactions) == 1
        assert found_transactions[0].reference_id == "ref_123"


class TestAnalyticsRepository:
    """Test suite for Analytics Repository."""

    def test_save_video_analytics(self, db_session, sample_video, sample_user):
        """Test saving video analytics."""
        repository = SQLiteAnalyticsRepository(db_session)

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

        saved_analytics = repository.save_video_analytics(analytics)

        assert saved_analytics.id is not None
        assert saved_analytics.video_id == sample_video.id
        assert saved_analytics.views == 100

    def test_get_top_performing_videos(self, db_session, sample_user):
        """Test getting top performing videos."""
        repository = SQLiteAnalyticsRepository(db_session)

        # Save test analytics with different view counts
        for i in range(5):
            analytics = VideoAnalytics(
                video_id=f"video_{i}",
                user_id=sample_user.id,
                views=(i + 1) * 50,  # 50, 100, 150, 200, 250 views
                likes=10,
                comments=2,
                shares=1,
                period_start=datetime.utcnow(),
                period_end=datetime.utcnow(),
            )
            repository.save_video_analytics(analytics)

        top_videos = repository.get_top_performing_videos(
            sample_user.id, limit=3, metric="views"
        )

        assert len(top_videos) == 3
        # Should be ordered by views descending
        assert top_videos[0].views >= top_videos[1].views >= top_videos[2].views

    def test_aggregate_daily_analytics(self, db_session, sample_user):
        """Test daily analytics aggregation."""
        repository = SQLiteAnalyticsRepository(db_session)

        # Save test analytics for different videos on the same day
        today = datetime.utcnow()
        for i in range(3):
            analytics = VideoAnalytics(
                video_id=f"video_{i}",
                user_id=sample_user.id,
                views=(i + 1) * 10,
                likes=i + 1,
                comments=1,
                shares=0,
                period_start=today,
                period_end=today,
            )
            repository.save_video_analytics(analytics)

        daily_data = repository.aggregate_daily_analytics(sample_user.id, today)

        assert daily_data["daily_views"] == 60  # 10 + 20 + 30
        assert daily_data["daily_likes"] == 6  # 1 + 2 + 3
        assert daily_data["daily_comments"] == 3
        assert daily_data["active_videos"] == 3


class TestIntegration:
    """Integration tests for the complete system."""

    def test_video_upload_to_analytics_flow(self, db_session, sample_user):
        """Test the complete flow from video upload to analytics tracking."""
        # This would test the integration between video upload and analytics
        # For now, it's a placeholder for integration testing
        pass

    def test_payment_to_analytics_integration(self, db_session, sample_user):
        """Test integration between payment and analytics systems."""
        # Test how payments (tips, subscriptions) flow into analytics
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime
from ..entities.analytics import (
    VideoAnalytics,
    CreatorAnalytics,
    TimeSeriesData,
    AudienceDemographics,
    ContentPerformance,
    MetricType,
    TimePeriod,
    ContentType,
)


class AnalyticsRepositoryPort(ABC):
    """Repository port for analytics operations."""

    # Video Analytics
    @abstractmethod
    def save_video_analytics(self, analytics: VideoAnalytics) -> VideoAnalytics:
        """Save or update video analytics."""
        pass

    @abstractmethod
    def get_video_analytics(
        self,
        video_id: str,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> Optional[VideoAnalytics]:
        """Get analytics for a specific video."""
        pass

    @abstractmethod
    def get_user_video_analytics(
        self,
        user_id: str,
        limit: int = 50,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> List[VideoAnalytics]:
        """Get analytics for user's videos."""
        pass

    @abstractmethod
    def get_top_performing_videos(
        self, user_id: str, limit: int = 10, metric: str = "views"
    ) -> List[VideoAnalytics]:
        """Get top performing videos by metric."""
        pass

    # Creator Analytics
    @abstractmethod
    def save_creator_analytics(self, analytics: CreatorAnalytics) -> CreatorAnalytics:
        """Save or update creator analytics."""
        pass

    @abstractmethod
    def get_creator_analytics(
        self,
        user_id: str,
        period: TimePeriod,
        period_start: datetime,
        period_end: datetime,
    ) -> Optional[CreatorAnalytics]:
        """Get creator analytics for specific period."""
        pass

    @abstractmethod
    def get_creator_analytics_history(
        self, user_id: str, limit: int = 12
    ) -> List[CreatorAnalytics]:
        """Get historical creator analytics."""
        pass

    # Time Series Data
    @abstractmethod
    def save_time_series_data(self, data: TimeSeriesData) -> TimeSeriesData:
        """Save or update time series data."""
        pass

    @abstractmethod
    def get_time_series_data(
        self,
        user_id: str,
        metric_type: MetricType,
        time_period: TimePeriod,
        period_start: datetime,
        period_end: datetime,
    ) -> Optional[TimeSeriesData]:
        """Get time series data for specific metric."""
        pass

    @abstractmethod
    def get_metrics_summary(
        self,
        user_id: str,
        metrics: List[MetricType],
        time_period: TimePeriod,
        period_start: datetime,
        period_end: datetime,
    ) -> Dict[str, Any]:
        """Get summary for multiple metrics."""
        pass

    # Audience Demographics
    @abstractmethod
    def save_audience_demographics(
        self, demographics: AudienceDemographics
    ) -> AudienceDemographics:
        """Save or update audience demographics."""
        pass

    @abstractmethod
    def get_audience_demographics(
        self,
        user_id: str,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> Optional[AudienceDemographics]:
        """Get audience demographics for user."""
        pass

    # Content Performance
    @abstractmethod
    def save_content_performance(
        self, performance: ContentPerformance
    ) -> ContentPerformance:
        """Save or update content performance."""
        pass

    @abstractmethod
    def get_content_performance(self, video_id: str) -> Optional[ContentPerformance]:
        """Get content performance for video."""
        pass

    @abstractmethod
    def get_user_content_performance(
        self, user_id: str, limit: int = 50, content_type: Optional[ContentType] = None
    ) -> List[ContentPerformance]:
        """Get content performance for user's videos."""
        pass

    # Analytics Calculations
    @abstractmethod
    def calculate_engagement_metrics(
        self, user_id: str, period_start: datetime, period_end: datetime
    ) -> Dict[str, float]:
        """Calculate engagement metrics for user."""
        pass

    @abstractmethod
    def calculate_growth_metrics(
        self, user_id: str, period_start: datetime, period_end: datetime
    ) -> Dict[str, float]:
        """Calculate growth metrics for user."""
        pass

    @abstractmethod
    def calculate_revenue_metrics(
        self, user_id: str, period_start: datetime, period_end: datetime
    ) -> Dict[str, float]:
        """Calculate revenue metrics for user."""
        pass

    # Trending and Discovery
    @abstractmethod
    def get_trending_videos(
        self, limit: int = 20, time_period: TimePeriod = TimePeriod.DAY
    ) -> List[VideoAnalytics]:
        """Get trending videos."""
        pass

    @abstractmethod
    def get_trending_creators(
        self, limit: int = 20, time_period: TimePeriod = TimePeriod.WEEK
    ) -> List[CreatorAnalytics]:
        """Get trending creators."""
        pass

    # Data Aggregation
    @abstractmethod
    def aggregate_daily_analytics(self, user_id: str, date: datetime) -> Dict[str, Any]:
        """Aggregate daily analytics for user."""
        pass

    @abstractmethod
    def aggregate_weekly_analytics(
        self, user_id: str, week_start: datetime
    ) -> Dict[str, Any]:
        """Aggregate weekly analytics for user."""
        pass

    @abstractmethod
    def aggregate_monthly_analytics(
        self, user_id: str, month: datetime
    ) -> Dict[str, Any]:
        """Aggregate monthly analytics for user."""
        pass

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
import uuid


class MetricType(str, Enum):
    VIEWS = "views"
    LIKES = "likes"
    COMMENTS = "comments"
    SHARES = "shares"
    TIPS = "tips"
    SUBSCRIPTIONS = "subscriptions"
    WATCH_TIME = "watch_time"
    ENGAGEMENT_RATE = "engagement_rate"
    REACH = "reach"
    IMPRESSIONS = "impressions"


class TimePeriod(str, Enum):
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class ContentType(str, Enum):
    VIDEO = "video"
    SHORT = "short"
    LIVESTREAM = "livestream"


@dataclass(frozen=True, kw_only=True)
class VideoAnalytics:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    video_id: str
    user_id: str
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    tips_count: int = 0
    tips_amount: float = 0.0
    watch_time: float = 0.0  # Total watch time in seconds
    average_watch_time: float = 0.0  # Average watch time per view
    engagement_rate: float = 0.0  # (likes + comments + shares) / views
    reach: int = 0  # Unique viewers
    impressions: int = 0  # Total times shown in feed
    period_start: datetime
    period_end: datetime
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())

    def calculate_engagement_rate(self) -> float:
        """Calculate engagement rate."""
        if self.views == 0:
            return 0.0
        interactions = self.likes + self.comments + self.shares
        return (interactions / self.views) * 100

    def calculate_average_watch_time(self) -> float:
        """Calculate average watch time per view."""
        if self.views == 0:
            return 0.0
        return self.watch_time / self.views

    def update_metrics(self, **kwargs) -> "VideoAnalytics":
        """Update metrics and recalculate derived values."""
        updated_data = {}

        for key, value in kwargs.items():
            if hasattr(self, key):
                updated_data[key] = value

        # Recalculate derived metrics
        if "watch_time" in updated_data or "views" in updated_data:
            watch_time = updated_data.get("watch_time", self.watch_time)
            views = updated_data.get("views", self.views)
            updated_data["average_watch_time"] = (
                watch_time / views if views > 0 else 0.0
            )

        if (
            "views" in updated_data
            or "likes" in updated_data
            or "comments" in updated_data
            or "shares" in updated_data
        ):
            views = updated_data.get("views", self.views)
            likes = updated_data.get("likes", self.likes)
            comments = updated_data.get("comments", self.comments)
            shares = updated_data.get("shares", self.shares)

            if views > 0:
                interactions = likes + comments + shares
                updated_data["engagement_rate"] = (interactions / views) * 100
            else:
                updated_data["engagement_rate"] = 0.0

        return self.replace(**updated_data)


@dataclass(frozen=True, kw_only=True)
class CreatorAnalytics:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    period: TimePeriod
    period_start: datetime
    period_end: datetime

    # Audience metrics
    total_followers: int = 0
    new_followers: int = 0
    follower_growth_rate: float = 0.0

    # Content metrics
    total_videos: int = 0
    total_views: int = 0
    total_likes: int = 0
    total_comments: int = 0
    total_shares: int = 0

    # Engagement metrics
    average_engagement_rate: float = 0.0
    top_performing_videos: List[str] = field(default_factory=list)  # Video IDs

    # Revenue metrics
    total_tips: float = 0.0
    total_subscriptions: float = 0.0
    total_revenue: float = 0.0
    average_revenue_per_follower: float = 0.0

    # Content performance
    most_viewed_video: Optional[str] = None  # Video ID
    most_liked_video: Optional[str] = None  # Video ID
    most_commented_video: Optional[str] = None  # Video ID

    created_at: datetime = field(default_factory=lambda: datetime.utcnow())
    updated_at: Optional[datetime] = None

    def calculate_growth_rate(self, previous_followers: int) -> float:
        """Calculate follower growth rate."""
        if previous_followers == 0:
            return 0.0
        growth = self.total_followers - previous_followers
        return (growth / previous_followers) * 100

    def calculate_average_revenue_per_follower(self) -> float:
        """Calculate average revenue per follower."""
        if self.total_followers == 0:
            return 0.0
        return self.total_revenue / self.total_followers


@dataclass(frozen=True, kw_only=True)
class TimeSeriesData:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    metric_type: MetricType
    time_period: TimePeriod
    data_points: List[Dict[str, Any]] = field(default_factory=list)
    period_start: datetime
    period_end: datetime
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())

    def add_data_point(
        self,
        timestamp: datetime,
        value: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "TimeSeriesData":
        """Add a data point to the time series."""
        data_point = {"timestamp": timestamp.isoformat(), "value": value}

        if metadata:
            data_point["metadata"] = metadata

        return self.replace(data_points=self.data_points + [data_point])


@dataclass(frozen=True, kw_only=True)
class AudienceDemographics:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    age_groups: Dict[str, int] = field(default_factory=dict)
    gender_distribution: Dict[str, int] = field(default_factory=dict)
    location_distribution: Dict[str, int] = field(default_factory=dict)
    device_distribution: Dict[str, int] = field(default_factory=dict)
    language_distribution: Dict[str, int] = field(default_factory=dict)
    period_start: datetime
    period_end: datetime
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())

    def get_top_location(self) -> Optional[str]:
        """Get the location with most viewers."""
        if not self.location_distribution:
            return None
        return max(self.location_distribution, key=self.location_distribution.get)

    def get_primary_device(self) -> Optional[str]:
        """Get the most used device."""
        if not self.device_distribution:
            return None
        return max(self.device_distribution, key=self.device_distribution.get)


@dataclass(frozen=True, kw_only=True)
class ContentPerformance:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    video_id: str
    content_type: ContentType

    # Performance metrics
    views: int = 0
    views_per_day: float = 0.0
    retention_rate: float = 0.0  # Percentage of viewers who watch to end
    click_through_rate: float = 0.0  # For shorts leading to longer videos

    # Engagement breakdown
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0  # Users who saved/bookmarked

    # Revenue
    tips_amount: float = 0.0
    subscription_conversions: int = 0

    # Timing metrics
    peak_view_time: Optional[datetime] = None
    publish_date: datetime
    first_24h_views: int = 0
    first_7d_views: int = 0

    created_at: datetime = field(default_factory=lambda: datetime.utcnow())
    updated_at: Optional[datetime] = None

    def calculate_views_per_day(self) -> float:
        """Calculate average views per day since publish."""
        days_since_publish = (datetime.utcnow() - self.publish_date).days
        if days_since_publish == 0:
            return float(self.views)
        return self.views / days_since_publish

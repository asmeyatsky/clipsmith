from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from ..domain.entities.analytics import (
    VideoAnalytics,
    CreatorAnalytics,
    TimeSeriesData,
    AudienceDemographics,
    ContentPerformance,
    MetricType,
    TimePeriod,
    ContentType,
)
from ..domain.ports.analytics_repository_port import AnalyticsRepositoryPort


class AnalyticsService:
    """Service layer for analytics operations."""

    def __init__(self, repository: AnalyticsRepositoryPort):
        self.repository = repository

    # Video Analytics
    async def track_video_view(
        self,
        video_id: str,
        user_id: Optional[str] = None,
        viewer_id: Optional[str] = None,
        watch_time: float = 0.0,
    ) -> Dict[str, Any]:
        """Track a video view."""
        # Get existing analytics for today
        today = datetime.utcnow()
        start_of_day = today.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        existing_analytics = self.repository.get_video_analytics(
            video_id, start_of_day, end_of_day
        )

        if existing_analytics:
            # Update existing analytics
            updated_analytics = existing_analytics.update_metrics(
                views=existing_analytics.views + 1,
                watch_time=existing_analytics.watch_time + watch_time,
            )
            saved_analytics = self.repository.save_video_analytics(updated_analytics)
        else:
            # Create new analytics record
            new_analytics = VideoAnalytics(
                video_id=video_id,
                user_id=user_id or "unknown",
                views=1,
                watch_time=watch_time,
                period_start=start_of_day,
                period_end=end_of_day,
            )
            saved_analytics = self.repository.save_video_analytics(new_analytics)

        # Also track in content performance
        await this._update_content_performance(video_id, user_id, "view", watch_time)

        return {"success": True, "analytics": saved_analytics}

    async def track_video_engagement(
        self, video_id: str, user_id: str, engagement_type: str, value: int = 1
    ) -> Dict[str, Any]:
        """Track video engagement (like, comment, share, tip)."""
        today = datetime.utcnow()
        start_of_day = today.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        existing_analytics = self.repository.get_video_analytics(
            video_id, start_of_day, end_of_day
        )

        if existing_analytics:
            update_data = {}

            if engagement_type == "like":
                update_data["likes"] = existing_analytics.likes + value
            elif engagement_type == "comment":
                update_data["comments"] = existing_analytics.comments + value
            elif engagement_type == "share":
                update_data["shares"] = existing_analytics.shares + value
            elif engagement_type == "tip":
                update_data["tips_count"] = existing_analytics.tips_count + 1
                update_data["tips_amount"] = existing_analytics.tips_amount + float(
                    value
                )

            updated_analytics = existing_analytics.update_metrics(**update_data)
            saved_analytics = self.repository.save_video_analytics(updated_analytics)
        else:
            # Create new analytics record with engagement
            new_analytics_data = {
                "video_id": video_id,
                "user_id": user_id,
                "period_start": start_of_day,
                "period_end": end_of_day,
                "views": 0,
            }

            if engagement_type == "like":
                new_analytics_data["likes"] = value
            elif engagement_type == "comment":
                new_analytics_data["comments"] = value
            elif engagement_type == "share":
                new_analytics_data["shares"] = value
            elif engagement_type == "tip":
                new_analytics_data["tips_count"] = 1
                new_analytics_data["tips_amount"] = float(value)

            new_analytics = VideoAnalytics(**new_analytics_data)
            saved_analytics = self.repository.save_video_analytics(new_analytics)

        # Track in content performance
        await self._update_content_performance(
            video_id, user_id, engagement_type, value
        )

        return {"success": True, "analytics": saved_analytics}

    async def _update_content_performance(
        self, video_id: str, user_id: str, action_type: str, value: Any = None
    ) -> None:
        """Update content performance metrics."""
        performance = self.repository.get_content_performance(video_id)

        if performance:
            update_data = {}

            if action_type == "view":
                update_data["views"] = performance.views + 1
                if isinstance(value, (int, float)):
                    update_data["watch_time"] = performance.watch_time + value
            elif action_type == "like":
                update_data["likes"] = performance.likes + 1
            elif action_type == "comment":
                update_data["comments"] = performance.comments + 1
            elif action_type == "share":
                update_data["shares"] = performance.shares + 1
            elif action_type == "tip":
                if isinstance(value, (int, float)):
                    update_data["tips_amount"] = performance.tips_amount + value
            elif action_type == "subscription":
                update_data["subscription_conversions"] = (
                    performance.subscription_conversions + 1
                )

            updated_performance = performance.replace(**update_data)
            self.repository.save_content_performance(updated_performance)
        else:
            # Create new content performance record
            # This would need video publish date
            now = datetime.utcnow()
            new_performance = ContentPerformance(
                user_id=user_id,
                video_id=video_id,
                content_type=ContentType.VIDEO,
                views=1 if action_type == "view" else 0,
                likes=1 if action_type == "like" else 0,
                comments=1 if action_type == "comment" else 0,
                shares=1 if action_type == "share" else 0,
                tips_amount=float(value)
                if action_type == "tip" and isinstance(value, (int, float))
                else 0.0,
                publish_date=now,
                first_24h_views=1 if action_type == "view" else 0,
            )
            self.repository.save_content_performance(new_performance)

    # Creator Analytics
    async def generate_creator_analytics(
        self, user_id: str, period: TimePeriod = TimePeriod.MONTH
    ) -> Dict[str, Any]:
        """Generate comprehensive analytics for creator."""
        # Calculate period boundaries
        now = datetime.utcnow()
        if period == TimePeriod.DAY:
            period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(days=1)
        elif period == TimePeriod.WEEK:
            period_start = now - timedelta(days=now.weekday())
            period_start = period_start.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            period_end = period_start + timedelta(days=7)
        elif period == TimePeriod.MONTH:
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(days=32)
            period_end = period_end.replace(day=1) - timedelta(seconds=1)
        else:
            period_start = now - timedelta(days=30)
            period_end = now

        # Check if analytics already exist for this period
        existing_analytics = self.repository.get_creator_analytics(
            user_id, period, period_start, period_end
        )

        # Calculate metrics
        engagement_metrics = self.repository.calculate_engagement_metrics(
            user_id, period_start, period_end
        )
        growth_metrics = self.repository.calculate_growth_metrics(
            user_id, period_start, period_end
        )
        revenue_metrics = self.repository.calculate_revenue_metrics(
            user_id, period_start, period_end
        )

        # Get top performing videos
        top_videos = self.repository.get_top_performing_videos(
            user_id, limit=5, metric="views"
        )
        top_video_ids = [video.video_id for video in top_videos]

        # Get video count
        video_analytics = self.repository.get_user_video_analytics(
            user_id, limit=1000, period_start=period_start, period_end=period_end
        )

        creator_analytics = CreatorAnalytics(
            user_id=user_id,
            period=period,
            period_start=period_start,
            period_end=period_end,
            total_videos=len(set([v.video_id for v in video_analytics])),
            total_views=int(engagement_metrics.get("total_views", 0)),
            total_likes=int(engagement_metrics.get("total_likes", 0)),
            total_comments=int(engagement_metrics.get("total_comments", 0)),
            total_shares=int(engagement_metrics.get("total_shares", 0)),
            average_engagement_rate=engagement_metrics.get("avg_engagement_rate", 0.0),
            top_performing_videos=top_video_ids,
            total_tips=revenue_metrics.get("total_tips", 0.0),
            total_subscriptions=revenue_metrics.get("total_subscriptions", 0.0),
            total_revenue=revenue_metrics.get("total_revenue", 0.0),
            total_followers=int(growth_metrics.get("total_followers", 0)),
            new_followers=int(growth_metrics.get("new_followers", 0)),
            follower_growth_rate=growth_metrics.get("growth_rate", 0.0),
            most_viewed_video=top_video_ids[0] if top_video_ids else None,
        )

        if existing_analytics:
            # Update existing
            creator_analytics = creator_analytics.replace(id=existing_analytics.id)

        saved_analytics = self.repository.save_creator_analytics(creator_analytics)

        return {
            "success": True,
            "analytics": saved_analytics,
            "engagement_metrics": engagement_metrics,
            "growth_metrics": growth_metrics,
            "revenue_metrics": revenue_metrics,
        }

    async def get_creator_dashboard(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive dashboard data for creator."""
        # Get analytics for different periods
        now = datetime.utcnow()

        # Current month
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = month_start + timedelta(days=32)
        month_end = month_end.replace(day=1) - timedelta(seconds=1)

        # Last month
        last_month_start = month_start - timedelta(days=32)
        last_month_end = month_start - timedelta(seconds=1)

        # This week
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = week_start + timedelta(days=7)

        # Get analytics
        current_month_analytics = self.repository.get_creator_analytics(
            user_id, TimePeriod.MONTH, month_start, month_end
        )
        last_month_analytics = self.repository.get_creator_analytics(
            user_id, TimePeriod.MONTH, last_month_start, last_month_end
        )

        # Get trending videos
        trending_videos = self.repository.get_top_performing_videos(
            user_id, limit=5, metric="engagement_rate"
        )

        # Get recent time series data
        views_series = self.repository.get_time_series_data(
            user_id, MetricType.VIEWS, TimePeriod.WEEK, week_start, week_end
        )

        # Calculate growth rates
        monthly_growth = 0.0
        if current_month_analytics and last_month_analytics:
            if last_month_analytics.total_views > 0:
                monthly_growth = (
                    (
                        current_month_analytics.total_views
                        - last_month_analytics.total_views
                    )
                    / last_month_analytics.total_views
                    * 100
                )

        return {
            "success": True,
            "current_month": current_month_analytics.model_dump()
            if current_month_analytics
            else None,
            "last_month": last_month_analytics.model_dump()
            if last_month_analytics
            else None,
            "monthly_growth_rate": monthly_growth,
            "trending_videos": [video.model_dump() for video in trending_videos],
            "views_time_series": views_series.data_points if views_series else [],
            "key_metrics": {
                "total_views": current_month_analytics.total_views
                if current_month_analytics
                else 0,
                "total_revenue": current_month_analytics.total_revenue
                if current_month_analytics
                else 0.0,
                "follower_growth": current_month_analytics.new_followers
                if current_month_analytics
                else 0,
                "engagement_rate": current_month_analytics.average_engagement_rate
                if current_month_analytics
                else 0.0,
            },
        }

    # Time Series
    async def generate_time_series_data(
        self, user_id: str, metric_type: MetricType, time_period: TimePeriod
    ) -> Dict[str, Any]:
        """Generate time series data for a specific metric."""
        now = datetime.utcnow()

        # Calculate period boundaries based on time_period
        if time_period == TimePeriod.DAY:
            period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(days=1)
            data_points = []

            # Generate hourly data points
            for hour in range(24):
                hour_start = period_start + timedelta(hours=hour)
                hour_end = hour_start + timedelta(hours=1)

                value = await self._get_metric_value(
                    user_id, metric_type, hour_start, hour_end
                )

                data_points.append(
                    {"timestamp": hour_start.isoformat(), "value": value}
                )

        elif time_period == TimePeriod.WEEK:
            period_start = now - timedelta(days=now.weekday())
            period_start = period_start.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            period_end = period_start + timedelta(days=7)
            data_points = []

            # Generate daily data points
            for day in range(7):
                day_start = period_start + timedelta(days=day)
                day_end = day_start + timedelta(days=1)

                value = await self._get_metric_value(
                    user_id, metric_type, day_start, day_end
                )

                data_points.append({"timestamp": day_start.isoformat(), "value": value})

        elif time_period == TimePeriod.MONTH:
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(days=32)
            period_end = period_end.replace(day=1) - timedelta(seconds=1)
            data_points = []

            # Generate daily data points
            current_day = period_start
            while current_day < period_end:
                day_end = current_day + timedelta(days=1)

                value = await self._get_metric_value(
                    user_id, metric_type, current_day, day_end
                )

                data_points.append(
                    {"timestamp": current_day.isoformat(), "value": value}
                )

                current_day = day_end

        else:
            return {"success": False, "error": "Unsupported time period"}

        # Save time series data
        time_series_data = TimeSeriesData(
            user_id=user_id,
            metric_type=metric_type,
            time_period=time_period,
            data_points=data_points,
            period_start=period_start,
            period_end=period_end,
        )

        saved_data = self.repository.save_time_series_data(time_series_data)

        return {"success": True, "time_series": saved_data, "data_points": data_points}

    async def _get_metric_value(
        self,
        user_id: str,
        metric_type: MetricType,
        start_time: datetime,
        end_time: datetime,
    ) -> float:
        """Get metric value for a specific time range."""
        metrics_summary = self.repository.get_metrics_summary(
            user_id, [metric_type], TimePeriod.DAY, start_time, end_time
        )

        if metric_type == MetricType.VIEWS:
            return metrics_summary.get("total_views", 0.0)
        elif metric_type == MetricType.LIKES:
            return metrics_summary.get("total_likes", 0.0)
        elif metric_type == MetricType.TIPS:
            return metrics_summary.get("total_tips", 0.0)
        else:
            return 0.0

    # Audience Demographics
    async def update_audience_demographics(
        self, user_id: str, demographics_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update audience demographics for creator."""
        now = datetime.utcnow()
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        period_end = period_start + timedelta(days=32)
        period_end = period_end.replace(day=1) - timedelta(seconds=1)

        # Check if demographics already exist for current month
        existing_demographics = self.repository.get_audience_demographics(
            user_id, period_start, period_end
        )

        demographics = AudienceDemographics(
            user_id=user_id,
            age_groups=demographics_data.get("age_groups", {}),
            gender_distribution=demographics_data.get("gender_distribution", {}),
            location_distribution=demographics_data.get("location_distribution", {}),
            device_distribution=demographics_data.get("device_distribution", {}),
            language_distribution=demographics_data.get("language_distribution", {}),
            period_start=period_start,
            period_end=period_end,
        )

        if existing_demographics:
            demographics = demographics.replace(id=existing_demographics.id)

        saved_demographics = self.repository.save_audience_demographics(demographics)

        return {"success": True, "demographics": saved_demographics}

    # Trending and Discovery
    async def get_trending_content(
        self,
        content_type: str = "video",
        time_period: TimePeriod = TimePeriod.DAY,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """Get trending content."""
        trending_videos = self.repository.get_trending_videos(limit, time_period)

        # Get creator information for each video
        trending_with_creators = []
        for video_analytics in trending_videos:
            # This would typically fetch user info from user repository
            trending_with_creators.append(
                {
                    "video_id": video_analytics.video_id,
                    "views": video_analytics.views,
                    "likes": video_analytics.likes,
                    "comments": video_analytics.comments,
                    "shares": video_analytics.shares,
                    "engagement_rate": video_analytics.engagement_rate,
                    "user_id": video_analytics.user_id,
                    # Add user info as needed
                }
            )

        return {
            "success": True,
            "trending_content": trending_with_creators,
            "content_type": content_type,
            "time_period": time_period.value,
        }

    async def get_trending_creators(
        self, time_period: TimePeriod = TimePeriod.WEEK, limit: int = 20
    ) -> Dict[str, Any]:
        """Get trending creators."""
        trending_creators = self.repository.get_trending_creators(limit, time_period)

        return {
            "success": True,
            "trending_creators": [
                creator.model_dump() for creator in trending_creators
            ],
            "time_period": time_period.value,
        }

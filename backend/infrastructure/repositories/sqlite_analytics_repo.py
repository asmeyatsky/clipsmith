from typing import List, Optional, Dict, Any
from sqlmodel import Session, select, and_, desc, func
from datetime import datetime, timedelta
from ...domain.entities.analytics import (
    VideoAnalytics,
    CreatorAnalytics,
    TimeSeriesData,
    AudienceDemographics,
    ContentPerformance,
    MetricType,
    TimePeriod,
    ContentType,
)
from ...domain.ports.analytics_repository_port import AnalyticsRepositoryPort
from .database import engine
from .models import (
    VideoAnalyticsDB,
    CreatorAnalyticsDB,
    TimeSeriesDataDB,
    AudienceDemographicsDB,
    ContentPerformanceDB,
)
import json


class SQLiteAnalyticsRepository(AnalyticsRepositoryPort):
    def __init__(self, session: Session):
        self.session = session

    # Video Analytics
    def save_video_analytics(self, analytics: VideoAnalytics) -> VideoAnalytics:
        analytics_db = VideoAnalyticsDB.model_validate(analytics)
        analytics_db = self.session.merge(analytics_db)
        self.session.commit()
        self.session.refresh(analytics_db)
        return VideoAnalytics(**analytics_db.model_dump())

    def get_video_analytics(
        self,
        video_id: str,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> Optional[VideoAnalytics]:
        query = select(VideoAnalyticsDB).where(VideoAnalyticsDB.video_id == video_id)

        if period_start:
            query = query.where(VideoAnalyticsDB.period_start >= period_start)

        if period_end:
            query = query.where(VideoAnalyticsDB.period_end <= period_end)

        analytics_db = self.session.exec(
            query.order_by(VideoAnalyticsDB.created_at.desc())
        ).first()
        if analytics_db:
            return VideoAnalytics(**analytics_db.model_dump())
        return None

    def get_user_video_analytics(
        self,
        user_id: str,
        limit: int = 50,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> List[VideoAnalytics]:
        query = select(VideoAnalyticsDB).where(VideoAnalyticsDB.user_id == user_id)

        if period_start:
            query = query.where(VideoAnalyticsDB.period_start >= period_start)

        if period_end:
            query = query.where(VideoAnalyticsDB.period_end <= period_end)

        query = query.order_by(VideoAnalyticsDB.created_at.desc()).limit(limit)

        results = self.session.exec(query).all()
        return [VideoAnalytics(**analytics.model_dump()) for analytics in results]

    def get_top_performing_videos(
        self, user_id: str, limit: int = 10, metric: str = "views"
    ) -> List[VideoAnalytics]:
        # Map metric strings to database columns
        metric_map = {
            "views": VideoAnalyticsDB.views,
            "likes": VideoAnalyticsDB.likes,
            "comments": VideoAnalyticsDB.comments,
            "shares": VideoAnalyticsDB.shares,
            "engagement_rate": VideoAnalyticsDB.engagement_rate,
            "tips_amount": VideoAnalyticsDB.tips_amount,
        }

        order_column = metric_map.get(metric, VideoAnalyticsDB.views)

        query = select(VideoAnalyticsDB).where(VideoAnalyticsDB.user_id == user_id)
        query = query.order_by(order_column.desc()).limit(limit)

        results = self.session.exec(query).all()
        return [VideoAnalytics(**analytics.model_dump()) for analytics in results]

    # Creator Analytics
    def save_creator_analytics(self, analytics: CreatorAnalytics) -> CreatorAnalytics:
        analytics_db = CreatorAnalyticsDB.model_validate(analytics)

        # Convert list to JSON string if needed
        if analytics.top_performing_videos:
            analytics_db.top_performing_videos = json.dumps(
                analytics.top_performing_videos
            )

        analytics_db = self.session.merge(analytics_db)
        self.session.commit()
        self.session.refresh(analytics_db)
        return CreatorAnalytics(**analytics_db.model_dump())

    def get_creator_analytics(
        self,
        user_id: str,
        period: TimePeriod,
        period_start: datetime,
        period_end: datetime,
    ) -> Optional[CreatorAnalytics]:
        analytics_db = self.session.exec(
            select(CreatorAnalyticsDB)
            .where(
                and_(
                    CreatorAnalyticsDB.user_id == user_id,
                    CreatorAnalyticsDB.period == period.value,
                    CreatorAnalyticsDB.period_start >= period_start,
                    CreatorAnalyticsDB.period_end <= period_end,
                )
            )
            .order_by(CreatorAnalyticsDB.created_at.desc())
        ).first()

        if analytics_db:
            # Parse JSON string back to list
            analytics_dict = analytics_db.model_dump()
            if analytics_db.top_performing_videos:
                analytics_dict["top_performing_videos"] = json.loads(
                    analytics_db.top_performing_videos
                )

            return CreatorAnalytics(**analytics_dict)
        return None

    def get_creator_analytics_history(
        self, user_id: str, limit: int = 12
    ) -> List[CreatorAnalytics]:
        query = select(CreatorAnalyticsDB).where(CreatorAnalyticsDB.user_id == user_id)
        query = query.order_by(CreatorAnalyticsDB.period_start.desc()).limit(limit)

        results = self.session.exec(query).all()
        analytics_list = []

        for analytics_db in results:
            analytics_dict = analytics_db.model_dump()
            if analytics_db.top_performing_videos:
                analytics_dict["top_performing_videos"] = json.loads(
                    analytics_db.top_performing_videos
                )

            analytics_list.append(CreatorAnalytics(**analytics_dict))

        return analytics_list

    # Time Series Data
    def save_time_series_data(self, data: TimeSeriesData) -> TimeSeriesData:
        data_db = TimeSeriesDataDB.model_validate(data)

        # Convert list to JSON string
        if data.data_points:
            data_db.data_points = json.dumps(data.data_points)

        data_db = self.session.merge(data_db)
        self.session.commit()
        self.session.refresh(data_db)
        return TimeSeriesData(**data_db.model_dump())

    def get_time_series_data(
        self,
        user_id: str,
        metric_type: MetricType,
        time_period: TimePeriod,
        period_start: datetime,
        period_end: datetime,
    ) -> Optional[TimeSeriesData]:
        data_db = self.session.exec(
            select(TimeSeriesDataDB)
            .where(
                and_(
                    TimeSeriesDataDB.user_id == user_id,
                    TimeSeriesDataDB.metric_type == metric_type.value,
                    TimeSeriesDataDB.time_period == time_period.value,
                    TimeSeriesDataDB.period_start >= period_start,
                    TimeSeriesDataDB.period_end <= period_end,
                )
            )
            .order_by(TimeSeriesDataDB.created_at.desc())
        ).first()

        if data_db:
            data_dict = data_db.model_dump()
            if data_db.data_points:
                data_dict["data_points"] = json.loads(data_db.data_points)

            return TimeSeriesData(**data_dict)
        return None

    def get_metrics_summary(
        self,
        user_id: str,
        metrics: List[MetricType],
        time_period: TimePeriod,
        period_start: datetime,
        period_end: datetime,
    ) -> Dict[str, Any]:
        summary = {}

        for metric in metrics:
            if metric == MetricType.VIEWS:
                result = self.session.exec(
                    select(func.sum(VideoAnalyticsDB.views)).where(
                        and_(
                            VideoAnalyticsDB.user_id == user_id,
                            VideoAnalyticsDB.period_start >= period_start,
                            VideoAnalyticsDB.period_end <= period_end,
                        )
                    )
                ).first()
                summary["total_views"] = int(result) if result else 0

            elif metric == MetricType.LIKES:
                result = self.session.exec(
                    select(func.sum(VideoAnalyticsDB.likes)).where(
                        and_(
                            VideoAnalyticsDB.user_id == user_id,
                            VideoAnalyticsDB.period_start >= period_start,
                            VideoAnalyticsDB.period_end <= period_end,
                        )
                    )
                ).first()
                summary["total_likes"] = int(result) if result else 0

            elif metric == MetricType.TIPS:
                result = self.session.exec(
                    select(func.sum(VideoAnalyticsDB.tips_amount)).where(
                        and_(
                            VideoAnalyticsDB.user_id == user_id,
                            VideoAnalyticsDB.period_start >= period_start,
                            VideoAnalyticsDB.period_end <= period_end,
                        )
                    )
                ).first()
                summary["total_tips"] = float(result) if result else 0.0

        return summary

    # Audience Demographics
    def save_audience_demographics(
        self, demographics: AudienceDemographics
    ) -> AudienceDemographics:
        demographics_db = AudienceDemographicsDB.model_validate(demographics)

        # Convert dicts to JSON strings
        if demographics.age_groups:
            demographics_db.age_groups = json.dumps(demographics.age_groups)
        if demographics.gender_distribution:
            demographics_db.gender_distribution = json.dumps(
                demographics.gender_distribution
            )
        if demographics.location_distribution:
            demographics_db.location_distribution = json.dumps(
                demographics.location_distribution
            )
        if demographics.device_distribution:
            demographics_db.device_distribution = json.dumps(
                demographics.device_distribution
            )
        if demographics.language_distribution:
            demographics_db.language_distribution = json.dumps(
                demographics.language_distribution
            )

        demographics_db = self.session.merge(demographics_db)
        self.session.commit()
        self.session.refresh(demographics_db)
        return AudienceDemographics(**demographics_db.model_dump())

    def get_audience_demographics(
        self,
        user_id: str,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> Optional[AudienceDemographics]:
        query = select(AudienceDemographicsDB).where(
            AudienceDemographicsDB.user_id == user_id
        )

        if period_start:
            query = query.where(AudienceDemographicsDB.period_start >= period_start)

        if period_end:
            query = query.where(AudienceDemographicsDB.period_end <= period_end)

        demographics_db = self.session.exec(
            query.order_by(AudienceDemographicsDB.created_at.desc())
        ).first()

        if demographics_db:
            demographics_dict = demographics_db.model_dump()

            # Parse JSON strings back to dicts
            for field in [
                "age_groups",
                "gender_distribution",
                "location_distribution",
                "device_distribution",
                "language_distribution",
            ]:
                json_string = getattr(demographics_db, field)
                if json_string:
                    demographics_dict[field] = json.loads(json_string)

            return AudienceDemographics(**demographics_dict)
        return None

    # Content Performance
    def save_content_performance(
        self, performance: ContentPerformance
    ) -> ContentPerformance:
        performance_db = ContentPerformanceDB.model_validate(performance)
        performance_db = self.session.merge(performance_db)
        self.session.commit()
        self.session.refresh(performance_db)
        return ContentPerformance(**performance_db.model_dump())

    def get_content_performance(self, video_id: str) -> Optional[ContentPerformance]:
        performance_db = self.session.exec(
            select(ContentPerformanceDB).where(
                ContentPerformanceDB.video_id == video_id
            )
        ).first()

        if performance_db:
            return ContentPerformance(**performance_db.model_dump())
        return None

    def get_user_content_performance(
        self, user_id: str, limit: int = 50, content_type: Optional[ContentType] = None
    ) -> List[ContentPerformance]:
        query = select(ContentPerformanceDB).where(
            ContentPerformanceDB.user_id == user_id
        )

        if content_type:
            query = query.where(ContentPerformanceDB.content_type == content_type.value)

        query = query.order_by(ContentPerformanceDB.created_at.desc()).limit(limit)

        results = self.session.exec(query).all()
        return [
            ContentPerformance(**performance.model_dump()) for performance in results
        ]

    # Analytics Calculations
    def calculate_engagement_metrics(
        self, user_id: str, period_start: datetime, period_end: datetime
    ) -> Dict[str, float]:
        # Get total metrics for the period
        result = self.session.exec(
            select(
                func.sum(VideoAnalyticsDB.views).label("total_views"),
                func.sum(VideoAnalyticsDB.likes).label("total_likes"),
                func.sum(VideoAnalyticsDB.comments).label("total_comments"),
                func.sum(VideoAnalyticsDB.shares).label("total_shares"),
                func.avg(VideoAnalyticsDB.engagement_rate).label("avg_engagement_rate"),
            ).where(
                and_(
                    VideoAnalyticsDB.user_id == user_id,
                    VideoAnalyticsDB.period_start >= period_start,
                    VideoAnalyticsDB.period_end <= period_end,
                )
            )
        ).first()

        total_views = int(result.total_views) if result.total_views else 0
        total_likes = int(result.total_likes) if result.total_likes else 0
        total_comments = int(result.total_comments) if result.total_comments else 0
        total_shares = int(result.total_shares) if result.total_shares else 0
        avg_engagement_rate = (
            float(result.avg_engagement_rate) if result.avg_engagement_rate else 0.0
        )

        return {
            "total_views": float(total_views),
            "total_likes": float(total_likes),
            "total_comments": float(total_comments),
            "total_shares": float(total_shares),
            "total_interactions": float(total_likes + total_comments + total_shares),
            "avg_engagement_rate": avg_engagement_rate,
            "interaction_rate": (total_likes + total_comments + total_shares)
            / total_views
            if total_views > 0
            else 0.0,
        }

    def calculate_growth_metrics(
        self, user_id: str, period_start: datetime, period_end: datetime
    ) -> Dict[str, float]:
        # This would typically compare with previous period
        # For now, return current period metrics
        current_analytics = self.get_creator_analytics(
            user_id, TimePeriod.MONTH, period_start, period_end
        )

        if not current_analytics:
            return {"growth_rate": 0.0, "new_followers": 0.0}

        return {
            "growth_rate": current_analytics.follower_growth_rate,
            "new_followers": float(current_analytics.new_followers),
            "total_followers": float(current_analytics.total_followers),
        }

    def calculate_revenue_metrics(
        self, user_id: str, period_start: datetime, period_end: datetime
    ) -> Dict[str, float]:
        # Get revenue from video analytics (tips) and payment repository (subscriptions)
        tips_result = self.session.exec(
            select(func.sum(VideoAnalyticsDB.tips_amount)).where(
                and_(
                    VideoAnalyticsDB.user_id == user_id,
                    VideoAnalyticsDB.period_start >= period_start,
                    VideoAnalyticsDB.period_end <= period_end,
                )
            )
        ).first()

        total_tips = float(tips_result) if tips_result else 0.0

        # This would typically include subscription revenue from payment repository
        # For now, return tips only
        return {
            "total_tips": total_tips,
            "total_subscriptions": 0.0,  # Would come from payment repo
            "total_revenue": total_tips,
            "average_revenue_per_follower": 0.0,  # Would need follower count
        }

    # Trending and Discovery
    def get_trending_videos(
        self, limit: int = 20, time_period: TimePeriod = TimePeriod.DAY
    ) -> List[VideoAnalytics]:
        # Calculate period start based on time period
        now = datetime.utcnow()
        if time_period == TimePeriod.DAY:
            period_start = now - timedelta(days=1)
        elif time_period == TimePeriod.WEEK:
            period_start = now - timedelta(weeks=1)
        else:
            period_start = now - timedelta(days=1)  # Default to day

        query = select(VideoAnalyticsDB).where(
            VideoAnalyticsDB.period_start >= period_start
        )
        query = query.order_by(
            VideoAnalyticsDB.views.desc(), VideoAnalyticsDB.engagement_rate.desc()
        ).limit(limit)

        results = self.session.exec(query).all()
        return [VideoAnalytics(**analytics.model_dump()) for analytics in results]

    def get_trending_creators(
        self, limit: int = 20, time_period: TimePeriod = TimePeriod.WEEK
    ) -> List[CreatorAnalytics]:
        # Calculate period start based on time period
        now = datetime.utcnow()
        if time_period == TimePeriod.WEEK:
            period_start = now - timedelta(weeks=1)
        elif time_period == TimePeriod.MONTH:
            period_start = now - timedelta(days=30)
        else:
            period_start = now - timedelta(weeks=1)  # Default to week

        query = select(CreatorAnalyticsDB).where(
            CreatorAnalyticsDB.period_start >= period_start
        )
        query = query.order_by(
            CreatorAnalyticsDB.follower_growth_rate.desc(),
            CreatorAnalyticsDB.total_views.desc(),
        ).limit(limit)

        results = self.session.exec(query).all()
        analytics_list = []

        for analytics_db in results:
            analytics_dict = analytics_db.model_dump()
            if analytics_db.top_performing_videos:
                analytics_dict["top_performing_videos"] = json.loads(
                    analytics_db.top_performing_videos
                )

            analytics_list.append(CreatorAnalytics(**analytics_dict))

        return analytics_list

    # Data Aggregation
    def aggregate_daily_analytics(self, user_id: str, date: datetime) -> Dict[str, Any]:
        # Aggregate all video analytics for the given date
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        result = self.session.exec(
            select(
                func.sum(VideoAnalyticsDB.views).label("daily_views"),
                func.sum(VideoAnalyticsDB.likes).label("daily_likes"),
                func.sum(VideoAnalyticsDB.comments).label("daily_comments"),
                func.sum(VideoAnalyticsDB.shares).label("daily_shares"),
                func.count(VideoAnalyticsDB.video_id).label("active_videos"),
            ).where(
                and_(
                    VideoAnalyticsDB.user_id == user_id,
                    VideoAnalyticsDB.period_start >= day_start,
                    VideoAnalyticsDB.period_start < day_end,
                )
            )
        ).first()

        return {
            "date": date.isoformat(),
            "daily_views": int(result.daily_views) if result.daily_views else 0,
            "daily_likes": int(result.daily_likes) if result.daily_likes else 0,
            "daily_comments": int(result.daily_comments)
            if result.daily_comments
            else 0,
            "daily_shares": int(result.daily_shares) if result.daily_shares else 0,
            "active_videos": int(result.active_videos) if result.active_videos else 0,
        }

    def aggregate_weekly_analytics(
        self, user_id: str, week_start: datetime
    ) -> Dict[str, Any]:
        week_end = week_start + timedelta(weeks=1)

        # Similar to daily aggregation but for week
        result = self.session.exec(
            select(
                func.sum(VideoAnalyticsDB.views).label("weekly_views"),
                func.sum(VideoAnalyticsDB.likes).label("weekly_likes"),
                func.sum(VideoAnalyticsDB.comments).label("weekly_comments"),
                func.sum(VideoAnalyticsDB.shares).label("weekly_shares"),
                func.count(VideoAnalyticsDB.video_id).label("active_videos"),
            ).where(
                and_(
                    VideoAnalyticsDB.user_id == user_id,
                    VideoAnalyticsDB.period_start >= week_start,
                    VideoAnalyticsDB.period_start < week_end,
                )
            )
        ).first()

        return {
            "week_start": week_start.isoformat(),
            "weekly_views": int(result.weekly_views) if result.weekly_views else 0,
            "weekly_likes": int(result.weekly_likes) if result.weekly_likes else 0,
            "weekly_comments": int(result.weekly_comments)
            if result.weekly_comments
            else 0,
            "weekly_shares": int(result.weekly_shares) if result.weekly_shares else 0,
            "active_videos": int(result.active_videos) if result.active_videos else 0,
        }

    def aggregate_monthly_analytics(
        self, user_id: str, month: datetime
    ) -> Dict[str, Any]:
        month_start = month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # Calculate end of month
        next_month = month_start + timedelta(days=32)
        month_end = next_month.replace(day=1) - timedelta(seconds=1)

        result = self.session.exec(
            select(
                func.sum(VideoAnalyticsDB.views).label("monthly_views"),
                func.sum(VideoAnalyticsDB.likes).label("monthly_likes"),
                func.sum(VideoAnalyticsDB.comments).label("monthly_comments"),
                func.sum(VideoAnalyticsDB.shares).label("monthly_shares"),
                func.count(VideoAnalyticsDB.video_id).label("active_videos"),
            ).where(
                and_(
                    VideoAnalyticsDB.user_id == user_id,
                    VideoAnalyticsDB.period_start >= month_start,
                    VideoAnalyticsDB.period_start < month_end,
                )
            )
        ).first()

        return {
            "month": month.isoformat(),
            "monthly_views": int(result.monthly_views) if result.monthly_views else 0,
            "monthly_likes": int(result.monthly_likes) if result.monthly_likes else 0,
            "monthly_comments": int(result.monthly_comments)
            if result.monthly_comments
            else 0,
            "monthly_shares": int(result.monthly_shares)
            if result.monthly_shares
            else 0,
            "active_videos": int(result.active_videos) if result.active_videos else 0,
        }

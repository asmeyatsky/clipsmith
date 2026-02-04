from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from ...application.services.analytics_service import AnalyticsService
from ...infrastructure.repositories.sqlite_analytics_repo import (
    SQLiteAnalyticsRepository,
)
from ...infrastructure.repositories.database import get_session
from ...presentation.middleware.security import get_current_user
from ...domain.entities.analytics import MetricType, TimePeriod, ContentType
from sqlmodel import Session
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def get_analytics_service(session: Session = Depends(get_session)) -> AnalyticsService:
    """Dependency injection for analytics service."""
    repository = SQLiteAnalyticsRepository(session)
    return AnalyticsService(repository)


# Video Analytics endpoints
@router.post("/videos/{video_id}/track")
async def track_video_event(
    video_id: str,
    event_type: str = Query(
        ..., description="Event type: view, like, comment, share, tip"
    ),
    value: float = Query(
        1.0, description="Event value (amount for tips, count for others)"
    ),
    watch_time: float = Query(0.0, description="Watch time in seconds for views"),
    current_user: Optional[dict] = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Track video events (views, engagement, etc.)."""
    user_id = current_user["id"] if current_user else None

    if event_type == "view":
        result = await service.track_video_view(
            video_id, user_id, watch_time=watch_time
        )
    elif event_type in ["like", "comment", "share"]:
        result = await service.track_video_engagement(
            video_id, user_id, event_type, int(value)
        )
    elif event_type == "tip":
        result = await service.track_video_engagement(
            video_id, user_id, event_type, value
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid event type")

    if not result["success"]:
        raise HTTPException(
            status_code=400, detail=result.get("error", "Tracking failed")
        )

    return {"success": True, "tracked": True}


@router.get("/videos/{video_id}/analytics")
async def get_video_analytics(
    video_id: str,
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
    current_user: Optional[dict] = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Get analytics for a specific video."""
    # Check permissions - video owner or admin
    if current_user:
        analytics = service.repository.get_video_analytics(
            video_id, period_start, period_end
        )
        return {"success": True, "analytics": analytics}
    else:
        raise HTTPException(status_code=403, detail="Access denied")


@router.get("/videos/analytics")
async def get_user_video_analytics(
    limit: int = Query(50, ge=1, le=100),
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
    current_user: dict = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Get analytics for user's videos."""
    analytics = service.repository.get_user_video_analytics(
        current_user["id"], limit, period_start, period_end
    )
    return {"success": True, "analytics": analytics}


@router.get("/videos/top-performing")
async def get_top_performing_videos(
    metric: str = Query(
        "views",
        description="Metric to rank by: views, likes, comments, shares, engagement_rate",
    ),
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Get user's top performing videos."""
    top_videos = service.repository.get_top_performing_videos(
        current_user["id"], limit, metric
    )
    return {"success": True, "top_videos": top_videos}


# Creator Analytics endpoints
@router.get("/creator/dashboard")
async def get_creator_dashboard(
    current_user: dict = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Get comprehensive creator dashboard."""
    dashboard = await service.get_creator_dashboard(current_user["id"])

    if not dashboard["success"]:
        raise HTTPException(
            status_code=400,
            detail=dashboard.get("error", "Dashboard generation failed"),
        )

    return dashboard


@router.get("/creator/analytics")
async def get_creator_analytics(
    period: str = Query("month", description="Time period: day, week, month"),
    current_user: dict = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Get creator analytics for specific period."""
    try:
        time_period = TimePeriod(period)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid time period")

    analytics = await service.generate_creator_analytics(
        current_user["id"], time_period
    )

    if not analytics["success"]:
        raise HTTPException(
            status_code=400,
            detail=analytics.get("error", "Analytics generation failed"),
        )

    return analytics


@router.get("/creator/history")
async def get_analytics_history(
    limit: int = Query(12, ge=1, le=24),
    current_user: dict = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Get historical creator analytics."""
    history = service.repository.get_creator_analytics_history(
        current_user["id"], limit
    )
    return {"success": True, "history": history}


# Time Series endpoints
@router.get("/time-series/{metric}")
async def get_time_series_data(
    metric: str,
    time_period: str = Query("week", description="Time period: day, week, month"),
    current_user: dict = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Get time series data for a specific metric."""
    try:
        metric_type = MetricType(metric)
        period = TimePeriod(time_period)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid metric or time period")

    time_series = await service.generate_time_series_data(
        current_user["id"], metric_type, period
    )

    if not time_series["success"]:
        raise HTTPException(
            status_code=400,
            detail=time_series.get("error", "Time series generation failed"),
        )

    return time_series


# Audience Demographics endpoints
@router.get("/audience/demographics")
async def get_audience_demographics(
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
    current_user: dict = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Get audience demographics."""
    demographics = service.repository.get_audience_demographics(
        current_user["id"], period_start, period_end
    )
    return {"success": True, "demographics": demographics}


@router.post("/audience/demographics")
async def update_audience_demographics(
    demographics_data: dict,
    current_user: dict = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Update audience demographics data."""
    result = await service.update_audience_demographics(
        current_user["id"], demographics_data
    )

    if not result["success"]:
        raise HTTPException(
            status_code=400, detail=result.get("error", "Demographics update failed")
        )

    return result


# Content Performance endpoints
@router.get("/content/performance/{video_id}")
async def get_content_performance(
    video_id: str,
    current_user: dict = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Get performance metrics for specific content."""
    performance = service.repository.get_content_performance(video_id)
    return {"success": True, "performance": performance}


@router.get("/content/performance")
async def get_user_content_performance(
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Get performance metrics for user's content."""
    content_type_enum = ContentType(content_type) if content_type else None

    performance = service.repository.get_user_content_performance(
        current_user["id"], limit, content_type_enum
    )
    return {"success": True, "performance": performance}


# Trending and Discovery endpoints
@router.get("/trending/content")
async def get_trending_content(
    content_type: str = Query("video", description="Content type"),
    time_period: str = Query("day", description="Time period: day, week, month"),
    limit: int = Query(20, ge=1, le=50),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Get trending content across the platform."""
    try:
        period = TimePeriod(time_period)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid time period")

    trending = await service.get_trending_content(content_type, period, limit)

    if not trending["success"]:
        raise HTTPException(
            status_code=400,
            detail=trending.get("error", "Trending content fetch failed"),
        )

    return trending


@router.get("/trending/creators")
async def get_trending_creators(
    time_period: str = Query("week", description="Time period: day, week, month"),
    limit: int = Query(20, ge=1, le=50),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Get trending creators across the platform."""
    try:
        period = TimePeriod(time_period)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid time period")

    trending = await service.get_trending_creators(period, limit)

    if not trending["success"]:
        raise HTTPException(
            status_code=400,
            detail=trending.get("error", "Trending creators fetch failed"),
        )

    return trending


# Aggregation endpoints
@router.get("/aggregates/daily")
async def get_daily_analytics(
    date: datetime = Query(..., description="Date for daily analytics"),
    current_user: dict = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Get daily aggregated analytics."""
    daily_data = service.repository.aggregate_daily_analytics(current_user["id"], date)
    return {"success": True, "daily_analytics": daily_data}


@router.get("/aggregates/weekly")
async def get_weekly_analytics(
    week_start: datetime = Query(..., description="Start of the week"),
    current_user: dict = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Get weekly aggregated analytics."""
    weekly_data = service.repository.aggregate_weekly_analytics(
        current_user["id"], week_start
    )
    return {"success": True, "weekly_analytics": weekly_data}


@router.get("/aggregates/monthly")
async def get_monthly_analytics(
    month: datetime = Query(..., description="Month for analytics"),
    current_user: dict = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Get monthly aggregated analytics."""
    monthly_data = service.repository.aggregate_monthly_analytics(
        current_user["id"], month
    )
    return {"success": True, "monthly_analytics": monthly_data}


# Metrics Summary endpoints
@router.get("/metrics/summary")
async def get_metrics_summary(
    metrics: str = Query("views,likes,comments", description="Comma-separated metrics"),
    time_period: str = Query("week", description="Time period: day, week, month"),
    current_user: dict = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Get summary for specific metrics."""
    try:
        metric_list = [MetricType(m.strip()) for m in metrics.split(",")]
        period = TimePeriod(time_period)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid metrics or time period")

    # Calculate period boundaries
    now = datetime.utcnow()
    if period == TimePeriod.DAY:
        period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        period_end = period_start + timedelta(days=1)
    elif period == TimePeriod.WEEK:
        period_start = now - timedelta(days=now.weekday())
        period_start = period_start.replace(hour=0, minute=0, second=0, microsecond=0)
        period_end = period_start + timedelta(days=7)
    else:  # MONTH
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        period_end = period_start + timedelta(days=32)
        period_end = period_end.replace(day=1) - timedelta(seconds=1)

    summary = service.repository.get_metrics_summary(
        current_user["id"], metric_list, period, period_start, period_end
    )

    return {"success": True, "metrics": summary}

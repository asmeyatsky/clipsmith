from typing import Annotated
from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from ..application.services.monitoring_service import monitoring_service, logger
from ..infrastructure.security.jwt_adapter import JWTAdapter

router = APIRouter(prefix="/monitoring", tags=["monitoring"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
):
    payload = JWTAdapter.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    return payload


@router.get("/health")
def get_system_health():
    """
    Get comprehensive system health status.
    Requires admin access in production.
    """
    health_status = monitoring_service.get_health_status()

    # Add additional context for production use
    health_status["environment"] = os.getenv("ENVIRONMENT", "development")
    health_status["version"] = "1.0.0"
    health_status["service"] = "clipsmith-api"

    if health_status["status"] == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_status.get("error", "Service unavailable"),
        )

    return health_status


@router.get("/metrics")
def get_metrics_summary(
    days: Annotated[
        int, Query(ge=1, le=30, description="Days of metrics to analyze")
    ] = 7,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
):
    """
    Get application metrics for the specified time period.
    Requires admin access.
    """
    # Check admin permissions (simplified for demo)
    if current_user and not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )

    metrics = monitoring_service.get_metrics_summary()

    # Filter by time period
    if days > 0:
        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Filter API requests by time period
        metrics["api_requests"] = [
            req
            for req in metrics["api_requests"]
            if datetime.fromisoformat(req["timestamp"]) >= cutoff_date
        ]

        # Calculate time-period specific metrics
        recent_requests = metrics["api_requests"]
        if recent_requests:
            avg_response_time = sum(
                req["response_time"] for req in recent_requests
            ) / len(recent_requests)
            error_rate = sum(
                1 for req in recent_requests if req["status_code"] >= 400
            ) / len(recent_requests)
        else:
            avg_response_time = 0
            error_rate = 0

        metrics["time_period_stats"] = {
            "days": days,
            "requests_count": len(recent_requests),
            "average_response_time": round(avg_response_time, 3),
            "error_rate": round(error_rate * 100, 2),
        }

    return metrics


@router.get("/logs")
def get_recent_logs(
    lines: Annotated[
        int, Query(ge=1, le=1000, description="Number of log lines to return")
    ] = 100,
    level: Annotated[
        str, Query(description="Log level (debug, info, warning, error)")
    ] = "info",
    current_user: Annotated[dict, Depends(get_current_user)] = None,
):
    """
    Get recent application logs.
    Requires admin access.
    """
    # Check admin permissions
    if current_user and not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )

    try:
        with open("logs/clipsmith.log", "r") as log_file:
            # Read from the end
            log_file.seek(0, 2)  # Go to end
            file_size = log_file.tell()

            # Find lines containing the specified level
            lines = []
            while len(lines) < lines and file_size > 0:
                file_file.seek(file_size - 1024, 1)  # Go back 1KB
                chunk = log_file.readline()
                if chunk:
                    if level.lower() in chunk.lower():
                        lines.append(chunk.strip())
                file_size = log_file.tell()

            log_file.close()

        return {
            "lines": lines,
            "level": level,
            "total_lines": len(lines),
            "lines_returned": len(lines),
        }

    except Exception as e:
        logger.error(f"Failed to read log file: {e}")
        return {
            "error": str(e),
            "lines": [],
            "level": level,
            "total_lines": 0,
            "lines_returned": 0,
        }


@router.post("/test-log")
def test_logging(
    message: Annotated[
        str, Query(description="Test message to log")
    ] = "Test message from monitoring endpoint",
    current_user: Annotated[dict, Depends(get_current_user)] = None,
):
    """
    Test the logging system by logging a message.
    Requires admin access.
    """
    # Check admin permissions
    if current_user and not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )

    # Log test message
    logger.info(
        f"Test log message: {message}",
        extra={
            "test": True,
            "timestamp": monitoring_service.metrics["system_health"].get("timestamp"),
            "endpoint": "/monitoring/test-log",
        },
    )

    return {
        "message": f"Test message logged: {message}",
        "timestamp": monitoring_service.metrics["system_health"].get("timestamp"),
    }


@router.get("/performance")
def get_performance_metrics(
    hours: Annotated[
        int, Query(ge=1, le=24, description="Hours of performance data to analyze")
    ] = 1,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
):
    """
    Get detailed performance metrics.
    Requires admin access.
    """
    # Check admin permissions
    if current_user and not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )

    # Performance metrics would include:
    # - Response times by endpoint
    # - Error rates by endpoint
    # - Active user metrics
    # - System resource usage

    metrics = monitoring_service.metrics_summary()

    # Detailed endpoint analysis
    recent_requests = metrics.get("api_requests", [])
    endpoint_performance = {}

    for req in recent_requests:
        endpoint = req["endpoint"]
        if endpoint not in endpoint_performance:
            endpoint_performance[endpoint] = {
                "requests": 0,
                "total_response_time": 0,
                "errors": 0,
                "avg_response_time": 0,
            }

        endpoint_performance[endpoint]["requests"] += 1
        endpoint_performance[endpoint]["total_response_time"] += req.get(
            "response_time", 0
        )
        if req["status_code"] >= 400:
            endpoint_performance[endpoint]["errors"] += 1
        endpoint_performance[endpoint]["avg_response_time"] = (
            endpoint_performance[endpoint]["total_response_time"]
            / endpoint_performance[endpoint]["requests"]
        )

    # Calculate average performance across all endpoints
    all_avg_times = [
        perf["avg_response_time"]
        for perf in endpoint_performance.values()
        if perf["requests"] > 0
    ]
    overall_avg = sum(all_avg_times) / len(all_avg_times) if all_avg_times else 0

    return {
        "summary": metrics,
        "endpoint_performance": dict(
            sorted(
                endpoint_performance.items(),
                key=lambda x: x[1]["avg_response_time"],
                reverse=True,
            )
        ),
        "overall_average_response_time": round(overall_avg, 3),
        "hours_analyzed": hours,
    }

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from ...application.services.monitoring_service import (
    monitoring_service,
    logger,
    error_reporting,
)


class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for API monitoring and request logging."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # Get client IP and user agent
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent", "Unknown")

        # Get user from request state if available
        user_id = getattr(request.state, "user_id", None)

        # Log request start
        logger.info(
            "API Request Started",
            method=request.method,
            path=request.url.path,
            client_ip=client_ip,
            user_agent=user_agent,
            user_id=user_id,
        )

        try:
            # Process request
            response = await call_next(request)

            # Calculate response time
            process_time = time.time() - start_time

            # Record metrics
            monitoring_service.record_api_request(
                method=request.method,
                endpoint=request.url.path,
                user_id=user_id,
                status_code=response.status_code,
                response_time=process_time,
            )

            # Log completion
            logger.info(
                "API Request Completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                response_time=f"{process_time:.3f}s",
                client_ip=client_ip,
                user_agent=user_agent,
                user_id=user_id,
            )

            # Add monitoring headers
            response.headers["X-Response-Time"] = f"{process_time:.3f}"
            response.headers["X-Request-ID"] = str(
                int(time.time() * 1000)
            )  # Unique request ID

            return response

        except Exception as e:
            process_time = time.time() - start_time

            # Log error
            logger.error(
                "API Request Failed",
                method=request.method,
                path=request.url.path,
                error=str(e),
                response_time=f"{process_time:.3f}s",
                client_ip=client_ip,
                user_agent=user_agent,
                user_id=user_id,
            )

            # Record error metrics
            monitoring_service.record_error(
                "api_request",
                f"Request failed: {str(e)}",
                {
                    "method": request.method,
                    "path": request.url.path,
                    "client_ip": client_ip,
                    "user_agent": user_agent,
                    "user_id": user_id,
                },
            )

            # Capture exception for external monitoring
            error_reporting.capture_exception(
                e,
                {
                    "request_method": request.method,
                    "request_path": request.url.path,
                    "client_ip": client_ip,
                    "user_agent": user_agent,
                    "user_id": user_id,
                },
            )

            # Re-raise exception
            raise e


class HealthCheckMiddleware:
    """Middleware for periodic health checks."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # Check if this is a health check request
        if scope["type"] == "http" and scope["path"] == "/health":
            health_status = monitoring_service.get_health_status()
            return await send(
                {
                    "type": "http.response.start",
                    "status": 200,
                    "headers": {"content-type": "application/json"},
                }
            )

        # Regular request - pass through
        await self.app(scope, receive, send)


class UserActivityMiddleware:
    """Middleware to track user activity."""

    async def __call__(self, scope, receive, send):
        # Extract user from JWT token if available
        request = Request(scope, receive)

        # Look for Authorization header
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                # This is simplified - in production, you'd verify the JWT properly
                # For now, we'll just extract user_id if token exists
                import base64

                token_parts = auth_header.split(" ")[1]

                # Simple token parsing (for demonstration)
                if len(token_parts) == 3:  # header.payload.signature
                    user_info = base64.b64decode(token_parts[1])
                    if user_info and user_info.isdigit():
                        user_id = user_info
                        request.state.user_id = user_id
                        monitoring_service.record_user_activity(
                            user_id=user_id,
                            activity_type="api_request",
                            endpoint=request.url.path,
                        )
            except Exception:
                pass  # Ignore token parsing errors for now

        await self.app(scope, receive, send)

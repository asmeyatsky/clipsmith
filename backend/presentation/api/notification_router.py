from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from ...domain.ports.repository_ports import (
    NotificationRepositoryPort,
    UserRepositoryPort,
    VideoRepositoryPort,
)
from ...infrastructure.repositories.sqlite_notification_repo import (
    SQLiteNotificationRepository,
)
from ...infrastructure.repositories.sqlite_user_repo import SQLiteUserRepository
from ...infrastructure.repositories.sqlite_video_repo import SQLiteVideoRepository
from ...application.services.notification_service import NotificationService
from ...domain.entities.notification import NotificationStatus
from ...infrastructure.security.jwt_adapter import JWTAdapter

router = APIRouter(prefix="/notifications", tags=["notifications"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Dependency Injection Helpers
from ...infrastructure.repositories.database import get_session
from sqlmodel import Session


def get_notification_repo(
    session: Session = Depends(get_session),
) -> NotificationRepositoryPort:
    return SQLiteNotificationRepository(session)


def get_user_repo(session: Session = Depends(get_session)) -> UserRepositoryPort:
    return SQLiteUserRepository(session)


def get_video_repo(session: Session = Depends(get_session)) -> VideoRepositoryPort:
    return SQLiteVideoRepository(session)


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_repo: UserRepositoryPort = Depends(get_user_repo),
):
    payload = JWTAdapter.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    user = user_repo.get_by_id(payload.get("sub"))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


def get_notification_service(
    notification_repo: NotificationRepositoryPort = Depends(get_notification_repo),
    user_repo: UserRepositoryPort = Depends(get_user_repo),
    video_repo: VideoRepositoryPort = Depends(get_video_repo),
) -> NotificationService:
    return NotificationService(notification_repo, user_repo, video_repo)


@router.get("/")
def get_notifications(
    status: Annotated[
        Optional[str], Query(description="Filter by status: unread, read, archived")
    ] = None,
    offset: Annotated[
        int, Query(ge=0, description="Number of notifications to skip")
    ] = 0,
    limit: Annotated[
        int, Query(ge=1, le=100, description="Maximum notifications to return")
    ] = 20,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    notification_service: NotificationService = Depends(get_notification_service),
):
    """
    Get user's notifications with optional filtering.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    # Convert status string to enum
    notification_status = None
    if status:
        try:
            notification_status = NotificationStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status}. Must be one of: unread, read, archived",
            )

    notifications = notification_service.notification_repo.get_user_notifications(
        current_user.id, notification_status, offset, limit
    )

    return [notification.to_dict() for notification in notifications]


@router.get("/summary")
def get_notification_summary(
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    notification_service: NotificationService = Depends(get_notification_service),
):
    """
    Get a summary of user's notifications including unread count and recent activity.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    return notification_service.get_notification_summary(current_user.id)


@router.post("/{notification_id}/read")
def mark_notification_read(
    notification_id: str,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    notification_service: NotificationService = Depends(get_notification_service),
):
    """
    Mark a specific notification as read.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    # Verify notification belongs to user
    notification = notification_service.notification_repo.get_by_id(notification_id)
    if not notification or notification.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    success = notification_service.notification_repo.mark_as_read(notification_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notification as read",
        )

    return {"message": "Notification marked as read", "success": True}


@router.post("/mark-all-read")
def mark_all_notifications_read(
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    notification_service: NotificationService = Depends(get_notification_service),
):
    """
    Mark all unread notifications as read for the current user.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    count = notification_service.notification_repo.mark_all_as_read(current_user.id)

    return {"message": f"Marked {count} notifications as read", "count": count}


@router.get("/unread-count")
def get_unread_count(
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    notification_service: NotificationService = Depends(get_notification_service),
):
    """
    Get the count of unread notifications for the current user.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    count = notification_service.notification_repo.get_unread_count(current_user.id)

    return {"unread_count": count}


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: str,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    notification_service: NotificationService = Depends(get_notification_service),
):
    """
    Delete a specific notification.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    # Verify notification belongs to user
    notification = notification_service.notification_repo.get_by_id(notification_id)
    if not notification or notification.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    success = notification_service.notification_repo.delete_notification(
        notification_id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete notification",
        )

    return {"message": "Notification deleted successfully", "success": True}

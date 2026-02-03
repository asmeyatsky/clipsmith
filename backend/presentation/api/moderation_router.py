from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field

from ...domain.ports.repository_ports import ContentModerationRepositoryPort
from ...infrastructure.repositories.sqlite_content_moderation_repo import (
    SQLiteContentModerationRepository,
)
from ...application.services.content_moderation_service import (
    AIModerationService,
    HumanModerationService,
)
from ...domain.entities.content_moderation import (
    ModerationStatus,
    ModerationSeverity,
    ModerationReason,
)
from ...infrastructure.security.jwt_adapter import JWTAdapter

router = APIRouter(prefix="/moderation", tags=["moderation"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Dependency Injection Helpers
from ...infrastructure.repositories.database import get_session
from sqlmodel import Session


def get_moderation_repo(
    session: Session = Depends(get_session),
) -> ContentModerationRepositoryPort:
    return SQLiteContentModerationRepository(session)


def get_ai_moderation_service(
    moderation_repo: ContentModerationRepositoryPort = Depends(get_moderation_repo),
) -> AIModerationService:
    return AIModerationService(moderation_repo)


def get_human_moderation_service(
    moderation_repo: ContentModerationRepositoryPort = Depends(get_moderation_repo),
) -> HumanModerationService:
    return HumanModerationService(moderation_repo)


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


def require_moderator_role(current_user: dict = None):
    """Check if user has moderator role (simplified check)."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    # In a real system, you'd check user roles/permissions
    # For now, we'll use a simple check
    if not current_user.get("is_moderator", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Moderator access required",
        )

    return current_user


# Pydantic models for requests
class ModerationReviewRequest(BaseModel):
    moderation_id: str
    action: str = Field(..., description="Action: 'approve' or 'reject'")
    reason: Optional[str] = Field(
        None, description="Reason for rejection (required for reject)"
    )
    severity: Optional[ModerationSeverity] = Field(
        None, description="Severity level (required for reject)"
    )
    notes: Optional[str] = Field(None, description="Additional notes")


class BulkModerationRequest(BaseModel):
    moderation_ids: List[str]
    action: str = Field(..., description="Action: 'approve' or 'reject'")
    notes: Optional[str] = Field(None, description="Additional notes for bulk action")


@router.get("/queue")
def get_moderation_queue(
    status: Annotated[Optional[str], Query(description="Filter by status")] = None,
    severity: Annotated[
        Optional[ModerationSeverity], Query(description="Filter by severity")
    ] = None,
    limit: Annotated[
        int, Query(ge=1, le=100, description="Maximum items to return")
    ] = 20,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    ai_service: AIModerationService = Depends(get_ai_moderation_service),
    human_service: HumanModerationService = Depends(get_human_moderation_service),
):
    """
    Get content moderation queue for human reviewers.
    Requires moderator access.
    """
    require_moderator_role(current_user)

    # Get pending moderations
    pending_moderations = human_service.review_pending_content(limit=limit)

    # If status filter is applied, get by status
    if status:
        moderation_repo = get_moderation_repo()
        try:
            status_enum = ModerationStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status}",
            )

        moderations = moderation_repo.get_moderations_by_status(status_enum, limit)
    else:
        moderations = pending_moderations

    # Filter by severity if specified
    if severity:
        moderations = [m for m in moderations if m.severity == severity]

    return {
        "moderations": [
            {
                "id": m.id,
                "content_type": m.content_type,
                "content_id": m.content_id,
                "user_id": m.user_id,
                "status": m.status,
                "severity": m.severity,
                "reason": m.reason,
                "confidence_score": m.confidence_score,
                "ai_labels": m.ai_labels,
                "auto_action": m.auto_action,
                "created_at": m.created_at.isoformat(),
                "reviewed_at": m.reviewed_at.isoformat() if m.reviewed_at else None,
                "completed_at": m.completed_at.isoformat() if m.completed_at else None,
                "human_reviewer_id": m.human_reviewer_id,
                "human_notes": m.human_notes,
            }
            for m in moderations
        ],
        "total": len(moderations),
        "filters": {"status": status, "severity": severity.value if severity else None},
    }


@router.post("/review/{moderation_id}")
def review_content(
    moderation_id: str,
    review_data: ModerationReviewRequest,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    human_service: HumanModerationService = Depends(get_human_moderation_service),
):
    """
    Review a specific content item (approve or reject).
    Requires moderator access.
    """
    require_moderator_role(current_user)

    if review_data.action not in ["approve", "reject"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Action must be 'approve' or 'reject'",
        )

    if review_data.action == "reject" and not review_data.reason:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reason is required for rejection",
        )

    reviewer_id = current_user["user_id"]

    if review_data.action == "approve":
        moderation = human_service.approve_content(
            moderation_id, reviewer_id, review_data.notes
        )
    else:  # reject
        if not review_data.severity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Severity is required for rejection",
            )

        moderation = human_service.reject_content(
            moderation_id,
            reviewer_id,
            review_data.reason,
            review_data.severity,
            review_data.notes,
        )

    if not moderation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Moderation item not found"
        )

    return {
        "message": f"Content {review_data.action}d successfully",
        "moderation": moderation.to_dict()
        if hasattr(moderation, "to_dict")
        else {"id": moderation.id, "status": moderation.status.value},
    }


@router.post("/bulk-review")
def bulk_review_content(
    bulk_data: BulkModerationRequest,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    human_service: HumanModerationService = Depends(get_human_moderation_service),
):
    """
    Bulk approve/reject multiple moderation items.
    Requires moderator access.
    """
    require_moderator_role(current_user)

    if bulk_data.action not in ["approve", "reject"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Action must be 'approve' or 'reject'",
        )

    reviewer_id = current_user["user_id"]
    processed_count = 0
    errors = []

    for moderation_id in bulk_data.moderation_ids:
        if bulk_data.action == "approve":
            moderation = human_service.approve_content(
                moderation_id, reviewer_id, bulk_data.notes
            )
        else:  # reject
            moderation = human_service.reject_content(
                moderation_id,
                reviewer_id,
                ModerationReason.TERMS_OF_SERVICE_VIOLATION,
                ModerationSeverity.MEDIUM,
                bulk_data.notes,
            )

        if moderation:
            processed_count += 1
        else:
            errors.append(moderation_id)

    return {
        "message": f"Bulk {bulk_data.action} completed",
        "processed_count": processed_count,
        "error_count": len(errors),
        "errors": errors,
    }


@router.get("/statistics")
def get_moderation_statistics(
    days: Annotated[
        int, Query(ge=1, le=365, description="Days of statistics to analyze")
    ] = 30,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    moderation_repo: ContentModerationRepositoryPort = Depends(get_moderation_repo),
):
    """
    Get moderation statistics for the admin dashboard.
    Requires moderator access.
    """
    require_moderator_role(current_user)

    stats = moderation_repo.get_statistics(days)

    return {
        "period_days": days,
        "total_moderated": stats["total_moderated"],
        "approved": stats["approved"],
        "rejected": stats["rejected"],
        "flagged": stats["flagged"],
        "high_severity": stats["high_severity"],
        "critical_severity": stats["critical_severity"],
        "approval_rate": stats["approval_rate"],
        "rejection_rate": stats["rejection_rate"],
    }


@router.get("/reviewer-stats/{reviewer_id}")
def get_reviewer_statistics(
    reviewer_id: str,
    days: Annotated[
        int, Query(ge=1, le=365, description="Days of statistics to analyze")
    ] = 30,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    human_service: HumanModerationService = Depends(get_human_moderation_service),
):
    """
    Get statistics for a specific reviewer.
    Requires moderator access.
    """
    require_moderator_role(current_user)

    # Users can only see their own stats
    if current_user["user_id"] != reviewer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only view your own statistics",
        )

    stats = human_service.get_reviewer_statistics(reviewer_id, days)

    return stats


@router.post("/cleanup")
def cleanup_old_records(
    days: Annotated[
        int, Query(ge=1, le=365, description="Delete records older than N days")
    ] = 90,
    current_user: Annotated[dict, Depends(get_current_user)] = None,
    moderation_repo: ContentModerationRepositoryPort = Depends(get_moderation_repo),
):
    """
    Clean up old moderation records.
    Requires moderator access.
    """
    require_moderator_role(current_user)

    deleted_count = moderation_repo.delete_old_records(days)

    return {
        "message": f"Cleaned up {deleted_count} old moderation records",
        "deleted_count": deleted_count,
        "days_threshold": days,
    }

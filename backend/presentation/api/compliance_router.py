from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional
from ...infrastructure.repositories.database import get_session
from .auth_router import get_current_user
from sqlmodel import Session, select
from datetime import datetime
import uuid

router = APIRouter(prefix="/api/compliance", tags=["compliance"])


# ==================== GDPR Endpoints ====================


@router.post("/gdpr/request")
def submit_gdpr_request(
    request_body: dict,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Submit a GDPR data request (export, deletion, etc.)."""
    from ...infrastructure.repositories.models import GDPRRequestDB

    request_type = request_body.get("request_type")
    if not request_type:
        raise HTTPException(status_code=400, detail="request_type is required")

    valid_types = ("export", "deletion", "rectification", "restriction", "portability")
    if request_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid request_type. Must be one of: {', '.join(valid_types)}",
        )

    gdpr_request = GDPRRequestDB(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        request_type=request_type,
        status="pending",
    )
    session.add(gdpr_request)
    session.commit()

    return {
        "success": True,
        "request": {
            "id": gdpr_request.id,
            "request_type": gdpr_request.request_type,
            "status": gdpr_request.status,
            "submitted_at": gdpr_request.created_at.isoformat() if gdpr_request.created_at else None,
        },
    }


@router.get("/gdpr/request/{request_id}")
def get_gdpr_request_status(
    request_id: str,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Get the status of a GDPR request."""
    from ...infrastructure.repositories.models import GDPRRequestDB

    gdpr_request = session.get(GDPRRequestDB, request_id)
    if not gdpr_request:
        raise HTTPException(status_code=404, detail="GDPR request not found")

    if gdpr_request.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return {
        "success": True,
        "request": {
            "id": gdpr_request.id,
            "request_type": gdpr_request.request_type,
            "status": gdpr_request.status,
            "submitted_at": gdpr_request.created_at.isoformat() if gdpr_request.created_at else None,
            "completed_at": gdpr_request.completed_at.isoformat() if gdpr_request.completed_at else None,
        },
    }


@router.post("/gdpr/export")
def export_user_data(
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Request a full export of user data (GDPR Article 20)."""
    from ...infrastructure.repositories.models import GDPRRequestDB

    # Check for existing pending export request
    existing = session.exec(
        select(GDPRRequestDB).where(
            GDPRRequestDB.user_id == current_user.id,
            GDPRRequestDB.request_type == "export",
            GDPRRequestDB.status == "pending",
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=400, detail="You already have a pending export request"
        )

    export_request = GDPRRequestDB(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        request_type="export",
        status="pending",
    )
    session.add(export_request)
    session.commit()

    return {
        "success": True,
        "message": "Data export request submitted. You will be notified when it is ready.",
        "request_id": export_request.id,
    }


@router.post("/gdpr/delete")
def delete_user_data(
    request_body: dict,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Request deletion of specific user data categories (GDPR Article 17)."""
    from ...infrastructure.repositories.models import GDPRRequestDB

    categories = request_body.get("categories", [])
    if not categories:
        raise HTTPException(
            status_code=400,
            detail="At least one data category must be specified for deletion",
        )

    valid_categories = ("profile", "videos", "comments", "likes", "messages", "analytics", "all")
    for cat in categories:
        if cat not in valid_categories:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category: {cat}. Must be one of: {', '.join(valid_categories)}",
            )

    delete_request = GDPRRequestDB(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        request_type="deletion",
        status="pending",
        details=",".join(categories),
    )
    session.add(delete_request)
    session.commit()

    return {
        "success": True,
        "message": "Data deletion request submitted for categories: " + ", ".join(categories),
        "request_id": delete_request.id,
    }


# ==================== Consent Endpoints ====================


@router.post("/consent")
def record_consent(
    request_body: dict,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Record user consent for a specific purpose."""
    from ...infrastructure.repositories.models import ConsentRecordDB

    consent_type = request_body.get("consent_type")
    granted = request_body.get("granted")

    if not consent_type:
        raise HTTPException(status_code=400, detail="consent_type is required")
    if granted is None:
        raise HTTPException(status_code=400, detail="granted is required")

    valid_types = ("analytics", "marketing", "personalization", "third_party", "cookies")
    if consent_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid consent_type. Must be one of: {', '.join(valid_types)}",
        )

    # Update existing or create new
    existing = session.exec(
        select(ConsentRecordDB).where(
            ConsentRecordDB.user_id == current_user.id,
            ConsentRecordDB.consent_type == consent_type,
        )
    ).first()

    if existing:
        existing.granted = granted
        existing.updated_at = datetime.utcnow()
        session.add(existing)
    else:
        consent = ConsentRecordDB(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            consent_type=consent_type,
            granted=granted,
        )
        session.add(consent)

    session.commit()

    return {"success": True, "consent_type": consent_type, "granted": granted}


@router.get("/consent")
def get_user_consents(
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Get all consent records for the current user."""
    from ...infrastructure.repositories.models import ConsentRecordDB

    consents = session.exec(
        select(ConsentRecordDB).where(ConsentRecordDB.user_id == current_user.id)
    ).all()

    return {
        "success": True,
        "consents": [
            {
                "id": c.id,
                "consent_type": c.consent_type,
                "granted": c.granted,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            }
            for c in consents
        ],
    }


@router.post("/consent/withdraw")
def withdraw_consent(
    request_body: dict,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Withdraw a previously granted consent."""
    from ...infrastructure.repositories.models import ConsentRecordDB

    consent_type = request_body.get("consent_type")
    if not consent_type:
        raise HTTPException(status_code=400, detail="consent_type is required")

    consent = session.exec(
        select(ConsentRecordDB).where(
            ConsentRecordDB.user_id == current_user.id,
            ConsentRecordDB.consent_type == consent_type,
        )
    ).first()

    if not consent:
        raise HTTPException(status_code=404, detail="No consent record found for this type")

    consent.granted = False
    consent.updated_at = datetime.utcnow()
    session.add(consent)
    session.commit()

    return {"success": True, "message": f"Consent withdrawn for {consent_type}"}


# ==================== Age Verification Endpoints ====================


@router.post("/age-verification")
def verify_age(
    request_body: dict,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Verify user age for compliance."""
    from ...infrastructure.repositories.models import AgeVerificationDB

    date_of_birth = request_body.get("date_of_birth")
    if not date_of_birth:
        raise HTTPException(status_code=400, detail="date_of_birth is required")

    try:
        dob = datetime.fromisoformat(date_of_birth)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid date_of_birth format. Use ISO format.")

    # Calculate age
    today = datetime.utcnow()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    is_minor = age < 13
    requires_parental_consent = 13 <= age < 18

    verification = AgeVerificationDB(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        date_of_birth=date_of_birth,
        verified_age=age,
        is_minor=is_minor,
        requires_parental_consent=requires_parental_consent,
        status="verified",
    )
    session.add(verification)
    session.commit()

    result = {
        "success": True,
        "age": age,
        "is_minor": is_minor,
        "requires_parental_consent": requires_parental_consent,
        "status": "verified",
    }

    if is_minor:
        result["message"] = "Users under 13 are not allowed to use this service."
    elif requires_parental_consent:
        result["message"] = "Parental consent may be required for users under 18."

    return result


# ==================== CCPA Endpoints ====================


@router.get("/ccpa/data")
def get_ccpa_data(
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Get user data as required by CCPA (California Consumer Privacy Act)."""
    return {
        "success": True,
        "user_id": current_user.id,
        "data_categories_collected": [
            "personal_identifiers",
            "account_information",
            "usage_data",
            "content_data",
            "device_information",
        ],
        "data_shared_with_third_parties": False,
        "opt_out_status": False,
        "message": "Request a full data export via /api/compliance/gdpr/export for complete data.",
    }


@router.post("/ccpa/opt-out")
def opt_out_data_sale(
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Opt out of the sale of personal data (CCPA)."""
    from ...infrastructure.repositories.models import ConsentRecordDB

    # Record opt-out as a consent withdrawal for third_party data sharing
    existing = session.exec(
        select(ConsentRecordDB).where(
            ConsentRecordDB.user_id == current_user.id,
            ConsentRecordDB.consent_type == "third_party",
        )
    ).first()

    if existing:
        existing.granted = False
        existing.updated_at = datetime.utcnow()
        session.add(existing)
    else:
        consent = ConsentRecordDB(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            consent_type="third_party",
            granted=False,
        )
        session.add(consent)

    session.commit()

    return {
        "success": True,
        "message": "You have opted out of the sale of personal data.",
        "opt_out_effective": True,
    }

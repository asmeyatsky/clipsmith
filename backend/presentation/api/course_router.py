from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional
from ...infrastructure.repositories.database import get_session
from .auth_router import get_current_user
from sqlmodel import Session, select
from datetime import datetime
import uuid

router = APIRouter(prefix="/api/courses", tags=["courses"])


# ==================== Course Endpoints ====================


@router.post("/")
def create_course(
    request_body: dict,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Create a new course."""
    from ...infrastructure.repositories.models import CourseDB

    title = request_body.get("title")
    description = request_body.get("description", "")
    price = request_body.get("price", 0.0)
    category = request_body.get("category", "general")

    if not title:
        raise HTTPException(status_code=400, detail="title is required")

    course = CourseDB(
        id=str(uuid.uuid4()),
        title=title,
        description=description,
        price=price,
        category=category,
        creator_id=current_user.id,
        status="draft",
    )
    session.add(course)
    session.commit()

    return {
        "success": True,
        "course": {
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "price": course.price,
            "category": course.category,
            "creator_id": course.creator_id,
            "status": course.status,
        },
    }


@router.get("/")
def list_courses(
    category: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
):
    """List available courses."""
    from ...infrastructure.repositories.models import CourseDB

    query = select(CourseDB).where(CourseDB.status == "published")
    if category:
        query = query.where(CourseDB.category == category)
    query = query.offset(offset).limit(limit)

    courses = session.exec(query).all()

    return {
        "success": True,
        "courses": [
            {
                "id": c.id,
                "title": c.title,
                "description": c.description,
                "price": c.price,
                "category": c.category,
                "creator_id": c.creator_id,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in courses
        ],
    }


@router.get("/enrolled")
def get_enrolled_courses(
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Get courses the current user is enrolled in."""
    from ...infrastructure.repositories.models import CourseDB, CourseEnrollmentDB

    enrollments = session.exec(
        select(CourseEnrollmentDB).where(
            CourseEnrollmentDB.user_id == current_user.id
        )
    ).all()

    courses = []
    for enrollment in enrollments:
        course = session.get(CourseDB, enrollment.course_id)
        if course:
            courses.append({
                "id": course.id,
                "title": course.title,
                "description": course.description,
                "price": course.price,
                "category": course.category,
                "enrolled_at": enrollment.enrolled_at.isoformat() if enrollment.enrolled_at else None,
                "progress": enrollment.progress_percentage,
            })

    return {"success": True, "courses": courses}


@router.get("/creator/{creator_id}")
def get_creator_courses(
    creator_id: str,
    session: Session = Depends(get_session),
):
    """Get courses created by a specific creator."""
    from ...infrastructure.repositories.models import CourseDB

    courses = session.exec(
        select(CourseDB).where(CourseDB.creator_id == creator_id)
    ).all()

    return {
        "success": True,
        "courses": [
            {
                "id": c.id,
                "title": c.title,
                "description": c.description,
                "price": c.price,
                "category": c.category,
                "status": c.status,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in courses
        ],
    }


@router.get("/{course_id}")
def get_course(
    course_id: str,
    session: Session = Depends(get_session),
):
    """Get a specific course with its lessons."""
    from ...infrastructure.repositories.models import CourseDB, CourseLessonDB

    course = session.get(CourseDB, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    lessons = session.exec(
        select(CourseLessonDB)
        .where(CourseLessonDB.course_id == course_id)
    ).all()

    return {
        "success": True,
        "course": {
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "price": course.price,
            "category": course.category,
            "creator_id": course.creator_id,
            "status": course.status,
            "lessons": [
                {
                    "id": l.id,
                    "title": l.title,
                    "description": l.description,
                    "video_id": l.video_id,
                    "position": l.position,
                    "is_free_preview": l.is_free_preview,
                }
                for l in lessons
            ],
        },
    }


@router.post("/{course_id}/lessons")
def add_lesson(
    course_id: str,
    request_body: dict,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Add a lesson to a course."""
    from ...infrastructure.repositories.models import CourseDB, CourseLessonDB

    course = session.get(CourseDB, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the course creator can add lessons")

    title = request_body.get("title")
    description = request_body.get("description", "")
    video_id = request_body.get("video_id")
    position = request_body.get("position", 0)
    is_free_preview = request_body.get("is_free_preview", False)

    if not title:
        raise HTTPException(status_code=400, detail="title is required")

    lesson = CourseLessonDB(
        id=str(uuid.uuid4()),
        course_id=course_id,
        title=title,
        description=description,
        video_id=video_id,
        position=position,
        is_free_preview=is_free_preview,
    )
    session.add(lesson)
    session.commit()

    return {
        "success": True,
        "lesson": {
            "id": lesson.id,
            "title": lesson.title,
            "position": lesson.position,
            "is_free_preview": lesson.is_free_preview,
        },
    }


@router.post("/{course_id}/enroll")
def enroll_in_course(
    course_id: str,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Enroll in a course."""
    from ...infrastructure.repositories.models import CourseDB, CourseEnrollmentDB

    course = session.get(CourseDB, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    existing = session.exec(
        select(CourseEnrollmentDB).where(
            CourseEnrollmentDB.course_id == course_id,
            CourseEnrollmentDB.user_id == current_user.id,
        )
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Already enrolled in this course")

    enrollment = CourseEnrollmentDB(
        id=str(uuid.uuid4()),
        course_id=course_id,
        user_id=current_user.id,
        progress_percentage=0.0,
    )
    session.add(enrollment)
    session.commit()

    return {"success": True, "message": "Enrolled in course", "enrollment_id": enrollment.id}


@router.put("/{course_id}/progress")
def update_lesson_progress(
    course_id: str,
    request_body: dict,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Update lesson progress for an enrolled course."""
    from ...infrastructure.repositories.models import CourseEnrollmentDB, LessonProgressDB

    enrollment = session.exec(
        select(CourseEnrollmentDB).where(
            CourseEnrollmentDB.course_id == course_id,
            CourseEnrollmentDB.user_id == current_user.id,
        )
    ).first()

    if not enrollment:
        raise HTTPException(status_code=404, detail="Not enrolled in this course")

    lesson_id = request_body.get("lesson_id")
    if not lesson_id:
        raise HTTPException(status_code=400, detail="lesson_id is required")

    existing_progress = session.exec(
        select(LessonProgressDB).where(
            LessonProgressDB.enrollment_id == enrollment.id,
            LessonProgressDB.lesson_id == lesson_id,
        )
    ).first()

    if existing_progress:
        existing_progress.completed = True
        existing_progress.completed_at = datetime.utcnow()
        session.add(existing_progress)
    else:
        progress = LessonProgressDB(
            id=str(uuid.uuid4()),
            enrollment_id=enrollment.id,
            lesson_id=lesson_id,
            completed=True,
            completed_at=datetime.utcnow(),
        )
        session.add(progress)

    session.commit()

    return {"success": True, "message": "Lesson progress updated"}


# ==================== Subscription Tier Endpoints ====================


@router.post("/subscription-tiers")
def create_subscription_tier(
    request_body: dict,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Create a subscription tier for the creator."""
    from ...infrastructure.repositories.models import SubscriptionTierDB

    name = request_body.get("name")
    price = request_body.get("price")
    interval = request_body.get("interval", "month")
    description = request_body.get("description", "")
    benefits = request_body.get("benefits", "")

    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    if price is None:
        raise HTTPException(status_code=400, detail="price is required")

    tier = SubscriptionTierDB(
        id=str(uuid.uuid4()),
        creator_id=current_user.id,
        name=name,
        price=price,
        interval=interval,
        description=description,
        benefits=benefits,
    )
    session.add(tier)
    session.commit()

    return {
        "success": True,
        "tier": {
            "id": tier.id,
            "name": tier.name,
            "price": tier.price,
            "interval": tier.interval,
            "description": tier.description,
            "benefits": tier.benefits,
        },
    }


@router.get("/subscription-tiers/{creator_id}")
def get_subscription_tiers(
    creator_id: str,
    session: Session = Depends(get_session),
):
    """Get subscription tiers for a creator."""
    from ...infrastructure.repositories.models import SubscriptionTierDB

    tiers = session.exec(
        select(SubscriptionTierDB).where(
            SubscriptionTierDB.creator_id == creator_id
        )
    ).all()

    return {
        "success": True,
        "tiers": [
            {
                "id": t.id,
                "name": t.name,
                "price": t.price,
                "interval": t.interval,
                "description": t.description,
                "benefits": t.benefits,
            }
            for t in tiers
        ],
    }


# ==================== Creator Fund Endpoints ====================


@router.post("/creator-fund/apply")
def apply_for_creator_fund(
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Apply for the creator fund."""
    from ...infrastructure.repositories.models import CreatorFundEligibilityDB

    existing = session.exec(
        select(CreatorFundEligibilityDB).where(
            CreatorFundEligibilityDB.user_id == current_user.id,
            CreatorFundEligibilityDB.status != "rejected",
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="You already have an active or pending creator fund application",
        )

    application = CreatorFundEligibilityDB(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        status="pending",
    )
    session.add(application)
    session.commit()

    return {
        "success": True,
        "application": {
            "id": application.id,
            "status": application.status,
            "applied_at": application.applied_at.isoformat() if application.applied_at else None,
        },
    }


@router.get("/creator-fund/status")
def get_creator_fund_status(
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Get creator fund application status."""
    from ...infrastructure.repositories.models import CreatorFundEligibilityDB

    application = session.exec(
        select(CreatorFundEligibilityDB).where(
            CreatorFundEligibilityDB.user_id == current_user.id
        )
    ).first()

    if not application:
        return {"success": True, "has_application": False, "status": None}

    return {
        "success": True,
        "has_application": True,
        "status": application.status,
        "applied_at": application.applied_at.isoformat() if application.applied_at else None,
    }

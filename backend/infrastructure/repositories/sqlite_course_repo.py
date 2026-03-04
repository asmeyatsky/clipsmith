from typing import List, Optional
from datetime import datetime
from sqlmodel import Session, select, func
from sqlalchemy import text
from .models import (
    CourseDB,
    CourseLessonDB,
    CourseEnrollmentDB,
    LessonProgressDB,
    SubscriptionTierDB,
    CreatorFundEligibilityDB,
)


class SQLiteCourseRepository:
    def __init__(self, session: Session):
        self.session = session

    # ---- Course operations ----

    def save_course(self, course: CourseDB) -> CourseDB:
        course = self.session.merge(course)
        self.session.commit()
        self.session.refresh(course)
        return course

    def get_course(self, course_id: str) -> Optional[CourseDB]:
        return self.session.get(CourseDB, course_id)

    def get_courses_by_creator(self, creator_id: str) -> List[CourseDB]:
        statement = (
            select(CourseDB)
            .where(CourseDB.creator_id == creator_id)
            .order_by(CourseDB.created_at.desc())
        )
        return list(self.session.exec(statement).all())

    def get_published_courses(
        self, limit: int = 20, offset: int = 0
    ) -> List[CourseDB]:
        statement = (
            select(CourseDB)
            .where(CourseDB.status == "published")
            .order_by(CourseDB.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def delete_course(self, course_id: str) -> bool:
        course = self.session.get(CourseDB, course_id)
        if course:
            self.session.delete(course)
            self.session.commit()
            return True
        return False

    # ---- Lesson operations ----

    def save_lesson(self, lesson: CourseLessonDB) -> CourseLessonDB:
        lesson = self.session.merge(lesson)
        self.session.commit()
        self.session.refresh(lesson)
        return lesson

    def save_course_lesson(self, lesson: CourseLessonDB) -> CourseLessonDB:
        """Alias used by CourseService.add_lesson."""
        return self.save_lesson(lesson)

    def get_lesson(self, lesson_id: str) -> Optional[CourseLessonDB]:
        return self.session.get(CourseLessonDB, lesson_id)

    def get_course_lessons(self, course_id: str) -> List[CourseLessonDB]:
        statement = (
            select(CourseLessonDB)
            .where(CourseLessonDB.course_id == course_id)
            .order_by(CourseLessonDB.position.asc())
        )
        return list(self.session.exec(statement).all())

    def delete_lesson(self, lesson_id: str) -> bool:
        lesson = self.session.get(CourseLessonDB, lesson_id)
        if lesson:
            self.session.delete(lesson)
            self.session.commit()
            return True
        return False

    def count_course_lessons(self, course_id: str) -> int:
        statement = (
            select(func.count())
            .select_from(CourseLessonDB)
            .where(CourseLessonDB.course_id == course_id)
        )
        return self.session.exec(statement).one()

    # ---- Enrollment operations ----

    def save_enrollment(self, enrollment: CourseEnrollmentDB) -> CourseEnrollmentDB:
        enrollment = self.session.merge(enrollment)
        self.session.commit()
        self.session.refresh(enrollment)
        return enrollment

    def get_enrollment(
        self, course_id: str, user_id: str
    ) -> Optional[CourseEnrollmentDB]:
        statement = select(CourseEnrollmentDB).where(
            CourseEnrollmentDB.course_id == course_id,
            CourseEnrollmentDB.user_id == user_id,
        )
        return self.session.exec(statement).first()

    def get_enrollments_by_user(self, user_id: str) -> List[CourseEnrollmentDB]:
        statement = (
            select(CourseEnrollmentDB)
            .where(CourseEnrollmentDB.user_id == user_id)
            .order_by(CourseEnrollmentDB.enrolled_at.desc())
        )
        return list(self.session.exec(statement).all())

    def is_user_enrolled(self, course_id: str, user_id: str) -> bool:
        return self.get_enrollment(course_id, user_id) is not None

    def increment_course_enrollment_count(self, course_id: str) -> None:
        self.session.execute(
            text(
                "UPDATE coursedb SET enrollment_count = COALESCE(enrollment_count, 0) + 1 WHERE id = :cid"
            ),
            {"cid": course_id},
        )
        self.session.commit()

    def mark_lesson_completed(self, enrollment_id: str, lesson_id: str) -> None:
        # Check if progress record already exists
        statement = select(LessonProgressDB).where(
            LessonProgressDB.enrollment_id == enrollment_id,
            LessonProgressDB.lesson_id == lesson_id,
        )
        existing = self.session.exec(statement).first()
        if existing:
            if not existing.completed:
                existing.completed = True
                existing.completed_at = datetime.utcnow()
                self.session.add(existing)
                self.session.commit()
        else:
            progress = LessonProgressDB(
                enrollment_id=enrollment_id,
                lesson_id=lesson_id,
                completed=True,
                completed_at=datetime.utcnow(),
            )
            self.session.add(progress)
            self.session.commit()

    def count_completed_lessons(self, enrollment_id: str) -> int:
        statement = (
            select(func.count())
            .select_from(LessonProgressDB)
            .where(
                LessonProgressDB.enrollment_id == enrollment_id,
                LessonProgressDB.completed == True,
            )
        )
        return self.session.exec(statement).one()

    def update_enrollment_progress(
        self, enrollment_id: str, progress_percentage: float
    ) -> None:
        enrollment = self.session.get(CourseEnrollmentDB, enrollment_id)
        if enrollment:
            enrollment.progress_percentage = progress_percentage
            self.session.add(enrollment)
            self.session.commit()

    def complete_enrollment(
        self, enrollment_id: str, completed_at: datetime
    ) -> None:
        enrollment = self.session.get(CourseEnrollmentDB, enrollment_id)
        if enrollment:
            enrollment.status = "completed"
            enrollment.completed_at = completed_at
            self.session.add(enrollment)
            self.session.commit()

    def check_course_purchase(self, course_id: str, user_id: str) -> bool:
        """Check if a user has purchased a course.

        For now this always returns True as the payment integration
        is handled elsewhere. A real implementation would check
        the transactions table.
        """
        return True

    # ---- Subscription Tier operations ----

    def save_subscription_tier(self, tier: SubscriptionTierDB) -> SubscriptionTierDB:
        tier = self.session.merge(tier)
        self.session.commit()
        self.session.refresh(tier)
        return tier

    def get_subscription_tiers_by_creator(
        self, creator_id: str
    ) -> List[SubscriptionTierDB]:
        statement = (
            select(SubscriptionTierDB)
            .where(SubscriptionTierDB.creator_id == creator_id)
            .where(SubscriptionTierDB.is_active == True)
            .order_by(SubscriptionTierDB.price.asc())
        )
        return list(self.session.exec(statement).all())

    def delete_subscription_tier(self, tier_id: str) -> bool:
        tier = self.session.get(SubscriptionTierDB, tier_id)
        if tier:
            tier.is_active = False
            self.session.add(tier)
            self.session.commit()
            return True
        return False

    # ---- Creator Fund Eligibility operations ----

    def get_creator_fund_eligibility(
        self, user_id: str
    ) -> Optional[CreatorFundEligibilityDB]:
        statement = select(CreatorFundEligibilityDB).where(
            CreatorFundEligibilityDB.user_id == user_id
        )
        return self.session.exec(statement).first()

    def save_creator_fund_eligibility(
        self, eligibility: CreatorFundEligibilityDB
    ) -> CreatorFundEligibilityDB:
        eligibility = self.session.merge(eligibility)
        self.session.commit()
        self.session.refresh(eligibility)
        return eligibility

    def update_creator_fund_eligibility(
        self,
        user_id: str,
        follower_count: int = None,
        monthly_views: int = None,
        is_eligible: bool = None,
    ) -> None:
        eligibility = self.get_creator_fund_eligibility(user_id)
        if eligibility:
            if follower_count is not None:
                eligibility.follower_count = follower_count
            if monthly_views is not None:
                eligibility.monthly_views = monthly_views
            if is_eligible is not None:
                eligibility.is_eligible = is_eligible
                if is_eligible and eligibility.status == "pending":
                    eligibility.status = "approved"
                    eligibility.approved_at = datetime.utcnow()
            self.session.add(eligibility)
            self.session.commit()

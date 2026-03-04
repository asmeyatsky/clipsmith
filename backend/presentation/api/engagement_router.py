from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional
from ...infrastructure.repositories.database import get_session
from .auth_router import get_current_user
from sqlmodel import Session, select
from datetime import datetime
import uuid

router = APIRouter(prefix="/api/engagement", tags=["engagement"])


# ==================== Poll Endpoints ====================


@router.post("/polls")
def create_poll(
    request_body: dict,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Create a poll on a video."""
    from ...infrastructure.repositories.models import PollDB, PollOptionDB

    video_id = request_body.get("video_id")
    question = request_body.get("question")
    options = request_body.get("options", [])
    poll_type = request_body.get("poll_type", "multiple_choice")
    correct_answer = request_body.get("correct_answer")
    start_time = request_body.get("start_time")
    end_time = request_body.get("end_time")

    if not video_id:
        raise HTTPException(status_code=400, detail="video_id is required")
    if not question:
        raise HTTPException(status_code=400, detail="question is required")
    if len(options) < 2:
        raise HTTPException(status_code=400, detail="At least 2 options are required")

    poll = PollDB(
        id=str(uuid.uuid4()),
        video_id=video_id,
        creator_id=current_user.id,
        question=question,
        poll_type=poll_type,
        correct_answer=correct_answer,
        start_time=start_time,
        end_time=end_time,
    )
    session.add(poll)
    session.flush()

    poll_options = []
    for idx, option_text in enumerate(options):
        option = PollOptionDB(
            id=str(uuid.uuid4()),
            poll_id=poll.id,
            text=option_text,
            position=idx,
        )
        session.add(option)
        poll_options.append({"id": option.id, "text": option_text, "position": idx})

    session.commit()

    return {
        "success": True,
        "poll": {
            "id": poll.id,
            "video_id": poll.video_id,
            "question": poll.question,
            "poll_type": poll.poll_type,
            "options": poll_options,
        },
    }


@router.post("/polls/{poll_id}/vote")
def vote_on_poll(
    poll_id: str,
    request_body: dict,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Vote on a poll option."""
    from ...infrastructure.repositories.models import PollDB, PollVoteDB

    poll = session.get(PollDB, poll_id)
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")

    option_id = request_body.get("option_id")
    if not option_id:
        raise HTTPException(status_code=400, detail="option_id is required")

    # Check if already voted
    existing = session.exec(
        select(PollVoteDB).where(
            PollVoteDB.poll_id == poll_id,
            PollVoteDB.user_id == current_user.id,
        )
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Already voted on this poll")

    vote = PollVoteDB(
        id=str(uuid.uuid4()),
        poll_id=poll_id,
        option_id=option_id,
        user_id=current_user.id,
    )
    session.add(vote)
    session.commit()

    return {"success": True, "message": "Vote recorded"}


@router.get("/polls/{poll_id}")
def get_poll(
    poll_id: str,
    session: Session = Depends(get_session),
):
    """Get poll details with vote counts."""
    from ...infrastructure.repositories.models import PollDB, PollOptionDB, PollVoteDB

    poll = session.get(PollDB, poll_id)
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")

    options = session.exec(
        select(PollOptionDB).where(PollOptionDB.poll_id == poll_id)
    ).all()

    option_results = []
    for opt in options:
        vote_count = len(
            session.exec(
                select(PollVoteDB).where(PollVoteDB.option_id == opt.id)
            ).all()
        )
        option_results.append({
            "id": opt.id,
            "text": opt.text,
            "position": opt.position,
            "vote_count": vote_count,
        })

    return {
        "success": True,
        "poll": {
            "id": poll.id,
            "video_id": poll.video_id,
            "question": poll.question,
            "poll_type": poll.poll_type,
            "options": option_results,
            "created_at": poll.created_at.isoformat() if poll.created_at else None,
        },
    }


@router.get("/videos/{video_id}/polls")
def get_polls_for_video(
    video_id: str,
    session: Session = Depends(get_session),
):
    """Get all polls for a video."""
    from ...infrastructure.repositories.models import PollDB

    polls = session.exec(
        select(PollDB).where(PollDB.video_id == video_id)
    ).all()

    return {
        "success": True,
        "polls": [
            {
                "id": p.id,
                "question": p.question,
                "poll_type": p.poll_type,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in polls
        ],
    }


# ==================== Chapter Marker Endpoints ====================


@router.post("/videos/{video_id}/chapters")
def create_chapter_marker(
    video_id: str,
    request_body: dict,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Create a chapter marker on a video."""
    from ...infrastructure.repositories.models import ChapterMarkerDB

    title = request_body.get("title")
    start_time = request_body.get("start_time")
    end_time = request_body.get("end_time")

    if not title:
        raise HTTPException(status_code=400, detail="title is required")
    if start_time is None:
        raise HTTPException(status_code=400, detail="start_time is required")

    marker = ChapterMarkerDB(
        id=str(uuid.uuid4()),
        video_id=video_id,
        title=title,
        start_time=start_time,
        end_time=end_time,
        creator_id=current_user.id,
    )
    session.add(marker)
    session.commit()

    return {
        "success": True,
        "chapter": {
            "id": marker.id,
            "video_id": marker.video_id,
            "title": marker.title,
            "start_time": marker.start_time,
            "end_time": marker.end_time,
        },
    }


@router.get("/videos/{video_id}/chapters")
def get_chapter_markers(
    video_id: str,
    session: Session = Depends(get_session),
):
    """Get all chapter markers for a video."""
    from ...infrastructure.repositories.models import ChapterMarkerDB

    markers = session.exec(
        select(ChapterMarkerDB)
        .where(ChapterMarkerDB.video_id == video_id)
    ).all()

    return {
        "success": True,
        "chapters": [
            {
                "id": m.id,
                "title": m.title,
                "start_time": m.start_time,
                "end_time": m.end_time,
            }
            for m in markers
        ],
    }


# ==================== Product Tag Endpoints ====================


@router.post("/videos/{video_id}/product-tags")
def add_product_tag(
    video_id: str,
    request_body: dict,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Add a product tag to a video."""
    from ...infrastructure.repositories.models import ProductTagDB

    product_name = request_body.get("product_name")
    product_url = request_body.get("product_url")
    price = request_body.get("price")
    currency = request_body.get("currency", "USD")
    timestamp = request_body.get("timestamp")

    if not product_name:
        raise HTTPException(status_code=400, detail="product_name is required")

    tag = ProductTagDB(
        id=str(uuid.uuid4()),
        video_id=video_id,
        product_name=product_name,
        product_url=product_url,
        price=price,
        currency=currency,
        timestamp=timestamp,
        creator_id=current_user.id,
    )
    session.add(tag)
    session.commit()

    return {
        "success": True,
        "product_tag": {
            "id": tag.id,
            "video_id": tag.video_id,
            "product_name": tag.product_name,
            "product_url": tag.product_url,
            "price": tag.price,
        },
    }


@router.get("/videos/{video_id}/product-tags")
def get_product_tags(
    video_id: str,
    session: Session = Depends(get_session),
):
    """Get all product tags for a video."""
    from ...infrastructure.repositories.models import ProductTagDB

    tags = session.exec(
        select(ProductTagDB).where(ProductTagDB.video_id == video_id)
    ).all()

    return {
        "success": True,
        "product_tags": [
            {
                "id": t.id,
                "product_name": t.product_name,
                "product_url": t.product_url,
                "price": t.price,
                "currency": t.currency,
                "click_count": t.click_count,
            }
            for t in tags
        ],
    }


@router.post("/product-tags/{tag_id}/click")
def track_product_click(
    tag_id: str,
    session: Session = Depends(get_session),
):
    """Track a click on a product tag."""
    from ...infrastructure.repositories.models import ProductTagDB

    tag = session.get(ProductTagDB, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Product tag not found")

    tag.click_count = (tag.click_count or 0) + 1
    session.add(tag)
    session.commit()

    return {"success": True, "click_count": tag.click_count}


# ==================== Video Link Endpoints ====================


@router.post("/videos/{video_id}/links")
def add_video_link(
    video_id: str,
    request_body: dict,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Add a link to a video."""
    from ...infrastructure.repositories.models import VideoLinkDB

    title = request_body.get("title")
    url = request_body.get("url")
    icon = request_body.get("icon")

    if not title:
        raise HTTPException(status_code=400, detail="title is required")
    if not url:
        raise HTTPException(status_code=400, detail="url is required")

    link = VideoLinkDB(
        id=str(uuid.uuid4()),
        video_id=video_id,
        title=title,
        url=url,
        icon=icon,
        creator_id=current_user.id,
    )
    session.add(link)
    session.commit()

    return {
        "success": True,
        "link": {
            "id": link.id,
            "video_id": link.video_id,
            "title": link.title,
            "url": link.url,
            "icon": link.icon,
        },
    }


@router.get("/videos/{video_id}/links")
def get_video_links(
    video_id: str,
    session: Session = Depends(get_session),
):
    """Get all links for a video."""
    from ...infrastructure.repositories.models import VideoLinkDB

    links = session.exec(
        select(VideoLinkDB).where(VideoLinkDB.video_id == video_id)
    ).all()

    return {
        "success": True,
        "links": [
            {
                "id": l.id,
                "title": l.title,
                "url": l.url,
                "icon": l.icon,
                "click_count": l.click_count,
            }
            for l in links
        ],
    }


@router.post("/links/{link_id}/click")
def track_link_click(
    link_id: str,
    session: Session = Depends(get_session),
):
    """Track a click on a video link."""
    from ...infrastructure.repositories.models import VideoLinkDB

    link = session.get(VideoLinkDB, link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    link.click_count = (link.click_count or 0) + 1
    session.add(link)
    session.commit()

    return {"success": True, "click_count": link.click_count}


# ==================== Challenge Endpoints ====================


@router.post("/challenges")
def create_challenge(
    request_body: dict,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Create a new challenge."""
    from ...infrastructure.repositories.models import ChallengeDB

    hashtag_id = request_body.get("hashtag_id")
    title = request_body.get("title")
    description = request_body.get("description", "")
    rules = request_body.get("rules", "")
    start_date = request_body.get("start_date")
    end_date = request_body.get("end_date")
    prize_description = request_body.get("prize_description")

    if not title:
        raise HTTPException(status_code=400, detail="title is required")

    challenge = ChallengeDB(
        id=str(uuid.uuid4()),
        hashtag_id=hashtag_id,
        title=title,
        description=description,
        rules=rules,
        start_date=start_date,
        end_date=end_date,
        prize_description=prize_description,
        creator_id=current_user.id,
        status="active",
    )
    session.add(challenge)
    session.commit()

    return {
        "success": True,
        "challenge": {
            "id": challenge.id,
            "title": challenge.title,
            "description": challenge.description,
            "start_date": challenge.start_date,
            "end_date": challenge.end_date,
            "status": challenge.status,
        },
    }


@router.post("/challenges/{challenge_id}/join")
def join_challenge(
    challenge_id: str,
    request_body: dict,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Join a challenge with a video submission."""
    from ...infrastructure.repositories.models import ChallengeDB, ChallengeParticipantDB

    challenge = session.get(ChallengeDB, challenge_id)
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    if challenge.status != "active":
        raise HTTPException(status_code=400, detail="Challenge is not active")

    video_id = request_body.get("video_id")
    if not video_id:
        raise HTTPException(status_code=400, detail="video_id is required")

    existing = session.exec(
        select(ChallengeParticipantDB).where(
            ChallengeParticipantDB.challenge_id == challenge_id,
            ChallengeParticipantDB.user_id == current_user.id,
        )
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Already joined this challenge")

    entry = ChallengeParticipantDB(
        id=str(uuid.uuid4()),
        challenge_id=challenge_id,
        user_id=current_user.id,
        video_id=video_id,
    )
    session.add(entry)
    session.commit()

    return {"success": True, "message": "Joined challenge", "entry_id": entry.id}


@router.get("/challenges")
def get_active_challenges(
    limit: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    """Get active challenges."""
    from ...infrastructure.repositories.models import ChallengeDB

    challenges = session.exec(
        select(ChallengeDB)
        .where(ChallengeDB.status == "active")
        .limit(limit)
    ).all()

    return {
        "success": True,
        "challenges": [
            {
                "id": c.id,
                "title": c.title,
                "description": c.description,
                "start_date": c.start_date,
                "end_date": c.end_date,
                "prize_description": c.prize_description,
                "creator_id": c.creator_id,
            }
            for c in challenges
        ],
    }


# ==================== Badge Endpoints ====================


@router.get("/users/{user_id}/badges")
def get_user_badges(
    user_id: str,
    session: Session = Depends(get_session),
):
    """Get badges earned by a user."""
    from ...infrastructure.repositories.models import UserBadgeDB, BadgeDB

    user_badges = session.exec(
        select(UserBadgeDB).where(UserBadgeDB.user_id == user_id)
    ).all()

    badges = []
    for ub in user_badges:
        badge = session.get(BadgeDB, ub.badge_id)
        badges.append({
            "id": ub.id,
            "badge_type": badge.badge_type if badge else None,
            "badge_name": badge.name if badge else None,
            "description": badge.description if badge else None,
            "earned_at": ub.earned_at.isoformat() if ub.earned_at else None,
        })

    return {
        "success": True,
        "badges": badges,
    }

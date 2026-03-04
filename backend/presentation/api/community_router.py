from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from typing import Optional
from ...infrastructure.repositories.database import get_session
from .auth_router import get_current_user
from sqlmodel import Session, select
from datetime import datetime
import uuid

router = APIRouter(prefix="/api/community", tags=["community"])


# ==================== Circle Endpoints ====================


@router.post("/circles")
def create_circle(
    request_body: dict,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Create a new circle for organizing close connections."""
    name = request_body.get("name")
    description = request_body.get("description", "")

    if not name:
        raise HTTPException(status_code=400, detail="Circle name is required")

    circle = {
        "id": str(uuid.uuid4()),
        "name": name,
        "description": description,
        "user_id": current_user.id,
        "created_at": datetime.utcnow().isoformat(),
    }

    # Store circle in session (placeholder until model is created)
    from ...infrastructure.repositories.models import CircleDB

    db_circle = CircleDB(
        id=circle["id"],
        name=name,
        description=description,
        user_id=current_user.id,
    )
    session.add(db_circle)
    session.commit()

    return {"success": True, "circle": circle}


@router.get("/circles")
def get_user_circles(
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Get all circles owned by the current user."""
    from ...infrastructure.repositories.models import CircleDB

    circles = session.exec(
        select(CircleDB).where(CircleDB.user_id == current_user.id)
    ).all()

    return {
        "success": True,
        "circles": [
            {
                "id": c.id,
                "name": c.name,
                "description": c.description,
                "user_id": c.user_id,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in circles
        ],
    }


@router.post("/circles/{circle_id}/members")
def add_to_circle(
    circle_id: str,
    request_body: dict,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Add a member to a circle."""
    from ...infrastructure.repositories.models import CircleDB, CircleMemberDB

    circle = session.get(CircleDB, circle_id)
    if not circle:
        raise HTTPException(status_code=404, detail="Circle not found")

    if circle.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the circle owner can add members")

    member_id = request_body.get("member_id")
    if not member_id:
        raise HTTPException(status_code=400, detail="member_id is required")

    # Check if already a member
    existing = session.exec(
        select(CircleMemberDB).where(
            CircleMemberDB.circle_id == circle_id,
            CircleMemberDB.user_id == member_id,
        )
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="User is already a member of this circle")

    membership = CircleMemberDB(
        id=str(uuid.uuid4()),
        circle_id=circle_id,
        user_id=member_id,
    )
    session.add(membership)
    session.commit()

    return {"success": True, "message": "Member added to circle"}


@router.delete("/circles/{circle_id}/members/{member_id}")
def remove_from_circle(
    circle_id: str,
    member_id: str,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Remove a member from a circle."""
    from ...infrastructure.repositories.models import CircleDB, CircleMemberDB

    circle = session.get(CircleDB, circle_id)
    if not circle:
        raise HTTPException(status_code=404, detail="Circle not found")

    if circle.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the circle owner can remove members")

    membership = session.exec(
        select(CircleMemberDB).where(
            CircleMemberDB.circle_id == circle_id,
            CircleMemberDB.user_id == member_id,
        )
    ).first()

    if not membership:
        raise HTTPException(status_code=404, detail="Member not found in circle")

    session.delete(membership)
    session.commit()

    return {"success": True, "message": "Member removed from circle"}


@router.get("/circles/{circle_id}/members")
def get_circle_members(
    circle_id: str,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Get all members of a circle."""
    from ...infrastructure.repositories.models import CircleDB, CircleMemberDB

    circle = session.get(CircleDB, circle_id)
    if not circle:
        raise HTTPException(status_code=404, detail="Circle not found")

    members = session.exec(
        select(CircleMemberDB).where(CircleMemberDB.circle_id == circle_id)
    ).all()

    return {
        "success": True,
        "members": [
            {
                "id": m.id,
                "user_id": m.user_id,
                "joined_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in members
        ],
    }


# ==================== Group Endpoints ====================


@router.post("/groups")
def create_group(
    request_body: dict,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Create a new community group."""
    from ...infrastructure.repositories.models import CommunityGroupDB

    name = request_body.get("name")
    description = request_body.get("description", "")
    rules = request_body.get("rules", "")
    is_public = request_body.get("is_public", True)

    if not name:
        raise HTTPException(status_code=400, detail="Group name is required")

    group = CommunityGroupDB(
        id=str(uuid.uuid4()),
        name=name,
        description=description,
        rules=rules,
        is_public=is_public,
        creator_id=current_user.id,
    )
    session.add(group)
    session.commit()

    return {
        "success": True,
        "group": {
            "id": group.id,
            "name": group.name,
            "description": group.description,
            "is_public": group.is_public,
            "creator_id": group.creator_id,
        },
    }


@router.get("/groups")
def list_groups(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
):
    """List public community groups."""
    from ...infrastructure.repositories.models import CommunityGroupDB

    groups = session.exec(
        select(CommunityGroupDB)
        .where(CommunityGroupDB.is_public == True)
        .offset(offset)
        .limit(limit)
    ).all()

    return {
        "success": True,
        "groups": [
            {
                "id": g.id,
                "name": g.name,
                "description": g.description,
                "is_public": g.is_public,
                "creator_id": g.creator_id,
                "created_at": g.created_at.isoformat() if g.created_at else None,
            }
            for g in groups
        ],
    }


@router.get("/groups/{group_id}")
def get_group(
    group_id: str,
    session: Session = Depends(get_session),
):
    """Get details of a specific group."""
    from ...infrastructure.repositories.models import CommunityGroupDB

    group = session.get(CommunityGroupDB, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    return {
        "success": True,
        "group": {
            "id": group.id,
            "name": group.name,
            "description": group.description,
            "rules": group.rules,
            "is_public": group.is_public,
            "creator_id": group.creator_id,
            "created_at": group.created_at.isoformat() if group.created_at else None,
        },
    }


@router.post("/groups/{group_id}/join")
def join_group(
    group_id: str,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Join a community group."""
    from ...infrastructure.repositories.models import CommunityGroupDB, CommunityMemberDB

    group = session.get(CommunityGroupDB, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    existing = session.exec(
        select(CommunityMemberDB).where(
            CommunityMemberDB.group_id == group_id,
            CommunityMemberDB.user_id == current_user.id,
        )
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Already a member of this group")

    membership = CommunityMemberDB(
        id=str(uuid.uuid4()),
        group_id=group_id,
        user_id=current_user.id,
        role="member",
    )
    session.add(membership)
    session.commit()

    return {"success": True, "message": "Joined group successfully"}


@router.post("/groups/{group_id}/leave")
def leave_group(
    group_id: str,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Leave a community group."""
    from ...infrastructure.repositories.models import CommunityMemberDB

    membership = session.exec(
        select(CommunityMemberDB).where(
            CommunityMemberDB.group_id == group_id,
            CommunityMemberDB.user_id == current_user.id,
        )
    ).first()

    if not membership:
        raise HTTPException(status_code=404, detail="Not a member of this group")

    session.delete(membership)
    session.commit()

    return {"success": True, "message": "Left group successfully"}


@router.post("/groups/{group_id}/posts")
def create_discussion_post(
    group_id: str,
    request_body: dict,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Create a discussion post in a group."""
    from ...infrastructure.repositories.models import CommunityGroupDB, CommunityMemberDB, DiscussionPostDB

    group = session.get(CommunityGroupDB, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Verify membership
    membership = session.exec(
        select(CommunityMemberDB).where(
            CommunityMemberDB.group_id == group_id,
            CommunityMemberDB.user_id == current_user.id,
        )
    ).first()

    if not membership and group.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Must be a group member to post")

    content = request_body.get("content")
    parent_id = request_body.get("parent_id")

    if not content:
        raise HTTPException(status_code=400, detail="Content is required")

    post = DiscussionPostDB(
        id=str(uuid.uuid4()),
        group_id=group_id,
        user_id=current_user.id,
        content=content,
        parent_id=parent_id,
    )
    session.add(post)
    session.commit()

    return {
        "success": True,
        "post": {
            "id": post.id,
            "group_id": post.group_id,
            "user_id": post.user_id,
            "content": post.content,
            "parent_id": post.parent_id,
            "created_at": post.created_at.isoformat() if post.created_at else None,
        },
    }


@router.get("/groups/{group_id}/posts")
def get_discussion_posts(
    group_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
):
    """Get discussion posts for a group."""
    from ...infrastructure.repositories.models import CommunityGroupDB, DiscussionPostDB

    group = session.get(CommunityGroupDB, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    posts = session.exec(
        select(DiscussionPostDB)
        .where(DiscussionPostDB.group_id == group_id)
        .offset(offset)
        .limit(limit)
    ).all()

    return {
        "success": True,
        "posts": [
            {
                "id": p.id,
                "group_id": p.group_id,
                "user_id": p.user_id,
                "content": p.content,
                "parent_id": p.parent_id,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in posts
        ],
    }


# ==================== Event Endpoints ====================


@router.post("/events")
def create_event(
    request_body: dict,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Create a community event."""
    from ...infrastructure.repositories.models import EventDB

    title = request_body.get("title")
    description = request_body.get("description", "")
    event_type = request_body.get("event_type", "general")
    start_time = request_body.get("start_time")
    end_time = request_body.get("end_time")
    location = request_body.get("location")
    max_attendees = request_body.get("max_attendees")
    group_id = request_body.get("group_id")

    if not title:
        raise HTTPException(status_code=400, detail="Event title is required")
    if not start_time:
        raise HTTPException(status_code=400, detail="Start time is required")

    event = EventDB(
        id=str(uuid.uuid4()),
        title=title,
        description=description,
        event_type=event_type,
        start_time=start_time,
        end_time=end_time,
        location=location,
        max_attendees=max_attendees,
        group_id=group_id,
        creator_id=current_user.id,
    )
    session.add(event)
    session.commit()

    return {
        "success": True,
        "event": {
            "id": event.id,
            "title": event.title,
            "event_type": event.event_type,
            "start_time": event.start_time,
            "end_time": event.end_time,
            "creator_id": event.creator_id,
        },
    }


@router.get("/events")
def get_events(
    group_id: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    """Get community events, optionally filtered by group."""
    from ...infrastructure.repositories.models import EventDB

    query = select(EventDB)
    if group_id:
        query = query.where(EventDB.group_id == group_id)
    query = query.limit(limit)

    events = session.exec(query).all()

    return {
        "success": True,
        "events": [
            {
                "id": e.id,
                "title": e.title,
                "description": e.description,
                "event_type": e.event_type,
                "start_time": e.start_time,
                "end_time": e.end_time,
                "location": e.location,
                "max_attendees": e.max_attendees,
                "group_id": e.group_id,
                "creator_id": e.creator_id,
            }
            for e in events
        ],
    }


@router.post("/events/{event_id}/rsvp")
def rsvp_event(
    event_id: str,
    request_body: dict,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """RSVP to a community event."""
    from ...infrastructure.repositories.models import EventDB, EventAttendeeDB

    event = session.get(EventDB, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    rsvp_status = request_body.get("rsvp_status", "attending")
    if rsvp_status not in ("attending", "maybe", "not_attending"):
        raise HTTPException(status_code=400, detail="Invalid RSVP status")

    # Check for existing RSVP
    existing = session.exec(
        select(EventAttendeeDB).where(
            EventAttendeeDB.event_id == event_id,
            EventAttendeeDB.user_id == current_user.id,
        )
    ).first()

    if existing:
        existing.rsvp_status = rsvp_status
        session.add(existing)
    else:
        rsvp = EventAttendeeDB(
            id=str(uuid.uuid4()),
            event_id=event_id,
            user_id=current_user.id,
            rsvp_status=rsvp_status,
        )
        session.add(rsvp)

    session.commit()

    return {"success": True, "rsvp_status": rsvp_status}

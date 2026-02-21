import os
from typing import Optional


def get_media_domain() -> Optional[str]:
    """Get the media domain for serving user content.

    In production, this should be a separate domain (e.g., cdn.clipsmith.com)
    to prevent XSS attacks from user-uploaded content.
    """
    return os.getenv("MEDIA_DOMAIN")


def get_media_url(path: str) -> str:
    """Generate the full URL for media content.

    Args:
        path: The relative path to the media file (e.g., 'videos/abc123.mp4')

    Returns:
        The full URL to the media file
    """
    media_domain = get_media_domain()

    if media_domain:
        return f"{media_domain}/{path}"

    # Fall back to API URL for development
    api_url = os.getenv("NEXT_PUBLIC_API_URL", "http://localhost:8000")
    return f"{api_url}/{path}"


def should_serve_from_cdn() -> bool:
    """Check if media should be served from a CDN."""
    return get_media_domain() is not None

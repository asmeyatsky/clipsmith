import bleach
from typing import Optional


def sanitize_input(dirty: str) -> str:
    """Sanitize user input by stripping HTML tags."""
    return bleach.clean(dirty, tags=[], strip=True)


def sanitize_html(dirty: str, allowed_tags: Optional[list] = None) -> str:
    """Sanitize HTML content with optional allowed tags."""
    if allowed_tags is None:
        allowed_tags = []
    return bleach.clean(dirty, tags=allowed_tags, strip=True)


MAX_TITLE_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 5000
MAX_COMMENT_LENGTH = 2000
MAX_USERNAME_LENGTH = 50

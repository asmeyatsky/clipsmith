import re
from typing import List, Set
from ...domain.entities.hashtag import Hashtag
from ...domain.ports.repository_ports import HashtagRepositoryPort


class HashtagService:
    """Service for extracting and managing hashtags."""

    def __init__(self, hashtag_repo: HashtagRepositoryPort):
        self.hashtag_repo = hashtag_repo

    def extract_hashtags(self, text: str) -> List[str]:
        """
        Extract hashtags from text.

        Supports:
        - #hashtag
        - #camelpascalcase
        - #snake_case
        - Multiple per text: "Check out #video and #editing"
        """
        if not text:
            return []

        # Regex pattern to match hashtags
        # Matches # followed by word characters, spaces, or underscores
        hashtag_pattern = r"#([A-Za-z0-9_]+)"
        matches = re.findall(hashtag_pattern, text)

        # Normalize and deduplicate
        hashtags = []
        seen = set()

        for match in matches:
            hashtag = match.lower()
            if hashtag not in seen:
                seen.add(hashtag)

                # Convert to different formats
                normalized = self._normalize_hashtag(hashtag)
                hashtags.append(normalized)

        return hashtags

    def _normalize_hashtag(self, hashtag: str) -> str:
        """
        Convert hashtag to various display formats.
        - original: #video
        - camel case: #VideoEditing
        - readable: #video_editing
        """
        # Choose format based on length and complexity
        if len(hashtag) <= 6:
            # Short hashtags use original
            return f"#{hashtag}"
        elif "_" in hashtag:
            # Snake case to title case
            words = hashtag.split("_")
            title_case = "".join(word.capitalize() for word in words)
            return f"#{title_case}"
        elif hashtag.replace("_", "").isalnum():
            # Camel case to readable
            readable = re.sub(r"(?<!^)([A-Z])", r" \1", hashtag).strip()
            return f"#{readable.lower()}"
        else:
            # Default to original
            return f"#{hashtag}"

    def process_video_hashtags(
        self, video_id: str, title: str, description: str
    ) -> List[str]:
        """
        Extract and store hashtags from video metadata.
        """
        # Extract from title and description
        title_hashtags = self.extract_hashtags(title)
        description_hashtags = self.extract_hashtags(description)

        # Combine and deduplicate
        all_hashtags = list(set(title_hashtags + description_hashtags))

        # Update hashtag usage counts
        for hashtag_name in all_hashtags:
            self.hashtag_repo.update_hashtag_usage(hashtag_name)

        return all_hashtags

    def get_trending_hashtags(self, hours: int = 24) -> List[Hashtag]:
        """
        Calculate trending hashtags based on recent usage.
        """
        trending_hashtags = self.hashtag_repo.get_trending_hashtags(limit=20)

        # Calculate trending scores based on:
        # 1. Recent usage (last N hours)
        # 2. Growth rate (increase in usage)
        # 3. Diversity (used across multiple videos)

        recent_hashtags = self.hashtag_repo.get_recent_hashtags(hours=hours, limit=50)

        # Update trending scores
        hashtag_scores = {}

        for hashtag in trending_hashtags:
            # Base score from current trending score
            score = hashtag.trending_score

            # Boost for recent usage
            recent_usage = any(h.name == hashtag.name for h in recent_hashtags)
            if recent_usage:
                score *= 1.5

            # Boost for high usage count
            if hashtag.count > 10:
                score *= 1.2

            # Boost for consistent usage
            if hashtag.count > 5:
                score *= 1.1

            hashtag_scores[hashtag.name] = score

        # Update scores in database
        if hashtag_scores:
            self.hashtag_repo.update_trending_scores(hashtag_scores)

        # Return updated trending list
        return self.hashtag_repo.get_trending_hashtags(limit=20)

    def get_hashtag_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """
        Get hashtag suggestions based on partial match.
        """
        if len(query) < 2:
            return []

        matching_hashtags = self.hashtag_repo.search_hashtags(query, limit)
        return [h.name for h in matching_hashtags]

    def get_popular_hashtags(self, limit: int = 20) -> List[Hashtag]:
        """
        Get most popular hashtags overall.
        """
        return self.hashtag_repo.get_popular_hashtags(limit=limit)

    def format_hashtags_for_display(self, hashtags: List[str]) -> List[dict]:
        """
        Format hashtags for UI display with various styles.
        """
        formatted = []

        for hashtag in hashtags:
            base_hashtag = hashtag.lstrip("#")

            formatted_hashtag = {
                "original": f"#{base_hashtag}",
                "camel_case": self._to_camel_case(base_hashtag),
                "readable": re.sub(r"(?<!^)([A-Z])", r" \1", base_hashtag).lower(),
                "title_case": " ".join(
                    word.capitalize() for word in base_hashtag.split("_")
                ),
                "short": base_hashtag
                if len(base_hashtag) <= 8
                else base_hashtag[:8] + "...",
            }

            formatted.append(formatted_hashtag)

        return formatted

    def _to_camel_case(self, text: str) -> str:
        """Convert text to camel case."""
        if "_" in text:
            words = text.split("_")
            return "".join(word.capitalize() for word in words)
        return text.capitalize()

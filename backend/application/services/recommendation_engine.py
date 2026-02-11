import logging
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import math

from ..domain.entities.video import Video
from ..domain.entities.user import User
from ..domain.entities.interaction import InteractionType

logger = logging.getLogger(__name__)

class RecommendationEngine:
    """Advanced recommendation engine for personalized video feeds."""
    
    def __init__(self):
        self.decay_factors = {
            'view': 1.0,
            'like': 5.0,
            'comment': 10.0,
            'share': 20.0,
            'follow': 30.0
        }

        self.time_decay_hours = 24  # Content freshness window
        self.max_recommendations = 100
        
    def calculate_user_interests(self, user_interactions: List[Dict]) -> Dict[str, float]:
        """Calculate user interest scores based on interaction history."""
        interests = defaultdict(float)
        current_time = datetime.utcnow()
        
        for interaction in user_interactions:
            # Calculate time decay
            hours_ago = (current_time - interaction['created_at']).total_seconds() / 3600
            time_decay = math.exp(-hours_ago / self.time_decay_hours)
            
            # Extract content features (hashtags, categories, etc.)
            video_tags = self._extract_video_features(interaction['video'])
            
            # Apply interaction weight and time decay
            interaction_weight = self.decay_factors.get(interaction['interaction_type'], 1.0)
            score = interaction_weight * time_decay
            
            for tag in video_tags:
                interests[tag] += score
        
        return dict(interests)
    
    def find_similar_users(self, user_id: str, all_interactions: List[Dict]) -> List[tuple]:
        """Find users with similar interaction patterns."""
        user_interactions = [i for i in all_interactions if i['user_id'] == user_id]
        user_interests = self.calculate_user_interests(user_interactions)
        
        similarities = []
        
        # Group interactions by user
        user_groups = defaultdict(list)
        for interaction in all_interactions:
            if interaction['user_id'] != user_id:
                user_groups[interaction['user_id']].append(interaction)
        
        for other_user_id, other_interactions in user_groups.items():
            other_interests = self.calculate_user_interests(other_interactions)
            
            # Calculate cosine similarity
            similarity = self._cosine_similarity(user_interests, other_interests)
            if similarity > 0.1:  # Minimum similarity threshold
                similarities.append((other_user_id, similarity))
        
        # Sort by similarity and return top users
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:20]  # Top 20 similar users
    
    def recommend_videos(
        self, 
        user_id: str,
        user_interactions: List[Dict],
        all_videos: List[Video],
        all_interactions: List[Dict],
        user_following: Optional[Set[str]] = None
    ) -> List[Video]:
        """Generate personalized video recommendations."""
        if not all_videos:
            return []
        
        current_time = datetime.utcnow()
        user_following = user_following or set()
        
        # Get user's interest profile
        user_interests = self.calculate_user_interests(user_interactions)
        
        # Find similar users
        similar_users = self.find_similar_users(user_id, all_interactions)
        similar_user_ids = [user_id for user_id, _ in similar_users]
        
        # Score videos
        video_scores = []
        
        for video in all_videos:
            # Skip if user already interacted with this video
            if self._user_interacted_with_video(user_id, video.id, user_interactions):
                continue
            
            score = 0.0
            
            # 1. Interest relevance score
            video_tags = self._extract_video_features_from_entity(video)
            interest_score = sum(
                user_interests.get(tag, 0) for tag in video_tags
            )
            score += interest_score * 0.4  # 40% weight
            
            # 2. Similar users' preferences
            similar_score = 0.0
            for similar_user_id, similarity in similar_users:
                user_interactions_for_video = [
                    i for i in all_interactions 
                    if i['user_id'] == similar_user_id and i['video_id'] == video.id
                ]
                for interaction in user_interactions_for_video:
                    weight = self.decay_factors.get(interaction['interaction_type'], 1.0)
                    similar_score += weight * similarity
            score += similar_score * 0.3  # 30% weight
            
            # 3. Following creator boost
            if video.creator_id in user_following:
                score += 50.0  # Following boost
            elif similar_user_ids:
                # Check if similar users follow this creator
                similar_followers = sum(
                    1 for user_id in similar_user_ids[:10]
                    if self._user_follows_creator(user_id, video.creator_id, all_interactions)
                )
                score += similar_followers * 10.0
            
            # 4. Freshness score
            hours_since_upload = (current_time - video.created_at).total_seconds() / 3600
            freshness_score = math.exp(-hours_since_upload / (24 * 7))  # 7-day decay
            score += freshness_score * 20.0  # 20% weight
            
            # 5. Quality score (based on engagement)
            if video.views > 0:
                engagement_rate = (video.likes + video.comments) / video.views
                quality_score = min(engagement_rate * 100, 50)  # Cap at 50
                score += quality_score * 0.1  # 10% weight
            
            video_scores.append((video, score))
        
        # Sort by score and return top recommendations
        video_scores.sort(key=lambda x: x[1], reverse=True)
        return [video for video, _ in video_scores[:self.max_recommendations]]
    
    def get_trending_videos(
        self, 
        all_videos: List[Video],
        all_interactions: List[Dict],
        hours: int = 24
    ) -> List[Video]:
        """Calculate trending videos based on recent engagement."""
        current_time = datetime.utcnow()
        cutoff_time = current_time - timedelta(hours=hours)
        
        # Filter recent interactions
        recent_interactions = [
            i for i in all_interactions 
            if i['created_at'] > cutoff_time
        ]
        
        # Calculate trending scores
        video_scores = defaultdict(float)
        
        for interaction in recent_interactions:
            video_id = interaction['video_id']
            weight = self.decay_factors.get(interaction['interaction_type'], 1.0)
            
            # Apply time decay (more recent = higher score)
            hours_ago = (current_time - interaction['created_at']).total_seconds() / 3600
            time_multiplier = math.exp(-hours_ago / hours)
            
            video_scores[video_id] += weight * time_multiplier
        
        # Find corresponding videos and sort
        trending_videos = []
        for video in all_videos:
            if video.id in video_scores:
                trending_videos.append((video, video_scores[video.id]))
        
        trending_videos.sort(key=lambda x: x[1], reverse=True)
        return [video for video, _ in trending_videos[:50]]
    
    def get_for_you_feed(
        self,
        user_id: str,
        user_interactions: List[Dict],
        all_videos: List[Video],
        all_interactions: List[Dict],
        user_following: Optional[Set[str]] = None,
        include_trending: bool = True
    ) -> List[Video]:
        """Generate 'For You' feed with personalized and trending content."""
        
        # Get personalized recommendations (70% of feed)
        personalized = self.recommend_videos(
            user_id, user_interactions, all_videos, all_interactions, user_following
        )
        
        if not include_trending:
            return personalized
        
        # Get trending content (30% of feed)
        trending = self.get_trending_videos(all_videos, all_interactions)
        
        # Remove duplicates from trending that are already in personalized
        personalized_ids = {video.id for video in personalized}
        trending_unique = [v for v in trending if v.id not in personalized_ids]
        
        # Combine and interleave
        feed = []
        personalized_count = len(personalized)
        trending_count = len(trending_unique)
        
        # 70:30 ratio
        feed_size = min(personalized_count + trending_count, 50)
        personalized_target = int(feed_size * 0.7)
        trending_target = feed_size - personalized_target
        
        # Add personalized videos
        feed.extend(personalized[:personalized_target])
        
        # Add trending videos
        feed.extend(trending_unique[:trending_target])
        
        return feed[:50]  # Limit to 50 videos
    
    def _extract_video_features(self, video_data: Dict) -> List[str]:
        """Extract searchable features from video data."""
        features = []
        
        # Add title words
        if video_data.get('title'):
            features.extend(video_data['title'].lower().split())
        
        # Add description words
        if video_data.get('description'):
            features.extend(video_data['description'].lower().split())
        
        # Add hashtags (if implemented)
        if video_data.get('hashtags'):
            features.extend([tag.lower() for tag in video_data['hashtags']])
        
        # Add category (if implemented)
        if video_data.get('category'):
            features.append(video_data['category'].lower())
        
        return features
    
    def _extract_video_features_from_entity(self, video: Video) -> List[str]:
        """Extract features from Video entity."""
        features = []
        
        # Title words
        features.extend(video.title.lower().split())
        
        # Description words
        features.extend(video.description.lower().split())
        
        # For now, basic tokenization. Later can add hashtags, categories, etc.
        return [f.strip() for f in features if len(f.strip()) > 2]
    
    def _cosine_similarity(self, dict1: Dict[str, float], dict2: Dict[str, float]) -> float:
        """Calculate cosine similarity between two dictionaries."""
        if not dict1 or not dict2:
            return 0.0
        
        # Get common keys
        common_keys = set(dict1.keys()) & set(dict2.keys())
        if not common_keys:
            return 0.0
        
        # Calculate dot product
        dot_product = sum(dict1[key] * dict2[key] for key in common_keys)
        
        # Calculate magnitudes
        mag1 = math.sqrt(sum(val ** 2 for val in dict1.values()))
        mag2 = math.sqrt(sum(val ** 2 for val in dict2.values()))
        
        if mag1 == 0 or mag2 == 0:
            return 0.0
        
        return dot_product / (mag1 * mag2)
    
    def _user_interacted_with_video(self, user_id: str, video_id: str, interactions: List[Dict]) -> bool:
        """Check if user has already interacted with a video."""
        return any(
            interaction['user_id'] == user_id and interaction['video_id'] == video_id
            for interaction in interactions
        )
    
    def _user_follows_creator(self, user_id: str, creator_id: str, interactions: List[Dict]) -> bool:
        """Check if user follows a creator."""
        return any(
            interaction['user_id'] == user_id and 
            interaction['target_user_id'] == creator_id and 
            interaction['interaction_type'] == InteractionType.FOLLOW.value
            for interaction in interactions
        )
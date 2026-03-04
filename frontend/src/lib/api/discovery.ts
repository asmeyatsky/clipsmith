import { apiClient } from './client';

// ==================== Response Types ====================

export interface Playlist {
    id: string;
    title: string;
    description: string;
    is_collaborative: boolean;
    is_public: boolean;
    owner_id?: string;
    created_at: string | null;
}

export interface PlaylistItem {
    id: string;
    video_id: string;
    position: number;
    added_at: string | null;
}

export interface PlaylistsResponse {
    success: boolean;
    playlists: Playlist[];
}

export interface PlaylistDetailResponse {
    success: boolean;
    playlist: Playlist & {
        items: PlaylistItem[];
    };
}

export interface UserPreferences {
    interest_weight: number;
    community_weight: number;
    virality_weight: number;
    freshness_weight: number;
    preferred_categories: string;
    preferred_languages: string;
    location: string;
}

export interface PreferencesResponse {
    success: boolean;
    preferences: UserPreferences;
}

export interface FavoriteCreator {
    id: string;
    creator_id: string;
    priority_notifications: boolean;
    added_at: string | null;
}

export interface FavoritesResponse {
    success: boolean;
    favorites: FavoriteCreator[];
}

export interface SuccessResponse {
    success: boolean;
    message: string;
}

export interface DiscoveryScore {
    success: boolean;
    video_id: string;
    discovery_score: number;
    weights_applied: {
        interest: number;
        community: number;
        virality: number;
        freshness: number;
    };
}

export interface TrafficBreakdown {
    success: boolean;
    video_id: string;
    traffic: {
        feed: number;
        search: number;
        profile: number;
        direct: number;
        external: number;
        hashtag: number;
    };
}

// ==================== Service ====================

export const discoveryService = {
    // Playlists
    async listPlaylists(): Promise<PlaylistsResponse> {
        return apiClient<PlaylistsResponse>('/api/discovery/playlists');
    },

    async getPlaylist(playlistId: string): Promise<PlaylistDetailResponse> {
        return apiClient<PlaylistDetailResponse>(`/api/discovery/playlists/${playlistId}`);
    },

    async createPlaylist(data: { title: string; description?: string; is_collaborative?: boolean; is_public?: boolean }): Promise<{ success: boolean; playlist: Playlist }> {
        return apiClient('/api/discovery/playlists', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    async addToPlaylist(playlistId: string, videoId: string): Promise<{ success: boolean; item_id: string; position: number }> {
        return apiClient(`/api/discovery/playlists/${playlistId}/items`, {
            method: 'POST',
            body: JSON.stringify({ video_id: videoId }),
        });
    },

    async removeFromPlaylist(playlistId: string, videoId: string): Promise<SuccessResponse> {
        return apiClient<SuccessResponse>(`/api/discovery/playlists/${playlistId}/items/${videoId}`, {
            method: 'DELETE',
        });
    },

    async addCollaborator(playlistId: string, userId: string): Promise<SuccessResponse> {
        return apiClient<SuccessResponse>(`/api/discovery/playlists/${playlistId}/collaborators`, {
            method: 'POST',
            body: JSON.stringify({ user_id: userId }),
        });
    },

    // Preferences
    async getPreferences(): Promise<PreferencesResponse> {
        return apiClient<PreferencesResponse>('/api/discovery/preferences');
    },

    async updatePreferences(data: Partial<UserPreferences>): Promise<SuccessResponse> {
        return apiClient<SuccessResponse>('/api/discovery/preferences', {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    },

    // Favorites
    async getFavoriteCreators(): Promise<FavoritesResponse> {
        return apiClient<FavoritesResponse>('/api/discovery/favorites');
    },

    async addFavorite(creatorId: string, priorityNotifications: boolean = true): Promise<SuccessResponse> {
        return apiClient<SuccessResponse>('/api/discovery/favorites', {
            method: 'POST',
            body: JSON.stringify({ creator_id: creatorId, priority_notifications: priorityNotifications }),
        });
    },

    async removeFavorite(creatorId: string): Promise<SuccessResponse> {
        return apiClient<SuccessResponse>(`/api/discovery/favorites/${creatorId}`, {
            method: 'DELETE',
        });
    },

    // Discovery Score & Analytics
    async getDiscoveryScore(videoId: string): Promise<DiscoveryScore> {
        return apiClient<DiscoveryScore>(`/api/discovery/videos/${videoId}/discovery-score`);
    },

    async getTrafficBreakdown(videoId: string): Promise<TrafficBreakdown> {
        return apiClient<TrafficBreakdown>(`/api/discovery/videos/${videoId}/traffic`);
    },

    async getRetentionGraph(videoId: string): Promise<{ success: boolean; video_id: string; retention: { data_points: number[]; average_watch_time: number; average_percentage: number } }> {
        return apiClient(`/api/discovery/videos/${videoId}/retention`);
    },

    async getPostingRecommendations(): Promise<{ success: boolean; recommendations: { best_posting_times: { day: string; hour: number; timezone: string }[]; trending_topics: string[]; audience_active_hours: string[]; suggested_hashtags: string[] } }> {
        return apiClient('/api/discovery/posting-recommendations');
    },
};

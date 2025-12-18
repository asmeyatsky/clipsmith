import { apiClient } from './client';

export interface Comment {
    id: string;
    video_id: string;
    username: string;
    content: string;
    created_at: string;
}

export const interactionService = {
    toggleLike: async (videoId: string): Promise<{ message: string, is_liked: boolean }> => {
        return apiClient(`/videos/${videoId}/like`, {
            method: 'POST'
        });
    },

    getLikeStatus: async (videoId: string): Promise<{ has_liked: boolean }> => {
        return apiClient(`/videos/${videoId}/like-status`);
    },

    listComments: async (videoId: string): Promise<Comment[]> => {
        return apiClient(`/videos/${videoId}/comments`);
    },

    addComment: async (videoId: string, content: string): Promise<Comment> => {
        return apiClient(`/videos/${videoId}/comments`, {
            method: 'POST',
            body: JSON.stringify({ content })
        });
    }
};

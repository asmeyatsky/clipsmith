import { apiClient } from './client';
import { ProfileResponse, FollowResponseDTO, FollowStatusDTO } from '../types';

export const userService = {
    getProfile: async (username: string): Promise<ProfileResponse> => {
        return apiClient(`/users/${username}`);
    },

    follow: async (userId: string): Promise<FollowResponseDTO> => {
        return apiClient<FollowResponseDTO>(`/users/${userId}/follow`, {
            method: 'POST',
        });
    },

    unfollow: async (userId: string): Promise<void> => { // Unfollow typically returns 204 No Content
        return apiClient<void>(`/users/${userId}/follow`, {
            method: 'DELETE',
        });
    },

    getFollowStatus: async (userId: string): Promise<FollowStatusDTO> => {
        return apiClient<FollowStatusDTO>(`/users/${userId}/follow_status`);
    }
};

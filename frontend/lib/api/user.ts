import { apiClient } from './client';
import { ProfileResponse } from '../types';

export const userService = {
    getProfile: async (username: string): Promise<ProfileResponse> => {
        return apiClient(`/users/${username}`);
    }
};

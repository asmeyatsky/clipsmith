import { apiClient } from './client';

export const authService = {
    async requestPasswordReset(email: string): Promise<{ message: string; debug_token?: string }> {
        return await apiClient('/auth/password-reset/request', {
            method: 'POST',
            body: JSON.stringify({ email }),
        });
    },

    async confirmPasswordReset(token: string, newPassword: string): Promise<{ message: string }> {
        return await apiClient('/auth/password-reset/confirm', {
            method: 'POST',
            body: JSON.stringify({ token, new_password: newPassword }),
        });
    },
};

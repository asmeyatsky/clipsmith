import { apiClient } from './client';
import { VideoResponseDTO } from '../types';

export const videoService = {
    async getById(videoId: string): Promise<VideoResponseDTO> {
        return await apiClient<VideoResponseDTO>(`/videos/${videoId}`);
    },

    async generateCaptions(videoId: string): Promise<{ message: string; video_id: string }> {
        return await apiClient<{ message: string; video_id: string }>(`/videos/${videoId}/captions/generate`, {
            method: 'POST',
        });
    },

    async sendTip(videoId: string, receiverId: string, amount: number): Promise<TipResponseDTO> {
        return await apiClient<TipResponseDTO>(`/videos/${videoId}/tip`, {
            method: 'POST',
            body: JSON.stringify({
                receiver_id: receiverId,
                video_id: videoId,
                amount: amount,
                currency: "USD" // Assuming default currency for now
            })
        });
    }
};

import { apiClient } from './client';
import { VideoResponseDTO, PaginatedVideos } from '../types';

interface TipResponseDTO {
    id: string;
    sender_id: string;
    receiver_id: string;
    video_id: string;
    amount: number;
    currency: string;
}

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
                currency: "USD"
            })
        });
    },

    async incrementViews(videoId: string): Promise<{ views: number }> {
        return await apiClient<{ views: number }>(`/videos/${videoId}/view`, {
            method: 'POST',
        });
    },

    async search(query: string, page: number = 1, pageSize: number = 20): Promise<PaginatedVideos> {
        return await apiClient<PaginatedVideos>(`/videos/search?q=${encodeURIComponent(query)}&page=${page}&page_size=${pageSize}`);
    },

    async getCaptions(videoId: string): Promise<CaptionDTO[]> {
        return await apiClient<CaptionDTO[]>(`/videos/${videoId}/captions`);
    }
};

export interface CaptionDTO {
    id: string;
    video_id: string;
    text: string;
    start_time: number;
    end_time: number;
    language: string;
}

export interface UserProfile {
    id: string;
    username: string;
}

export interface VideoResponseDTO {
    id: string;
    title: string;
    description: string;
    creator_id: string;
    url: string | null;
    thumbnail_url?: string | null;
    status: string;
    views: number;
    likes: number;
    duration: number;
}

export interface PaginatedVideoResponse {
    items: VideoResponseDTO[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
}

export interface PaginatedVideos {
    videos: VideoResponseDTO[];
    total: number;
    page: number;
    page_size: number;
    has_more: boolean;
}

export interface ProfileResponse {
    user: UserProfile;
    videos: VideoResponseDTO[];
}

export interface TipResponseDTO {
    id: string;
    sender_id: string;
    receiver_id: string;
    video_id: string | null;
    amount: number;
    currency: string;
    created_at: string; // Assuming ISO string from backend
}

export interface FollowResponseDTO {
    follower_id: string;
    followed_id: string;
    created_at: string;
}

export interface FollowStatusDTO {
    is_following: boolean;
}

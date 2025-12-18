export interface UserProfile {
    id: string;
    username: string;
}

export interface VideoResponseDTO {
    id: string;
    title: string;
    description: string;
    url: string | null;
    thumbnail_url?: string | null;
    status: string;
    views: number;
    likes: number;
}

export interface PaginatedVideoResponse {
    items: VideoResponseDTO[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
}

export interface ProfileResponse {
    user: UserProfile;
    videos: VideoResponseDTO[];
}

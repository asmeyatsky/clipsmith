export interface UserProfile {
    id: string;
    username: string;
}

export interface Video {
    id: string;
    title: string;
    description: string;
    url: string;
    status: string;
    views: number;
    likes: number;
}

export interface ProfileResponse {
    user: UserProfile;
    videos: Video[];
}

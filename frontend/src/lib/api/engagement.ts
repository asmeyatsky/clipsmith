import { apiClient } from './client';

// ==================== Response Types ====================

export interface PollOption {
    id: string;
    text: string;
    position: number;
    vote_count?: number;
}

export interface Poll {
    id: string;
    video_id: string;
    question: string;
    poll_type: string;
    options: PollOption[];
    created_at?: string | null;
}

export interface PollResponse {
    success: boolean;
    poll: Poll;
}

export interface PollsResponse {
    success: boolean;
    polls: {
        id: string;
        question: string;
        poll_type: string;
        created_at: string | null;
    }[];
}

export interface Challenge {
    id: string;
    title: string;
    description: string;
    start_date: string | null;
    end_date: string | null;
    prize_description: string | null;
    creator_id: string;
    status?: string;
}

export interface ChallengesResponse {
    success: boolean;
    challenges: Challenge[];
}

export interface ChallengeResponse {
    success: boolean;
    challenge: {
        id: string;
        title: string;
        description: string;
        start_date: string | null;
        end_date: string | null;
        status: string;
    };
}

export interface UserBadge {
    id: string;
    badge_type: string;
    badge_name: string;
    description: string;
    earned_at: string | null;
}

export interface BadgesResponse {
    success: boolean;
    badges: UserBadge[];
}

export interface SuccessResponse {
    success: boolean;
    message: string;
}

export interface ChapterMarker {
    id: string;
    title: string;
    start_time: number;
    end_time: number | null;
}

export interface ChaptersResponse {
    success: boolean;
    chapters: ChapterMarker[];
}

export interface ProductTag {
    id: string;
    product_name: string;
    product_url: string | null;
    price: number | null;
    currency: string;
    click_count: number;
}

export interface ProductTagsResponse {
    success: boolean;
    product_tags: ProductTag[];
}

export interface VideoLink {
    id: string;
    title: string;
    url: string;
    icon: string | null;
    click_count: number;
}

export interface VideoLinksResponse {
    success: boolean;
    links: VideoLink[];
}

// ==================== Service ====================

export const engagementService = {
    // Polls
    async getPolls(videoId: string): Promise<PollsResponse> {
        return apiClient<PollsResponse>(`/api/engagement/videos/${videoId}/polls`);
    },

    async getPoll(pollId: string): Promise<PollResponse> {
        return apiClient<PollResponse>(`/api/engagement/polls/${pollId}`);
    },

    async createPoll(data: {
        video_id: string;
        question: string;
        options: string[];
        poll_type?: string;
        correct_answer?: string;
        start_time?: string;
        end_time?: string;
    }): Promise<PollResponse> {
        return apiClient<PollResponse>('/api/engagement/polls', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    async votePoll(pollId: string, optionId: string): Promise<SuccessResponse> {
        return apiClient<SuccessResponse>(`/api/engagement/polls/${pollId}/vote`, {
            method: 'POST',
            body: JSON.stringify({ option_id: optionId }),
        });
    },

    // Challenges
    async getChallenges(limit: number = 20): Promise<ChallengesResponse> {
        return apiClient<ChallengesResponse>(`/api/engagement/challenges?limit=${limit}`);
    },

    async createChallenge(data: {
        title: string;
        description?: string;
        rules?: string;
        hashtag_id?: string;
        start_date?: string;
        end_date?: string;
        prize_description?: string;
    }): Promise<ChallengeResponse> {
        return apiClient<ChallengeResponse>('/api/engagement/challenges', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    async joinChallenge(challengeId: string, videoId: string): Promise<{ success: boolean; message: string; entry_id: string }> {
        return apiClient(`/api/engagement/challenges/${challengeId}/join`, {
            method: 'POST',
            body: JSON.stringify({ video_id: videoId }),
        });
    },

    // Badges
    async getUserBadges(userId: string): Promise<BadgesResponse> {
        return apiClient<BadgesResponse>(`/api/engagement/users/${userId}/badges`);
    },

    // Chapter Markers
    async getChapters(videoId: string): Promise<ChaptersResponse> {
        return apiClient<ChaptersResponse>(`/api/engagement/videos/${videoId}/chapters`);
    },

    async createChapter(videoId: string, data: { title: string; start_time: number; end_time?: number }): Promise<{ success: boolean; chapter: { id: string; video_id: string; title: string; start_time: number; end_time: number | null } }> {
        return apiClient(`/api/engagement/videos/${videoId}/chapters`, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    // Product Tags
    async getProductTags(videoId: string): Promise<ProductTagsResponse> {
        return apiClient<ProductTagsResponse>(`/api/engagement/videos/${videoId}/product-tags`);
    },

    async addProductTag(videoId: string, data: { product_name: string; product_url?: string; price?: number; currency?: string; timestamp?: number }): Promise<{ success: boolean; product_tag: { id: string; video_id: string; product_name: string; product_url: string | null; price: number | null } }> {
        return apiClient(`/api/engagement/videos/${videoId}/product-tags`, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    async trackProductClick(tagId: string): Promise<{ success: boolean; click_count: number }> {
        return apiClient(`/api/engagement/product-tags/${tagId}/click`, {
            method: 'POST',
        });
    },

    // Video Links
    async getVideoLinks(videoId: string): Promise<VideoLinksResponse> {
        return apiClient<VideoLinksResponse>(`/api/engagement/videos/${videoId}/links`);
    },

    async addVideoLink(videoId: string, data: { title: string; url: string; icon?: string }): Promise<{ success: boolean; link: { id: string; video_id: string; title: string; url: string; icon: string | null } }> {
        return apiClient(`/api/engagement/videos/${videoId}/links`, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    async trackLinkClick(linkId: string): Promise<{ success: boolean; click_count: number }> {
        return apiClient(`/api/engagement/links/${linkId}/click`, {
            method: 'POST',
        });
    },
};

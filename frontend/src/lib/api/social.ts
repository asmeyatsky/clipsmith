import { apiClient } from './client';

// ==================== Response Types ====================

export interface Conversation {
    conversation_id: string;
    last_message: string;
    last_message_at: string | null;
    other_user_id: string;
}

export interface ConversationsResponse {
    success: boolean;
    conversations: Conversation[];
}

export interface DirectMessage {
    id: string;
    sender_id: string;
    receiver_id: string;
    content: string;
    created_at: string | null;
}

export interface MessagesResponse {
    success: boolean;
    messages: DirectMessage[];
}

export interface SendMessageResponse {
    success: boolean;
    message: {
        id: string;
        conversation_id: string;
        sender_id: string;
        receiver_id: string;
        content: string;
        created_at: string | null;
    };
}

export interface LiveStream {
    id: string;
    title: string;
    description: string;
    host_id: string;
    status: string;
    scheduled_for: string | null;
    created_at: string | null;
}

export interface LiveStreamsResponse {
    success: boolean;
    live_streams: LiveStream[];
}

export interface LiveStreamResponse {
    success: boolean;
    live_stream: {
        id: string;
        title: string;
        status: string;
        host_id: string;
        scheduled_for: string | null;
    };
}

export interface WatchParty {
    id: string;
    video_id: string;
    title: string;
    host_id: string;
    status: string;
}

export interface WatchPartyResponse {
    success: boolean;
    watch_party: WatchParty;
}

export interface SuccessResponse {
    success: boolean;
    message: string;
}

export interface Duet {
    id: string;
    original_video_id: string;
    response_video_id: string;
    duet_type: string;
    creator_id: string;
    created_at: string | null;
}

export interface DuetsResponse {
    success: boolean;
    duets: Duet[];
}

export interface DuetResponse {
    success: boolean;
    duet: {
        id: string;
        original_video_id: string;
        response_video_id: string;
        duet_type: string;
        creator_id: string;
    };
}

// ==================== Service ====================

export const socialService = {
    // Conversations / DMs
    async getConversations(): Promise<ConversationsResponse> {
        return apiClient<ConversationsResponse>('/api/social/conversations');
    },

    async getMessages(conversationId: string, limit: number = 50): Promise<MessagesResponse> {
        return apiClient<MessagesResponse>(`/api/social/conversations/${conversationId}/messages?limit=${limit}`);
    },

    async sendMessage(receiverId: string, content: string): Promise<SendMessageResponse> {
        return apiClient<SendMessageResponse>('/api/social/messages', {
            method: 'POST',
            body: JSON.stringify({ receiver_id: receiverId, content }),
        });
    },

    // Live Streams
    async getLiveStreams(status?: string): Promise<LiveStreamsResponse> {
        const params = status ? `?status=${encodeURIComponent(status)}` : '';
        return apiClient<LiveStreamsResponse>(`/api/social/live-streams${params}`);
    },

    async createLiveStream(data: { title: string; description?: string; scheduled_for?: string }): Promise<LiveStreamResponse> {
        return apiClient<LiveStreamResponse>('/api/social/live-streams', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    async endLiveStream(streamId: string): Promise<SuccessResponse> {
        return apiClient<SuccessResponse>(`/api/social/live-streams/${streamId}/end`, {
            method: 'POST',
        });
    },

    async joinAsGuest(streamId: string): Promise<SuccessResponse> {
        return apiClient<SuccessResponse>(`/api/social/live-streams/${streamId}/guests`, {
            method: 'POST',
        });
    },

    // Watch Parties
    async getWatchParties(): Promise<{ success: boolean; watch_parties: WatchParty[] }> {
        // Note: The backend doesn't have a list endpoint for watch parties,
        // but the create and join endpoints exist.
        return { success: true, watch_parties: [] };
    },

    async createWatchParty(data: { video_id: string; title: string }): Promise<WatchPartyResponse> {
        return apiClient<WatchPartyResponse>('/api/social/watch-parties', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    async joinWatchParty(partyId: string): Promise<SuccessResponse> {
        return apiClient<SuccessResponse>(`/api/social/watch-parties/${partyId}/join`, {
            method: 'POST',
        });
    },

    // Duets
    async getDuets(videoId: string): Promise<DuetsResponse> {
        return apiClient<DuetsResponse>(`/api/social/duets/${videoId}`);
    },

    async createDuet(data: { original_video_id: string; response_video_id: string; duet_type?: string }): Promise<DuetResponse> {
        return apiClient<DuetResponse>('/api/social/duets', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    // Collaborative Videos
    async createCollaborativeVideo(data: { video_id: string; max_participants?: number }): Promise<{ success: boolean; collaborative_video: { id: string; video_id: string; creator_id: string; max_participants: number; status: string } }> {
        return apiClient('/api/social/collaborative-videos', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    async joinCollaborativeVideo(collabId: string): Promise<SuccessResponse> {
        return apiClient<SuccessResponse>(`/api/social/collaborative-videos/${collabId}/join`, {
            method: 'POST',
        });
    },
};

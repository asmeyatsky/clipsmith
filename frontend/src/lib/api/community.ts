import { apiClient } from './client';

// ==================== Response Types ====================

export interface Group {
    id: string;
    name: string;
    description: string;
    is_public: boolean;
    owner_id: string;
    rules?: string;
    created_at: string | null;
}

export interface GroupsResponse {
    success: boolean;
    groups: Group[];
}

export interface GroupResponse {
    success: boolean;
    group: Group;
}

export interface CommunityEvent {
    id: string;
    title: string;
    description: string;
    event_type: string;
    start_time: string;
    end_time: string | null;
    location: string | null;
    max_attendees: number | null;
    group_id: string | null;
    organizer_id: string;
}

export interface EventsResponse {
    success: boolean;
    events: CommunityEvent[];
}

export interface EventResponse {
    success: boolean;
    event: {
        id: string;
        title: string;
        event_type: string;
        start_time: string;
        end_time: string | null;
        organizer_id: string;
    };
}

export interface Circle {
    id: string;
    name: string;
    description: string;
    owner_id: string;
    created_at: string | null;
}

export interface CirclesResponse {
    success: boolean;
    circles: Circle[];
}

export interface CircleResponse {
    success: boolean;
    circle: Circle;
}

export interface CircleMember {
    id: string;
    user_id: string;
    joined_at: string | null;
}

export interface CircleMembersResponse {
    success: boolean;
    members: CircleMember[];
}

export interface DiscussionPost {
    id: string;
    group_id: string;
    author_id: string;
    content: string;
    parent_id: string | null;
    created_at: string | null;
}

export interface DiscussionPostsResponse {
    success: boolean;
    posts: DiscussionPost[];
}

export interface DiscussionPostResponse {
    success: boolean;
    post: DiscussionPost;
}

export interface SuccessResponse {
    success: boolean;
    message: string;
}

export interface RsvpResponse {
    success: boolean;
    rsvp_status: string;
}

// ==================== Service ====================

export const communityService = {
    // Groups
    async listGroups(limit: number = 20, offset: number = 0): Promise<GroupsResponse> {
        return apiClient<GroupsResponse>(`/api/community/groups?limit=${limit}&offset=${offset}`);
    },

    async getGroup(groupId: string): Promise<GroupResponse> {
        return apiClient<GroupResponse>(`/api/community/groups/${groupId}`);
    },

    async createGroup(data: { name: string; description?: string; rules?: string; is_public?: boolean }): Promise<GroupResponse> {
        return apiClient<GroupResponse>('/api/community/groups', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    async joinGroup(groupId: string): Promise<SuccessResponse> {
        return apiClient<SuccessResponse>(`/api/community/groups/${groupId}/join`, {
            method: 'POST',
        });
    },

    async leaveGroup(groupId: string): Promise<SuccessResponse> {
        return apiClient<SuccessResponse>(`/api/community/groups/${groupId}/leave`, {
            method: 'POST',
        });
    },

    // Discussion Posts
    async listDiscussions(groupId: string, limit: number = 20, offset: number = 0): Promise<DiscussionPostsResponse> {
        return apiClient<DiscussionPostsResponse>(`/api/community/groups/${groupId}/posts?limit=${limit}&offset=${offset}`);
    },

    async createDiscussion(groupId: string, data: { content: string; parent_id?: string }): Promise<DiscussionPostResponse> {
        return apiClient<DiscussionPostResponse>(`/api/community/groups/${groupId}/posts`, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    // Events
    async listEvents(groupId?: string, limit: number = 20): Promise<EventsResponse> {
        const params = new URLSearchParams();
        if (groupId) params.set('group_id', groupId);
        params.set('limit', limit.toString());
        return apiClient<EventsResponse>(`/api/community/events?${params.toString()}`);
    },

    async getEvent(eventId: string): Promise<EventResponse> {
        return apiClient<EventResponse>(`/api/community/events/${eventId}`);
    },

    async createEvent(data: {
        title: string;
        description?: string;
        event_type?: string;
        start_time: string;
        end_time?: string;
        location?: string;
        max_attendees?: number;
        group_id?: string;
    }): Promise<EventResponse> {
        return apiClient<EventResponse>('/api/community/events', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    async rsvpEvent(eventId: string, rsvpStatus: 'attending' | 'maybe' | 'not_attending' = 'attending'): Promise<RsvpResponse> {
        return apiClient<RsvpResponse>(`/api/community/events/${eventId}/rsvp`, {
            method: 'POST',
            body: JSON.stringify({ rsvp_status: rsvpStatus }),
        });
    },

    // Circles
    async listCircles(): Promise<CirclesResponse> {
        return apiClient<CirclesResponse>('/api/community/circles');
    },

    async createCircle(data: { name: string; description?: string }): Promise<CircleResponse> {
        return apiClient<CircleResponse>('/api/community/circles', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    async addCircleMember(circleId: string, memberId: string): Promise<SuccessResponse> {
        return apiClient<SuccessResponse>(`/api/community/circles/${circleId}/members`, {
            method: 'POST',
            body: JSON.stringify({ member_id: memberId }),
        });
    },

    async removeCircleMember(circleId: string, memberId: string): Promise<SuccessResponse> {
        return apiClient<SuccessResponse>(`/api/community/circles/${circleId}/members/${memberId}`, {
            method: 'DELETE',
        });
    },

    async getCircleMembers(circleId: string): Promise<CircleMembersResponse> {
        return apiClient<CircleMembersResponse>(`/api/community/circles/${circleId}/members`);
    },
};

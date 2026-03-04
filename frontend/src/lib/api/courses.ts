import { apiClient } from './client';

// ==================== Response Types ====================

export interface Course {
    id: string;
    title: string;
    description: string;
    price: number;
    category: string;
    creator_id: string;
    status?: string;
    created_at: string | null;
}

export interface CoursesResponse {
    success: boolean;
    courses: Course[];
}

export interface CourseLesson {
    id: string;
    title: string;
    description: string;
    video_id: string | null;
    position: number;
    is_free_preview: boolean;
}

export interface CourseDetailResponse {
    success: boolean;
    course: Course & {
        lessons: CourseLesson[];
    };
}

export interface EnrolledCourse {
    id: string;
    title: string;
    description: string;
    price: number;
    category: string;
    enrolled_at: string | null;
    progress: number;
}

export interface EnrolledCoursesResponse {
    success: boolean;
    courses: EnrolledCourse[];
}

export interface EnrollResponse {
    success: boolean;
    message: string;
    enrollment_id: string;
}

export interface LessonResponse {
    success: boolean;
    lesson: {
        id: string;
        title: string;
        position: number;
        is_free_preview: boolean;
    };
}

export interface SuccessResponse {
    success: boolean;
    message: string;
}

export interface SubscriptionTier {
    id: string;
    name: string;
    price: number;
    interval: string;
    description: string;
    benefits: string;
}

export interface SubscriptionTiersResponse {
    success: boolean;
    tiers: SubscriptionTier[];
}

// ==================== Service ====================

export const courseService = {
    async listCourses(category?: string, limit: number = 20, offset: number = 0): Promise<CoursesResponse> {
        const params = new URLSearchParams();
        if (category) params.set('category', category);
        params.set('limit', limit.toString());
        params.set('offset', offset.toString());
        return apiClient<CoursesResponse>(`/api/courses/?${params.toString()}`);
    },

    async getCourse(courseId: string): Promise<CourseDetailResponse> {
        return apiClient<CourseDetailResponse>(`/api/courses/${courseId}`);
    },

    async enrollInCourse(courseId: string): Promise<EnrollResponse> {
        return apiClient<EnrollResponse>(`/api/courses/${courseId}/enroll`, {
            method: 'POST',
        });
    },

    async getEnrollments(): Promise<EnrolledCoursesResponse> {
        return apiClient<EnrolledCoursesResponse>('/api/courses/enrolled');
    },

    async getLessons(courseId: string): Promise<CourseDetailResponse> {
        // Lessons are included in the getCourse response
        return apiClient<CourseDetailResponse>(`/api/courses/${courseId}`);
    },

    async completeLesson(courseId: string, lessonId: string): Promise<SuccessResponse> {
        return apiClient<SuccessResponse>(`/api/courses/${courseId}/progress`, {
            method: 'PUT',
            body: JSON.stringify({ lesson_id: lessonId }),
        });
    },

    async createCourse(data: { title: string; description?: string; price?: number; category?: string }): Promise<{ success: boolean; course: Course }> {
        return apiClient(`/api/courses/`, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    async addLesson(courseId: string, data: { title: string; description?: string; video_id?: string; position?: number; is_free_preview?: boolean }): Promise<LessonResponse> {
        return apiClient<LessonResponse>(`/api/courses/${courseId}/lessons`, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    async getCreatorCourses(creatorId: string): Promise<CoursesResponse> {
        return apiClient<CoursesResponse>(`/api/courses/creator/${creatorId}`);
    },

    // Subscription Tiers
    async getSubscriptionTiers(creatorId: string): Promise<SubscriptionTiersResponse> {
        return apiClient<SubscriptionTiersResponse>(`/api/courses/subscription-tiers/${creatorId}`);
    },

    async createSubscriptionTier(data: { name: string; price: number; interval?: string; description?: string; benefits?: string }): Promise<{ success: boolean; tier: SubscriptionTier }> {
        return apiClient('/api/courses/subscription-tiers', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    // Creator Fund
    async applyForCreatorFund(): Promise<{ success: boolean; application: { id: string; status: string; applied_at: string | null } }> {
        return apiClient('/api/courses/creator-fund/apply', {
            method: 'POST',
        });
    },

    async getCreatorFundStatus(): Promise<{ success: boolean; has_application: boolean; status: string | null; applied_at?: string | null }> {
        return apiClient('/api/courses/creator-fund/status');
    },
};

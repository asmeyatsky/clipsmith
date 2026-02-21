import { useAuthStore } from '@/lib/auth/auth-store';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function getBaseUrl() {
    return BASE_URL;
}

export async function apiClient<T = unknown>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    };

    const response = await fetch(`${BASE_URL}${endpoint}`, {
        ...options,
        headers,
        credentials: 'include',
    });

    if (response.status === 401) {
        useAuthStore.getState().logout();
        throw new Error('Session expired. Please log in again.');
    }

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'API request failed' }));
        throw new Error(error.detail || `Request failed with status ${response.status}`);
    }

    return response.json() as Promise<T>;
}

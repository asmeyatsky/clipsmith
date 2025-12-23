import { useAuthStore } from '@/lib/auth/auth-store';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function getBaseUrl() {
    return BASE_URL;
}

export async function apiClient<T = any>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const { token } = useAuthStore.getState();

    const headers = {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options.headers,
    };

    const response = await fetch(`${BASE_URL}${endpoint}`, {
        ...options,
        headers,
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'API request failed');
    }

    return response.json() as Promise<T>;
}

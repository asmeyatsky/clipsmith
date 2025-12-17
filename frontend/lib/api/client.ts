import { useAuthStore } from './auth-store';

const BASE_URL = 'http://localhost:8001';

export async function apiClient(endpoint: string, options: RequestInit = {}) {
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

    return response.json();
}

import { create } from 'zustand';

interface User {
    id: string;
    username: string;
    email: string;
}

interface AuthState {
    user: User | null;
    isLoading: boolean;
    setAuth: (user: User) => void;
    logout: () => void;
    fetchCurrentUser: () => Promise<void>;
    isAuthenticated: () => boolean;
}

export const useAuthStore = create<AuthState>()(
    (set, get) => ({
        user: null,
        isLoading: true,
        setAuth: (user) => set({ user, isLoading: false }),
        logout: async () => {
            try {
                await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/auth/logout`, {
                    method: 'POST',
                    credentials: 'include',
                });
            } catch (e) {
                console.error('Logout request failed:', e);
            }
            set({ user: null });
        },
        fetchCurrentUser: async () => {
            set({ isLoading: true });
            try {
                const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/auth/me`, {
                    credentials: 'include',
                });
                if (response.ok) {
                    const user = await response.json();
                    set({ user, isLoading: false });
                } else {
                    set({ user: null, isLoading: false });
                }
            } catch {
                set({ user: null, isLoading: false });
            }
        },
        isAuthenticated: () => !!get().user,
    })
);

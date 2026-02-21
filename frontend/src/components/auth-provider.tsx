'use client';

import { useEffect } from 'react';
import { useAuthStore } from '@/lib/auth/auth-store';

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const { fetchCurrentUser, isLoading } = useAuthStore();

    useEffect(() => {
        fetchCurrentUser();
    }, [fetchCurrentUser]);

    if (isLoading) {
        return null;
    }

    return <>{children}</>;
}

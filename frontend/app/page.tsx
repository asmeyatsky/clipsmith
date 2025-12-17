'use client';

import Link from 'next/link';
import { useAuthStore } from '@/lib/auth/auth-store';
import { useEffect, useState } from 'react';
import { UploadModal } from '@/components/video/upload-modal';

export default function Home() {
    const { user, logout } = useAuthStore();
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
    }, []);

    if (!mounted) return null;

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-zinc-950 pb-20">
            {/* Hero Section */}
            <div className="flex flex-col items-center justify-center text-center p-8 pt-20">
                <h1 className="text-5xl font-extrabold bg-gradient-to-r from-blue-600 to-violet-600 bg-clip-text text-transparent mb-6">
                    clipsmith
                </h1>
                <p className="text-xl text-gray-600 dark:text-gray-400 mb-8 max-w-lg">
                    The premier social video creation platform. Build your community today.
                </p>

                <div className="flex gap-4 mb-16">
                    {user ? (
                        <div className="space-y-4 flex flex-col items-center">
                            <p className="text-lg font-medium">Hello, {user.username}!</p>
                            <div className="flex gap-3">
                                <UploadModal onUploadSuccess={() => window.location.reload()} />
                                <button
                                    onClick={logout}
                                    className="px-6 py-2.5 rounded-full bg-red-100 text-red-600 font-semibold hover:bg-red-200 transition-colors"
                                >
                                    Sign Out
                                </button>
                            </div>
                        </div>
                    ) : (
                        <>
                            <Link
                                href="/login"
                                className="px-8 py-3 rounded-full bg-white text-gray-900 border border-gray-200 font-semibold hover:bg-gray-50 transition-colors shadow-sm"
                            >
                                Log In
                            </Link>
                            <Link
                                href="/register"
                                className="px-8 py-3 rounded-full bg-blue-600 text-white font-semibold hover:bg-blue-700 transition-colors shadow-lg hover:shadow-xl hover:scale-105"
                            >
                                Get Started
                            </Link>
                        </>
                    )}
                </div>
            </div>

            {/* Video Feed Section */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex items-center gap-3 mb-8">
                    <h2 className="text-2xl font-bold">Trending Clips</h2>
                    <div className="h-px flex-1 bg-gray-200 dark:bg-zinc-800"></div>
                </div>
                <VideoFeed />
            </div>
        </div>
    );
}

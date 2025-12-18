'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation'; // Correct hook for App Router params
import { userService } from '@/lib/api/user';
import { ProfileResponse } from '@/lib/types';
import { ProfileHeader } from '@/components/profile/profile-header';
import { VideoCard } from '@/components/video/video-card';
import { Loader2, AlertCircle } from 'lucide-react';
import Link from 'next/link';

export default function ProfilePage() {
    const params = useParams();
    const username = params.username as string; // Next.js params can be string or string[]

    const [profile, setProfile] = useState<ProfileResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchProfile = async () => {
            if (!username) return;
            try {
                setLoading(true);
                const data = await userService.getProfile(username);
                setProfile(data);
            } catch (err: any) {
                setError(err.message || 'Failed to load profile');
            } finally {
                setLoading(false);
            }
        };

        fetchProfile();
    }, [username]);

    if (loading) {
        return (
            <div className="flex justify-center items-center h-screen">
                <Loader2 className="animate-spin text-blue-500" size={48} />
            </div>
        );
    }

    if (error || !profile) {
        return (
            <div className="flex flex-col items-center justify-center h-screen gap-4">
                <AlertCircle className="text-red-500" size={48} />
                <p className="text-xl font-semibold text-gray-800 dark:text-gray-200">
                    {error || 'User not found'}
                </p>
                <Link
                    href="/"
                    className="px-6 py-2 bg-blue-600 text-white rounded-full hover:bg-blue-700 transition-colors"
                >
                    Go Home
                </Link>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-zinc-950 pb-20 pt-20">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                {/* Back Button */}
                <Link href="/" className="inline-block mb-6 text-gray-500 hover:text-gray-900 dark:hover:text-gray-100 font-medium">
                    &larr; Back to Feed
                </Link>

                <ProfileHeader user={profile.user} videos={profile.videos} />

                <div className="flex items-center gap-3 mb-8">
                    <h2 className="text-2xl font-bold">Uploads</h2>
                    <div className="h-px flex-1 bg-gray-200 dark:bg-zinc-800"></div>
                </div>

                {profile.videos.length === 0 ? (
                    <div className="text-center py-20 text-gray-500">
                        No videos uploaded yet.
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {profile.videos.map((video) => (
                            <VideoCard key={video.id} video={video} />
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

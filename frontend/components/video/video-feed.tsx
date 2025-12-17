'use client';

import { useEffect, useState } from 'react';
import { VideoCard } from './video-card';
import { apiClient } from '@/lib/api/client';

interface Video {
    id: string;
    title: string;
    description: string;
    url: string;
    views: number;
    likes: number;
    status: string;
}

export function VideoFeed() {
    const [videos, setVideos] = useState<Video[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    const fetchVideos = async () => {
        try {
            const data = await apiClient('/videos/');
            // Using reverse() to show newest first if no sort on backend yet, 
            // though backend assumes append order or sorted by ID/time.
            // Let's assume backend returns list, frontend can client-sort for now.
            setVideos(data.reverse());
        } catch (err) {
            setError('Failed to load videos');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchVideos();
    }, []);

    // Refresh feed exposed to parent if needed, or simple auto-refresh/polling later

    if (loading) {
        return (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 animate-pulse">
                {[...Array(4)].map((_, i) => (
                    <div key={i} className="bg-gray-200 dark:bg-zinc-800 rounded-2xl aspect-[9/16] h-96"></div>
                ))}
            </div>
        );
    }

    if (error) {
        return <div className="text-center text-red-500 py-10">{error}</div>;
    }

    if (videos.length === 0) {
        return (
            <div className="text-center text-gray-500 py-20 bg-gray-50 dark:bg-zinc-900 rounded-3xl border border-dashed border-gray-200 dark:border-zinc-800">
                <p className="text-xl font-medium">No videos yet</p>
                <p className="text-sm mt-2">Be the first to upload one!</p>
            </div>
        );
    }

    return (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {videos.map((video) => (
                <VideoCard key={video.id} video={video} />
            ))}
        </div>
    );
}

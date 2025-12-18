'use client';

import { useEffect, useState, useCallback } from 'react';
import { VideoCard } from './video-card';
import { apiClient } from '@/lib/api/client';
import { motion } from 'framer-motion';
import { Loader2 } from 'lucide-react';

import { VideoResponseDTO, PaginatedVideoResponse } from '@/lib/types';

const container = {
    hidden: { opacity: 0 },
    show: {
        opacity: 1,
        transition: {
            staggerChildren: 0.1
        }
    }
};

export function VideoFeed() {
    const [videos, setVideos] = useState<VideoResponseDTO[]>([]);
    const [loading, setLoading] = useState(true);
    const [loadingMore, setLoadingMore] = useState(false);
    const [error, setError] = useState('');
    const [page, setPage] = useState(1);
    const [hasMore, setHasMore] = useState(true);

    const fetchVideos = useCallback(async (pageNum: number = 1, append: boolean = false) => {
        try {
            if (append) {
                setLoadingMore(true);
            } else {
                setLoading(true);
            }

            const data: PaginatedVideoResponse = await apiClient(`/videos/?page=${pageNum}&page_size=12`);

            if (append) {
                setVideos(prev => [...prev, ...data.items]);
            } else {
                setVideos(data.items);
            }

            setHasMore(pageNum < data.total_pages);
            setPage(pageNum);
        } catch (err) {
            setError('Failed to load videos');
        } finally {
            setLoading(false);
            setLoadingMore(false);
        }
    }, []);

    useEffect(() => {
        fetchVideos(1);
    }, [fetchVideos]);

    const loadMore = () => {
        if (!loadingMore && hasMore) {
            fetchVideos(page + 1, true);
        }
    };

    if (loading) {
        return (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8 animate-pulse">
                {[...Array(8)].map((_, i) => (
                    <div key={i} className="bg-zinc-100 dark:bg-zinc-900 rounded-3xl aspect-[9/16] h-[500px]" />
                ))}
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex flex-col items-center justify-center py-20 text-center">
                <p className="text-red-500 font-medium mb-4">{error}</p>
                <button onClick={() => fetchVideos(1)} className="text-blue-500 hover:underline">Try again</button>
            </div>
        );
    }

    if (videos.length === 0) {
        return (
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="text-center py-32 bg-zinc-50 dark:bg-zinc-900/40 rounded-[3rem] border border-dashed border-zinc-200 dark:border-zinc-800"
            >
                <p className="text-2xl font-semibold text-zinc-400">No videos found</p>
                <p className="text-sm mt-2 text-zinc-500">Wait for someone to share their magic.</p>
            </motion.div>
        );
    }

    return (
        <div className="space-y-8">
            <motion.div
                variants={container}
                initial="hidden"
                animate="show"
                className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8"
            >
                {videos.map((video) => (
                    <VideoCard key={video.id} video={video} />
                ))}
            </motion.div>

            {hasMore && (
                <div className="flex justify-center pt-4">
                    <button
                        onClick={loadMore}
                        disabled={loadingMore}
                        className="px-8 py-3 rounded-full bg-zinc-100 dark:bg-zinc-900 hover:bg-zinc-200 dark:hover:bg-zinc-800 transition-colors font-medium disabled:opacity-50 flex items-center gap-2"
                    >
                        {loadingMore ? (
                            <>
                                <Loader2 className="w-4 h-4 animate-spin" />
                                Loading...
                            </>
                        ) : (
                            'Load More'
                        )}
                    </button>
                </div>
            )}
        </div>
    );
}


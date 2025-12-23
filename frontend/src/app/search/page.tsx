'use client';

import { useSearchParams } from 'next/navigation';
import { useEffect, useState, Suspense } from 'react';
import { videoService } from '@/lib/api/video';
import { VideoResponseDTO } from '@/lib/types';
import { VideoCard } from '@/components/video/video-card';
import { motion } from 'framer-motion';
import { Search, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';

function SearchResults() {
    const searchParams = useSearchParams();
    const query = searchParams.get('q') || '';
    const [videos, setVideos] = useState<VideoResponseDTO[]>([]);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [hasMore, setHasMore] = useState(false);
    const [total, setTotal] = useState(0);

    useEffect(() => {
        if (query) {
            setLoading(true);
            setPage(1);
            videoService.search(query, 1, 12)
                .then((data) => {
                    setVideos(data.videos);
                    setHasMore(data.has_more);
                    setTotal(data.total);
                })
                .catch(console.error)
                .finally(() => setLoading(false));
        }
    }, [query]);

    const loadMore = async () => {
        const nextPage = page + 1;
        const data = await videoService.search(query, nextPage, 12);
        setVideos(prev => [...prev, ...data.videos]);
        setHasMore(data.has_more);
        setPage(nextPage);
    };

    if (!query) {
        return (
            <div className="flex flex-col items-center justify-center py-20">
                <Search className="w-16 h-16 text-zinc-300 dark:text-zinc-700 mb-4" />
                <h2 className="text-2xl font-bold text-zinc-500">Enter a search term</h2>
                <p className="text-zinc-400">Use the search bar above to find videos</p>
            </div>
        );
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center py-20">
                <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
            </div>
        );
    }

    return (
        <div>
            <div className="mb-8">
                <h1 className="text-3xl font-bold mb-2">
                    Search results for "{query}"
                </h1>
                <p className="text-zinc-500">
                    {total} video{total !== 1 ? 's' : ''} found
                </p>
            </div>

            {videos.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20">
                    <Search className="w-16 h-16 text-zinc-300 dark:text-zinc-700 mb-4" />
                    <h2 className="text-2xl font-bold text-zinc-500">No videos found</h2>
                    <p className="text-zinc-400">Try different search terms</p>
                </div>
            ) : (
                <>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                        {videos.map((video, index) => (
                            <motion.div
                                key={video.id}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: index * 0.05 }}
                            >
                                <VideoCard video={video} />
                            </motion.div>
                        ))}
                    </div>

                    {hasMore && (
                        <div className="flex justify-center mt-12">
                            <Button
                                onClick={loadMore}
                                variant="outline"
                                size="lg"
                                className="rounded-full"
                            >
                                Load More
                            </Button>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}

export default function SearchPage() {
    return (
        <div className="max-w-7xl mx-auto px-6 pt-32 pb-20">
            <Suspense fallback={
                <div className="flex items-center justify-center py-20">
                    <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
                </div>
            }>
                <SearchResults />
            </Suspense>
        </div>
    );
}

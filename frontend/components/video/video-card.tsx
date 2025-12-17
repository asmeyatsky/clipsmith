import { useState, useEffect } from 'react';
import { interactionService } from '@/lib/api/interactions';
import { useAuthStore } from '@/lib/auth/auth-store';
import { CommentsSection } from './comments-section';
import { Play, Heart, MessageCircle, Share2, MoreHorizontal } from 'lucide-react';

interface VideoProps {
    id: string;
    title: string;
    description: string;
    url: string;
    views: number;
    likes: number;
}

export function VideoCard({ video }: { video: VideoProps }) {
    const { user } = useAuthStore();
    const [likes, setLikes] = useState(video.likes);
    const [isLiked, setIsLiked] = useState(false);
    const [showComments, setShowComments] = useState(false);

    useEffect(() => {
        if (user) {
            interactionService.getLikeStatus(video.id).then(res => setIsLiked(res.has_liked));
        }
    }, [user, video.id]);

    const handleLike = async () => {
        if (!user) return alert("Login to like!"); // Or open login modal

        try {
            const res = await interactionService.toggleLike(video.id);
            setIsLiked(res.is_liked);
            setLikes(prev => res.is_liked ? prev + 1 : prev - 1);
        } catch (err) {
            console.error("Like failed", err);
        }
    };

    return (
        <>
            <div className="bg-white dark:bg-zinc-900 rounded-2xl overflow-hidden shadow-lg border border-gray-100 dark:border-zinc-800 hover:shadow-xl transition-all duration-300 group">
                {/* Video Player */}
                <div className="relative aspect-[9/16] bg-black">
                    <video
                        src={video.url}
                        controls
                        className="w-full h-full object-cover"
                        poster="/placeholder.png"
                    />
                </div>

                {/* Content */}
                <div className="p-4">
                    <div className="flex justify-between items-start mb-2">
                        <h3 className="font-bold text-lg line-clamp-2 leading-tight group-hover:text-blue-600 transition-colors">
                            {video.title}
                        </h3>
                        <button className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
                            <MoreHorizontal size={20} />
                        </button>
                    </div>

                    <p className="text-sm text-gray-500 dark:text-gray-400 line-clamp-2 mb-4">
                        {video.description}
                    </p>

                    {/* Actions */}
                    <div className="flex items-center justify-between text-gray-500 dark:text-gray-400">
                        <button
                            onClick={handleLike}
                            className={`flex items-center gap-1.5 transition-colors ${isLiked ? 'text-red-500' : 'hover:text-red-500'}`}
                        >
                            <Heart size={20} fill={isLiked ? "currentColor" : "none"} />
                            <span className="text-sm font-medium">{likes}</span>
                        </button>

                        <button
                            onClick={() => setShowComments(true)}
                            className="flex items-center gap-1.5 hover:text-blue-500 transition-colors"
                        >
                            <MessageCircle size={20} />
                            <span className="text-sm font-medium">Comments</span>
                        </button>

                        <button className="flex items-center gap-1.5 hover:text-green-500 transition-colors">
                            <Share2 size={20} />
                        </button>

                        <div className="text-xs font-medium bg-gray-100 dark:bg-zinc-800 px-2 py-1 rounded-md">
                            {video.views} views
                        </div>
                    </div>
                </div>
            </div>

            <CommentsSection
                videoId={video.id}
                isOpen={showComments}
                onClose={() => setShowComments(false)}
            />
        </>
    );
}

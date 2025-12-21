import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { interactionService } from '@/lib/api/interactions';
import { useAuthStore } from '@/lib/auth/auth-store';
import { CommentsSection } from './comments-section';
import { Play, Heart, MessageCircle, Share2, MoreHorizontal, Eye, Loader2, X, Pencil, DollarSign } from 'lucide-react'; // Added DollarSign
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { VideoResponseDTO } from '@/lib/types'; // Import the DTO
import { TipModal } from '@/components/modals/tip-modal'; // Import TipModal


interface VideoProps extends VideoResponseDTO {} // Use the DTO for props, or just use VideoResponseDTO directly

export function VideoCard({ video }: { video: VideoProps }) {
    const { user } = useAuthStore();
    const router = useRouter();
    const [likes, setLikes] = useState(video.likes);
    const [isLiked, setIsLiked] = useState(false);
    const [showComments, setShowComments] = useState(false);
    const [showTipModal, setShowTipModal] = useState(false); // New state for TipModal
    const [isHovered, setIsHovered] = useState(false);

    useEffect(() => {
        // Ensure likes state is updated if video prop changes
        setLikes(video.likes);
    }, [video.likes]);

    useEffect(() => {
        if (user) {
            interactionService.getLikeStatus(video.id).then(res => {
                if (res) { // Ensure response is not undefined
                    setIsLiked(res.has_liked);
                }
            });
        }
    }, [user, video.id]);

    const handleLike = async (e: React.MouseEvent) => {
        e.stopPropagation();
        if (!user) return alert("Login to like!");

        try {
            const res = await interactionService.toggleLike(video.id);
            setIsLiked(res.is_liked);
            setLikes(prev => res.is_liked ? prev + 1 : prev - 1);
        } catch (err) {
            console.error("Like failed", err);
        }
    };

    const handleEdit = (e: React.MouseEvent) => {
        e.stopPropagation();
        router.push(`/editor/${video.id}`);
    };

    return (
        <>
            <motion.div
                layout
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                whileHover={{ y: -8 }}
                onHoverStart={() => setIsHovered(true)}
                onHoverEnd={() => setIsHovered(false)}
                className="group relative"
            >
                <Card className="overflow-hidden border-none bg-zinc-900/50 backdrop-blur-sm shadow-2xl transition-all duration-500 hover:ring-2 hover:ring-blue-500/50">
                    <CardContent className="p-0">
                        {/* Video Player Area */}
                        <div className="relative aspect-[9/16] overflow-hidden bg-black cursor-pointer">
                            {video.status === 'READY' && video.url ? (
                                <video
                                    src={video.url}
                                    loop
                                    muted
                                    playsInline
                                    className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
                                    poster={video.thumbnail_url || "/placeholder.png"} // Use thumbnail or generic placeholder
                                    onMouseEnter={(e) => (e.target as HTMLVideoElement).play()}
                                    onMouseLeave={(e) => {
                                        const v = e.target as HTMLVideoElement;
                                        v.pause();
                                        v.currentTime = 0;
                                    }}
                                />
                            ) : (
                                <div className="absolute inset-0 flex flex-col items-center justify-center bg-zinc-900 text-white p-4 text-center">
                                    {video.status === 'FAILED' ? (
                                        <>
                                            <X size={48} className="text-red-500 mb-2" />
                                            <p className="font-bold text-lg">Video Processing Failed</p>
                                            <p className="text-sm text-zinc-400">Please try re-uploading.</p>
                                        </>
                                    ) : (
                                        <>
                                            <Loader2 size={48} className="animate-spin text-blue-500 mb-2" />
                                            <p className="font-bold text-lg">Processing Video</p>
                                            <p className="text-sm text-zinc-400">This clip will be ready soon!</p>
                                        </>
                                    )}
                                    {video.thumbnail_url && (
                                        <img src={video.thumbnail_url} alt="Video thumbnail" className="absolute inset-0 w-full h-full object-cover opacity-20 -z-10" />
                                    )}
                                </div>
                            )}

                            {/* Overlay Controls (Visual Only) */}
                            <div className="absolute inset-0 bg-black/20 group-hover:bg-black/0 transition-colors pointer-events-none" />

                            <div className="absolute top-4 right-4 flex flex-col gap-2 opacity-0 group-hover:opacity-100 transition-opacity translate-x-4 group-hover:translate-x-0 duration-300">
                                {user && user.id === video.creator_id && (
                                    <Button
                                        variant="secondary"
                                        size="icon"
                                        className="rounded-full bg-white/20 backdrop-blur-md border-white/20 text-white hover:bg-white/40"
                                        onClick={handleEdit}
                                    >
                                        <Pencil size={18} />
                                    </Button>
                                )}
                                <Button variant="secondary" size="icon" className="rounded-full bg-white/20 backdrop-blur-md border-white/20 text-white hover:bg-white/40">
                                    <Share2 size={18} />
                                </Button>
                                <Button variant="secondary" size="icon" className="rounded-full bg-white/20 backdrop-blur-md border-white/20 text-white hover:bg-white/40">
                                    <MoreHorizontal size={18} />
                                </Button>
                            </div>

                            <div className="absolute bottom-4 left-4 right-4 flex items-end justify-between">
                                <div className="space-y-1 text-white drop-shadow-lg max-w-[70%]">
                                    <h3 className="font-bold text-lg leading-tight line-clamp-2">
                                        {video.title}
                                    </h3>
                                    <p className="text-xs text-white/80 line-clamp-1">
                                        {video.description}
                                    </p>
                                </div>
                                <div className="flex flex-col items-center gap-4  mb-2">
                                    <motion.button
                                        whileTap={{ scale: 0.8 }}
                                        onClick={handleLike}
                                        className={`flex flex-col items-center gap-1 group/like ${isLiked ? 'text-red-500' : 'text-white'}`}
                                    >
                                        <div className={`p-2.5 rounded-full transition-colors ${isLiked ? 'bg-red-500/20' : 'bg-white/10 hover:bg-white/20'}`}>
                                            <Heart size={24} fill={isLiked ? "currentColor" : "none"} />
                                        </div>
                                        <span className="text-xs font-bold drop-shadow-md">{likes}</span>
                                    </motion.button>

                                    <button
                                        onClick={(e) => { e.stopPropagation(); setShowComments(true); }}
                                        className="flex flex-col items-center gap-1 text-white"
                                    >
                                        <div className="p-2.5 rounded-full bg-white/10 hover:bg-white/20 transition-colors">
                                            <MessageCircle size={24} />
                                        </div>
                                        <span className="text-xs font-bold drop-shadow-md">Chat</span>
                                    </button>

                                    {user && user.id !== video.creator_id && ( // Only show tip button if logged in and not own video
                                        <button
                                            onClick={(e) => { e.stopPropagation(); setShowTipModal(true); }}
                                            className="flex flex-col items-center gap-1 text-white"
                                        >
                                            <div className="p-2.5 rounded-full bg-white/10 hover:bg-white/20 transition-colors">
                                                <DollarSign size={24} />
                                            </div>
                                            <span className="text-xs font-bold drop-shadow-md">Tip</span>
                                        </button>
                                    )}
                                </div>
                            </div>

                            {/* Views Badge */}
                            <div className="absolute top-4 left-4">
                                <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-black/40 backdrop-blur-md border border-white/10 text-white text-[10px] font-bold uppercase tracking-wider">
                                    <div className="w-1 h-1 rounded-full bg-red-600 animate-pulse" />
                                    <Eye size={12} className="inline" />
                                    {video.views}
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </motion.div>

            <AnimatePresence>
                {showComments && (
                    <CommentsSection
                        videoId={video.id}
                        isOpen={showComments}
                        onClose={() => setShowComments(false)}
                    />
                )}
                {showTipModal && (
                    <TipModal
                        creatorId={video.creator_id}
                        videoId={video.id}
                        isOpen={showTipModal}
                        onClose={() => setShowTipModal(false)}
                    />
                )}
            </AnimatePresence>
        </>
    );
}


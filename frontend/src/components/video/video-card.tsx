import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { interactionService } from '@/lib/api/interactions';
import { useAuthStore } from '@/lib/auth/auth-store';
import { CommentsSection } from './comments-section';
import { Play, Heart, MessageCircle, Share2, MoreHorizontal, Eye, Loader2, X, Pencil, DollarSign, Info } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { VideoResponseDTO } from '@/lib/types';
import { TipModal } from '@/components/modals/tip-modal';
import { sanitizeForReact } from '@/lib/utils/sanitize';


interface VideoProps extends VideoResponseDTO {
    discoveryReasons?: string[];
}

export function VideoCard({ video }: { video: VideoProps }) {
    const router = useRouter();
    const { user } = useAuthStore();
    const [isLiked, setIsLiked] = useState(false);
    const [likes, setLikes] = useState(video.likes || 0);
    const [isHovered, setIsHovered] = useState(false);
    const [showComments, setShowComments] = useState(false);
    const [showTipModal, setShowTipModal] = useState(false);
    const [showDiscoveryReasons, setShowDiscoveryReasons] = useState(false);
    const [showOverlay, setShowOverlay] = useState(false);

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
                className="group relative max-w-sm mx-auto sm:max-w-none"
            >
                <Card className="overflow-hidden border-none bg-zinc-900/50 backdrop-blur-sm shadow-2xl transition-all duration-500 hover:ring-2 hover:ring-blue-500/50">
                    <CardContent className="p-0">
                        {/* Video Player Area */}
                        <div
                            className="relative aspect-[9/16] overflow-hidden bg-black cursor-pointer sm:aspect-video"
                            onClick={() => setShowOverlay(prev => !prev)}
                        >
                            {video.status === 'READY' && video.url ? (
                                <video
                                    src={video.url}
                                    loop
                                    muted
                                    playsInline
                                    className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
                                    poster={video.thumbnail_url || "/placeholder.png"}
                                    onMouseEnter={(e) => (e.target as HTMLVideoElement).play()}
                                    onMouseLeave={(e) => {
                                        const v = e.target as HTMLVideoElement;
                                        v.pause();
                                        v.currentTime = 0;
                                    }}
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        const v = e.target as HTMLVideoElement;
                                        if (v.paused) v.play();
                                        else v.pause();
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
                                        <Image src={video.thumbnail_url} alt="Video thumbnail" fill className="object-cover opacity-20 -z-10" />
                                    )}
                                </div>
                            )}

                            {/* Overlay Controls (Visual Only) */}
                            <div className="absolute inset-0 bg-black/20 group-hover:bg-black/0 transition-colors pointer-events-none" />

                            <div className={`absolute top-2 right-2 sm:top-4 sm:right-4 flex flex-col gap-1 sm:gap-2 transition-opacity duration-300 ${showOverlay ? 'opacity-100 translate-x-0' : 'opacity-100 translate-x-0 md:opacity-0 md:translate-x-4'} md:group-hover:opacity-100 md:group-hover:translate-x-0`}>
                                {user && user.id === video.creator_id && (
                                    <Button
                                        variant="secondary"
                                        size="icon"
                                        className="rounded-full bg-white/20 backdrop-blur-md border-white/20 text-white hover:bg-white/40 h-8 w-8 sm:h-10 sm:w-10"
                                        onClick={handleEdit}
                                    >
                                        <Pencil size={14} className="sm:size-4" />
                                    </Button>
                                )}
                                <Button variant="secondary" size="icon" className="rounded-full bg-white/20 backdrop-blur-md border-white/20 text-white hover:bg-white/40 h-8 w-8 sm:h-10 sm:w-10">
                                    <Share2 size={14} className="sm:size-4" />
                                </Button>
                                <Button variant="secondary" size="icon" className="rounded-full bg-white/20 backdrop-blur-md border-white/20 text-white hover:bg-white/40 h-8 w-8 sm:h-10 sm:w-10">
                                    <MoreHorizontal size={14} className="sm:size-4" />
                                </Button>
                            </div>

                            <div className="absolute bottom-2 left-2 right-2 sm:bottom-4 sm:left-4 sm:right-4 flex items-end justify-between">
                                <div className="space-y-1 text-white drop-shadow-lg max-w-[60%] sm:max-w-[70%]">
                                    <h3 
                                        className="font-bold text-sm sm:text-lg leading-tight line-clamp-2"
                                        dangerouslySetInnerHTML={{ __html: sanitizeForReact(video.title) }}
                                    />
                                    <p 
                                        className="text-xs text-white/80 line-clamp-1"
                                        dangerouslySetInnerHTML={{ __html: sanitizeForReact(video.description) }}
                                    />
                                </div>
                                <div className="flex flex-col items-center gap-2 sm:gap-4 mb-2">
                                    <motion.button
                                        whileTap={{ scale: 0.8 }}
                                        onClick={handleLike}
                                        className={`flex flex-col items-center gap-1 group/like ${isLiked ? 'text-red-500' : 'text-white'}`}
                                    >
                                        <div className={`p-1.5 sm:p-2.5 rounded-full transition-colors ${isLiked ? 'bg-red-500/20' : 'bg-white/10 hover:bg-white/20'}`}>
                                            <Heart size={16} className="sm:size-4" fill={isLiked ? "currentColor" : "none"} />
                                        </div>
                                        <span className="text-[10px] sm:text-xs font-bold drop-shadow-md">{likes}</span>
                                    </motion.button>

                                    <button
                                        onClick={(e) => { e.stopPropagation(); setShowComments(true); }}
                                        className="flex flex-col items-center gap-1 text-white"
                                    >
                                        <div className="p-1.5 sm:p-2.5 rounded-full bg-white/10 hover:bg-white/20 transition-colors">
                                            <MessageCircle size={16} className="sm:size-4" />
                                        </div>
                                        <span className="text-[10px] sm:text-xs font-bold drop-shadow-md">Chat</span>
                                    </button>

                                    {user && user.id !== video.creator_id && ( // Only show tip button if logged in and not own video
                                        <button
                                            onClick={(e) => { e.stopPropagation(); setShowTipModal(true); }}
                                            className="flex flex-col items-center gap-1 text-white"
                                        >
                                            <div className="p-1.5 sm:p-2.5 rounded-full bg-white/10 hover:bg-white/20 transition-colors">
                                                <DollarSign size={16} className="sm:size-4" />
                                            </div>
                                            <span className="text-[10px] sm:text-xs font-bold drop-shadow-md">Tip</span>
                                        </button>
                                    )}
                                </div>
                            </div>

                            {/* Views Badge */}
                            <div className="absolute top-2 left-2 sm:top-4 sm:left-4">
                                <div className="flex items-center gap-1 px-2 py-1 sm:gap-1.5 sm:px-2.5 sm:py-1 rounded-full bg-black/40 backdrop-blur-md border border-white/10 text-white text-[8px] sm:text-[10px] font-bold uppercase tracking-wider">
                                    <div className="w-1 h-1 rounded-full bg-red-600 animate-pulse" />
                                    <Eye size={10} className="inline sm:size-3" />
                                    {video.views}
                                </div>
                            </div>
                        </div>
                    </CardContent>

                    {/* Discovery Score */}
                    {video.discoveryReasons && video.discoveryReasons.length > 0 && (
                        <div className="px-3 pb-2">
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    setShowDiscoveryReasons(!showDiscoveryReasons);
                                }}
                                className="flex items-center gap-1 text-[10px] sm:text-xs text-zinc-400 hover:text-blue-400 transition-colors"
                            >
                                <Info size={12} />
                                <span>Why this?</span>
                            </button>
                            <AnimatePresence>
                                {showDiscoveryReasons && (
                                    <motion.div
                                        initial={{ height: 0, opacity: 0 }}
                                        animate={{ height: 'auto', opacity: 1 }}
                                        exit={{ height: 0, opacity: 0 }}
                                        transition={{ duration: 0.2 }}
                                        className="overflow-hidden"
                                    >
                                        <div className="mt-1.5 p-2 rounded-md bg-zinc-800/80 border border-zinc-700/50">
                                            <p className="text-[10px] sm:text-xs text-zinc-400 font-medium mb-1">Recommended because:</p>
                                            <ul className="space-y-0.5">
                                                {video.discoveryReasons.map((reason, idx) => (
                                                    <li key={idx} className="text-[10px] sm:text-xs text-zinc-500 flex items-start gap-1">
                                                        <span className="text-blue-400 mt-0.5">&#8226;</span>
                                                        <span>{reason}</span>
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    )}
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


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

import React, { useState, useEffect } from 'react';
import { formatDistance, formatNumber } from '@/lib/utils';
import { useAuth } from '@/lib/auth/auth-store';
import { Link } from 'next/link';
import { Sparkles, ArrowRight, Play, Zap, Heart } from 'lucide-react';

// Import hooks for payments and analytics
import { usePayment } from '../hooks/usePayment';
import { useAnalytics } from '../hooks/useAnalytics';
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
                className="group relative max-w-sm mx-auto sm:max-w-none"
            >
                <Card className="overflow-hidden border-none bg-zinc-900/50 backdrop-blur-sm shadow-2xl transition-all duration-500 hover:ring-2 hover:ring-blue-500/50">
                    <CardContent className="p-0">
                        {/* Video Player Area */}
                        <div className="relative aspect-[9/16] overflow-hidden bg-black cursor-pointer sm:aspect-video">
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

                            <div className="absolute top-2 right-2 sm:top-4 sm:right-4 flex flex-col gap-1 sm:gap-2 opacity-0 group-hover:opacity-100 transition-opacity translate-x-4 group-hover:translate-x-0 duration-300">
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
                                    <h3 className="font-bold text-sm sm:text-lg leading-tight line-clamp-2">
                                        {video.title}
                                    </h3>
                                    <p className="text-xs text-white/80 line-clamp-1">
                                        {video.description}
                                    </p>
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


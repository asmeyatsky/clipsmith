import { UserProfile, VideoResponseDTO } from '@/lib/types';
import { User, Video as VideoIcon, Heart, UserPlus, UserMinus } from 'lucide-react';
import { useAuthStore } from '@/lib/auth/auth-store';
import { useEffect, useState } from 'react';
import { userService } from '@/lib/api/user';
import { Button } from '@/components/ui/button';
import { sanitizeForReact } from '@/lib/utils/sanitize';

interface ProfileHeaderProps {
    user: UserProfile;
    videos: VideoResponseDTO[];
}

export function ProfileHeader({ user, videos }: ProfileHeaderProps) {
    const { user: currentUser } = useAuthStore();
    const [isFollowing, setIsFollowing] = useState(false);
    const [followLoading, setFollowLoading] = useState(false);
    const totalLikes = videos.reduce((acc, video) => acc + video.likes, 0);

    useEffect(() => {
        if (currentUser && currentUser.id !== user.id) {
            userService.getFollowStatus(user.id).then(res => {
                setIsFollowing(res.is_following);
            });
        }
    }, [currentUser, user.id]);

    const handleFollowToggle = async () => {
        if (!currentUser) return alert("Login to follow users!");
        if (currentUser.id === user.id) return;

        setFollowLoading(true);
        try {
            if (isFollowing) {
                await userService.unfollow(user.id);
                setIsFollowing(false);
            } else {
                await userService.follow(user.id);
                setIsFollowing(true);
            }
        } catch (error) {
            console.error("Failed to toggle follow status:", error);
            alert("Failed to update follow status.");
        } finally {
            setFollowLoading(false);
        }
    };

    return (
        <div className="bg-white dark:bg-zinc-900 rounded-2xl p-8 mb-8 shadow-sm border border-gray-100 dark:border-zinc-800">
            <div className="flex flex-col md:flex-row items-center gap-8">
                {/* Avatar */}
                <div className="w-32 h-32 rounded-full bg-gradient-to-br from-blue-500 to-violet-500 flex items-center justify-center text-white shadow-lg">
                    <User size={64} />
                </div>

                {/* Info */}
                <div className="text-center md:text-left flex-1">
                    <h1 
                    className="text-3xl font-bold mb-2"
                    dangerouslySetInnerHTML={{ __html: sanitizeForReact(user.username) }}
                />
                    <p className="text-gray-500 dark:text-gray-400 mb-6">Content Creator</p>

                    {/* Stats */}
                    <div className="flex items-center justify-center md:justify-start gap-8">
                        <div className="flex flex-col items-center md:items-start">
                            <div className="flex items-center gap-2 font-bold text-xl">
                                <VideoIcon size={20} className="text-blue-500" />
                                {videos.length}
                            </div>
                            <span className="text-sm text-gray-500">Videos</span>
                        </div>
                        <div className="flex flex-col items-center md:items-start">
                            <div className="flex items-center gap-2 font-bold text-xl">
                                <Heart size={20} className="text-red-500" />
                                {totalLikes}
                            </div>
                            <span className="text-sm text-gray-500">Likes</span>
                        </div>
                    </div>
                </div>

                <div className="flex gap-3">
                    {currentUser && currentUser.id !== user.id && (
                        <Button
                            onClick={handleFollowToggle}
                            disabled={followLoading}
                            className="px-6 py-2 bg-black dark:bg-white text-white dark:text-black rounded-full font-semibold hover:opacity-90 transition-opacity"
                        >
                            {followLoading ? (
                                <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                            ) : (
                                isFollowing ? (
                                    <>
                                        <UserMinus size={18} className="mr-2" /> Following
                                    </>
                                ) : (
                                    <>
                                        <UserPlus size={18} className="mr-2" /> Follow
                                    </>
                                )
                            )}
                        </Button>
                    )}
                </div>
            </div>
        </div>
    );
}

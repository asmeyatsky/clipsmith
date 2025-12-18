import { UserProfile, VideoResponseDTO } from '@/lib/types';
import { User, Video as VideoIcon, Heart } from 'lucide-react';

interface ProfileHeaderProps {
    user: UserProfile;
    videos: VideoResponseDTO[];
}

export function ProfileHeader({ user, videos }: ProfileHeaderProps) {
    const totalLikes = videos.reduce((acc, video) => acc + video.likes, 0);

    return (
        <div className="bg-white dark:bg-zinc-900 rounded-2xl p-8 mb-8 shadow-sm border border-gray-100 dark:border-zinc-800">
            <div className="flex flex-col md:flex-row items-center gap-8">
                {/* Avatar */}
                <div className="w-32 h-32 rounded-full bg-gradient-to-br from-blue-500 to-violet-500 flex items-center justify-center text-white shadow-lg">
                    <User size={64} />
                </div>

                {/* Info */}
                <div className="text-center md:text-left flex-1">
                    <h1 className="text-3xl font-bold mb-2">{user.username}</h1>
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
                    {/* Placeholder for Follow button */}
                    <button className="px-6 py-2 bg-black dark:bg-white text-white dark:text-black rounded-full font-semibold hover:opacity-90 transition-opacity">
                        Follow
                    </button>
                </div>
            </div>
        </div>
    );
}

import { useState, useEffect } from 'react';
import { interactionService, Comment } from '@/lib/api/interactions';
import { Send, User } from 'lucide-react';
import { useAuthStore } from '@/lib/auth/auth-store';

interface CommentsSectionProps {
    videoId: string;
    isOpen: boolean;
    onClose: () => void;
}

export function CommentsSection({ videoId, isOpen, onClose }: CommentsSectionProps) {
    const [comments, setComments] = useState<Comment[]>([]);
    const [newComment, setNewComment] = useState('');
    const [loading, setLoading] = useState(false);
    const { user } = useAuthStore();

    useEffect(() => {
        if (isOpen) {
            loadComments();
        }
    }, [isOpen, videoId]);

    const loadComments = async () => {
        try {
            const data = await interactionService.listComments(videoId);
            setComments(data);
        } catch (error) {
            console.error(error);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newComment.trim()) return;

        try {
            setLoading(true);
            const comment = await interactionService.addComment(videoId, newComment);
            setComments([comment, ...comments]);
            setNewComment('');
        } catch (error) {
            alert("Failed to post comment");
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center pointer-events-none">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/50 pointer-events-auto"
                onClick={onClose}
            />

            {/* Modal */}
            <div className="relative w-full max-w-lg bg-white dark:bg-zinc-900 rounded-t-2xl sm:rounded-2xl shadow-2xl pointer-events-auto flex flex-col max-h-[80vh]">
                <div className="p-4 border-b border-gray-100 dark:border-zinc-800 flex justify-between items-center">
                    <h3 className="font-bold text-lg">Comments ({comments.length})</h3>
                    <button onClick={onClose} className="text-gray-500 hover:text-gray-700">Close</button>
                </div>

                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                    {comments.length === 0 ? (
                        <p className="text-center text-gray-500 py-10">No comments yet. Be the first!</p>
                    ) : (
                        comments.map((comment) => (
                            <div key={comment.id} className="flex gap-3">
                                <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center shrink-0">
                                    <User size={14} className="text-blue-600" />
                                </div>
                                <div>
                                    <p className="text-sm font-semibold flex items-center gap-2">
                                        {comment.username}
                                        <span className="text-xs text-gray-400 font-normal">
                                            {new Date(comment.created_at).toLocaleDateString()}
                                        </span>
                                    </p>
                                    <p className="text-sm text-gray-700 dark:text-gray-300 mt-0.5">
                                        {comment.content}
                                    </p>
                                </div>
                            </div>
                        ))
                    )}
                </div>

                {user ? (
                    <form onSubmit={handleSubmit} className="p-4 border-t border-gray-100 dark:border-zinc-800 flex gap-2">
                        <input
                            type="text"
                            placeholder="Add a comment..."
                            value={newComment}
                            onChange={(e) => setNewComment(e.target.value)}
                            className="flex-1 bg-gray-100 dark:bg-zinc-800 rounded-full px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <button
                            type="submit"
                            disabled={loading || !newComment.trim()}
                            className="p-2 bg-blue-600 text-white rounded-full hover:bg-blue-700 disabled:opacity-50"
                        >
                            <Send size={18} />
                        </button>
                    </form>
                ) : (
                    <div className="p-4 text-center text-sm text-gray-500 border-t border-gray-100 dark:border-zinc-800">
                        Please log in to comment.
                    </div>
                )}
            </div>
        </div>
    );
}

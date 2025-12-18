import { useState, useEffect } from 'react';
import { useAuthStore } from '@/lib/auth/auth-store';
import { getBaseUrl } from '@/lib/api/client';
import { Upload, X, Film, Check, Loader2, Info } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
    DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { motion, AnimatePresence } from 'framer-motion';
import { VideoResponseDTO } from '@/lib/types';

export function UploadModal({ onUploadSuccess }: { onUploadSuccess?: () => void }) {
    const { token } = useAuthStore();
    const [isOpen, setIsOpen] = useState(false);
    const [file, setFile] = useState<File | null>(null);
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [uploading, setUploading] = useState(false); // Only for initial file upload
    const [error, setError] = useState('');

    // New states for video processing
    const [videoId, setVideoId] = useState<string | null>(null);
    const [processingStatus, setProcessingStatus] = useState<'idle' | 'uploading' | 'processing' | 'ready' | 'failed' | 'polling'>('idle');
    const [processedVideoData, setProcessedVideoData] = useState<VideoResponseDTO | null>(null);

    // Reset all states when modal is closed
    const resetModal = () => {
        setFile(null);
        setTitle('');
        setDescription('');
        setUploading(false);
        setError('');
        setVideoId(null);
        setProcessingStatus('idle');
        setProcessedVideoData(null);
    };

    useEffect(() => {
        if (!isOpen) {
            resetModal();
        }
    }, [isOpen]);

    useEffect(() => {
        let pollInterval: NodeJS.Timeout;

        if ((processingStatus === 'processing' || processingStatus === 'polling') && videoId && token) {
            pollInterval = setInterval(async () => {
                try {
                    const response = await fetch(`${getBaseUrl()}/videos/${videoId}`, {
                        headers: {
                            'Authorization': `Bearer ${token}`
                        }
                    });

                    if (!response.ok) {
                        throw new Error('Failed to fetch video status');
                    }

                    const data: VideoResponseDTO = await response.json();
                    setProcessedVideoData(data);

                    if (data.status === 'READY') {
                        setProcessingStatus('ready');
                        clearInterval(pollInterval);
                        if (onUploadSuccess) onUploadSuccess();
                        setTimeout(() => setIsOpen(false), 1000); // Close modal after a short delay
                    } else if (data.status === 'FAILED') {
                        setProcessingStatus('failed');
                        setError('Video processing failed.');
                        clearInterval(pollInterval);
                    } else {
                        setProcessingStatus('polling'); // Keep polling
                    }
                } catch (err: any) {
                    setError(err.message || 'Error checking video status');
                    setProcessingStatus('failed');
                    clearInterval(pollInterval);
                }
            }, 3000); // Poll every 3 seconds
        }

        return () => clearInterval(pollInterval); // Cleanup on unmount or status change
    }, [videoId, processingStatus, token, onUploadSuccess]);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!file || !title) return;

        setUploading(true);
        setError('');
        setProcessingStatus('uploading');

        const formData = new FormData();
        formData.append('title', title);
        formData.append('description', description);
        formData.append('file', file);

        try {
            const response = await fetch(`${getBaseUrl()}/videos/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Upload failed');
            }
            
            const data: VideoResponseDTO = await response.json();
            setVideoId(data.id);
            setProcessingStatus('processing');
            setProcessedVideoData(data); // Initial data from upload response

            // Do not close modal or call onUploadSuccess here, wait for processing to complete
        } catch (err: any) {
            setError(err.message || 'Upload failed');
            setProcessingStatus('failed');
        } finally {
            setUploading(false);
        }
    };

    if (!token) return null;

    return (
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
            <DialogTrigger asChild>
                <Button className="rounded-full gap-2 px-6 h-11 bg-blue-600 hover:bg-blue-700 shadow-lg shadow-blue-500/20">
                    <Upload size={18} />
                    Share Clip
                </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[500px] border-none bg-white dark:bg-zinc-950 p-0 overflow-hidden rounded-[2rem] shadow-2xl">
                <div className="bg-gradient-to-br from-blue-600 to-indigo-700 p-8 text-white relative">
                    <DialogHeader>
                        <DialogTitle className="text-2xl font-black tracking-tight">Post your Magic</DialogTitle>
                    </DialogHeader>
                    <p className="text-blue-100 text-sm mt-2 font-medium opacity-80">Share your story with the clipsmith community.</p>
                    <div className="absolute top-8 right-8 w-16 h-16 bg-white/10 rounded-full blur-2xl pointer-events-none" />
                </div>

                <form onSubmit={handleSubmit} className="p-8 space-y-6">
                    {error && (
                        <motion.div
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className="p-4 bg-red-500/10 border border-red-500/20 rounded-2xl text-red-500 text-xs font-bold uppercase tracking-wider text-center"
                        >
                            {error}
                        </motion.div>
                    )}

                    {processingStatus === 'idle' || processingStatus === 'uploading' || processingStatus === 'failed' ? (
                        <>
                            <div className="relative group/upload">
                                <label className={`
                                    flex flex-col items-center justify-center h-40 border-2 border-dashed rounded-[2rem] transition-all cursor-pointer
                                    ${file ? 'border-blue-500 bg-blue-50/30' : 'border-zinc-200 dark:border-zinc-800 hover:border-blue-500 hover:bg-zinc-50 dark:hover:bg-zinc-900/50'}
                                `}>
                                    <input
                                        type="file"
                                        accept="video/*"
                                        onChange={handleFileChange}
                                        className="hidden"
                                        required
                                    />
                                    <div className="flex flex-col items-center gap-3">
                                        {file ? (
                                            <>
                                                <div className="w-12 h-12 rounded-full bg-blue-500 flex items-center justify-center text-white shadow-lg">
                                                    <Check size={24} />
                                                </div>
                                                <p className="text-sm font-bold text-blue-600 max-w-[200px] truncate">{file.name}</p>
                                            </>
                                        ) : (
                                            <>
                                                <div className="w-12 h-12 rounded-full bg-zinc-100 dark:bg-zinc-900 flex items-center justify-center text-zinc-400 group-hover/upload:scale-110 transition-transform">
                                                    <Film size={24} />
                                                </div>
                                                <div className="text-center">
                                                    <p className="text-sm font-bold">Select a Video</p>
                                                    <p className="text-[10px] uppercase font-black text-zinc-400 mt-1">MP4, WebM (Max 100MB)</p>
                                                </div>
                                            </>
                                        )}
                                    </div>
                                </label>
                            </div>

                            <div className="space-y-4">
                                <div className="space-y-1.5">
                                    <label className="text-[10px] uppercase font-black tracking-widest text-zinc-500 px-1">Title</label>
                                    <Input
                                        placeholder="Give it a catchy name..."
                                        value={title}
                                        onChange={(e) => setTitle(e.target.value)}
                                        className="rounded-2xl h-12 bg-zinc-50 dark:bg-zinc-900 border-none ring-1 ring-zinc-200 dark:ring-zinc-800 focus-visible:ring-2 focus-visible:ring-blue-500"
                                        required
                                    />
                                </div>

                                <div className="space-y-1.5">
                                    <label className="text-[10px] uppercase font-black tracking-widest text-zinc-500 px-1">Story</label>
                                    <textarea
                                        placeholder="What's happening in this clip?"
                                        value={description}
                                        onChange={(e) => setDescription(e.target.value)}
                                        className="w-full rounded-2xl p-4 bg-zinc-50 dark:bg-zinc-900 ring-1 ring-zinc-200 dark:ring-zinc-800 focus:ring-2 focus:ring-blue-500 outline-none transition-all resize-none h-24 text-sm"
                                    />
                                </div>
                            </div>
                        </>
                    ) : (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="p-8 space-y-6 text-center"
                        >
                            {processingStatus === 'processing' || processingStatus === 'polling' ? (
                                <div className="flex flex-col items-center gap-4">
                                    <Loader2 className="w-12 h-12 text-blue-500 animate-spin" />
                                    <p className="text-lg font-bold text-zinc-700 dark:text-zinc-300">Processing your video...</p>
                                    <p className="text-sm text-zinc-500 dark:text-zinc-400">This might take a moment. We'll notify you when it's ready!</p>
                                </div>
                            ) : processingStatus === 'ready' ? (
                                <div className="flex flex-col items-center gap-4">
                                    <Check className="w-12 h-12 text-green-500" />
                                    <p className="text-lg font-bold text-zinc-700 dark:text-zinc-300">Video is ready!</p>
                                    <p className="text-sm text-zinc-500 dark:text-zinc-400">Your clip has been processed and is now available.</p>
                                </div>
                            ) : processingStatus === 'failed' ? (
                                <div className="flex flex-col items-center gap-4">
                                    <X className="w-12 h-12 text-red-500" />
                                    <p className="text-lg font-bold text-zinc-700 dark:text-zinc-300">Processing failed!</p>
                                    <p className="text-sm text-zinc-500 dark:text-zinc-400">{error || "Something went wrong during processing."}</p>
                                </div>
                            ) : null}
                        </motion.div>
                    )}

                    <DialogFooter className="pt-2">
                        <Button
                            type="submit"
                            disabled={processingStatus !== 'idle' && processingStatus !== 'failed' || !file || !title} // Disable if processing, uploading, or no file/title, allow retry on failed
                            className="w-full h-12 rounded-full font-bold text-lg bg-zinc-900 dark:bg-white text-white dark:text-black hover:scale-[1.02] transition-transform active:scale-95 disabled:opacity-50"
                        >
                            {processingStatus === 'uploading' ? (
                                <span className="flex items-center gap-2">
                                    <motion.div
                                        animate={{ rotate: 360 }}
                                        transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                                        className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full"
                                    />
                                    Uploading...
                                </span>
                            ) : processingStatus === 'processing' || processingStatus === 'polling' ? (
                                <span className="flex items-center gap-2">
                                    <motion.div
                                        animate={{ rotate: 360 }}
                                        transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                                        className="w-5 h-5 border-2 border-blue-200 border-t-blue-500 rounded-full"
                                    />
                                    Processing...
                                </span>
                            ) : processingStatus === 'ready' ? (
                                <span className="flex items-center gap-2">
                                    <Check size={20} />
                                    Video Ready!
                                </span>
                            ) : 'Post Now'}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}


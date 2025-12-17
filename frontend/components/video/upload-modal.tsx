'use client';

import { useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { useAuthStore } from '@/lib/auth/auth-store';
import { Upload, X } from 'lucide-react';
import { apiClient } from '@/lib/api/client';

export function UploadModal({ onUploadSuccess }: { onUploadSuccess?: () => void }) {
    const { token } = useAuthStore();
    const [isOpen, setIsOpen] = useState(false);
    const [file, setFile] = useState<File | null>(null);
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState('');

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

        const formData = new FormData();
        formData.append('title', title);
        formData.append('description', description);
        formData.append('file', file);

        try {
            // We use fetch directly here because apiClient wrapper assumes JSON
            // but we are sending FormData. We still need the token.
            const response = await fetch('http://localhost:8001/videos/', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData
            });

            if (!response.ok) {
                throw new Error('Upload failed');
            }

            setIsOpen(false);
            setFile(null);
            setTitle('');
            setDescription('');
            if (onUploadSuccess) onUploadSuccess();
        } catch (err: any) {
            setError(err.message || 'Upload failed');
        } finally {
            setUploading(false);
        }
    };

    if (!token) return null;

    return (
        <Dialog.Root open={isOpen} onOpenChange={setIsOpen}>
            <Dialog.Trigger asChild>
                <button className="flex items-center gap-2 px-6 py-2.5 rounded-full bg-blue-600 text-white font-semibold hover:bg-blue-700 transition-colors shadow-lg">
                    <Upload size={18} />
                    Upload
                </button>
            </Dialog.Trigger>
            <Dialog.Portal>
                <Dialog.Overlay className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 animate-in fade-in" />
                <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-lg bg-white dark:bg-zinc-900 p-6 rounded-2xl shadow-2xl z-50 animate-in zoom-in-95 border border-gray-100 dark:border-zinc-800">
                    <div className="flex justify-between items-center mb-6">
                        <Dialog.Title className="text-xl font-bold">Upload Video</Dialog.Title>
                        <Dialog.Close className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-zinc-800 transition-colors">
                            <X size={20} />
                        </Dialog.Close>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-6">
                        {error && <div className="p-3 bg-red-50 text-red-500 rounded-lg text-sm">{error}</div>}

                        <div className="border-2 border-dashed border-gray-300 dark:border-zinc-700 rounded-xl p-8 text-center hover:border-blue-500 transition-colors cursor-pointer relative">
                            <input
                                type="file"
                                accept="video/*"
                                onChange={handleFileChange}
                                className="absolute inset-0 opacity-0 cursor-pointer"
                                required
                            />
                            {file ? (
                                <div className="text-blue-600 font-medium">{file.name}</div>
                            ) : (
                                <div className="text-gray-500">
                                    <Upload className="mx-auto mb-2 opacity-50" size={32} />
                                    <span className="font-medium">Click directly to upload</span>
                                    <span className="block text-xs mt-1">MP4, WebM (Max 100MB)</span>
                                </div>
                            )}
                        </div>

                        <div>
                            <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">Title</label>
                            <input
                                type="text"
                                className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition-all dark:bg-zinc-800 dark:border-zinc-700"
                                value={title}
                                onChange={(e) => setTitle(e.target.value)}
                                required
                                placeholder="My awesome video"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">Description</label>
                            <textarea
                                className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition-all dark:bg-zinc-800 dark:border-zinc-700 resize-none h-24"
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                placeholder="Tell us about your clip..."
                            />
                        </div>

                        <div className="flex justify-end gap-3">
                            <Dialog.Close asChild>
                                <button type="button" className="px-5 py-2.5 rounded-xl text-gray-600 hover:bg-gray-100 font-medium transition-colors dark:text-gray-400 dark:hover:bg-zinc-800">
                                    Cancel
                                </button>
                            </Dialog.Close>
                            <button
                                type="submit"
                                disabled={uploading}
                                className="px-6 py-2.5 rounded-xl bg-blue-600 text-white font-semibold hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {uploading ? 'Uploading...' : 'Post Video'}
                            </button>
                        </div>
                    </form>
                </Dialog.Content>
            </Dialog.Portal>
        </Dialog.Root>
    );
}

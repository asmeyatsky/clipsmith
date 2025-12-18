'use client';

import Link from 'next/link';
import { useAuthStore } from '@/lib/auth/auth-store';
import { Button } from '@/components/ui/button';
import { motion } from 'framer-motion';
import { LogOut, User, Video, Plus, Search } from 'lucide-react';
import { UploadModal } from '@/components/video/upload-modal';

export function Navbar() {
    const { user, logout } = useAuthStore();

    return (
        <motion.nav
            initial={{ y: -100, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="fixed top-4 left-1/2 -translate-x-1/2 z-50 w-full max-w-5xl px-4"
        >
            <div className="bg-white/70 dark:bg-zinc-950/70 backdrop-blur-xl border border-white/20 dark:border-zinc-800/50 rounded-full px-6 py-3 shadow-2xl flex items-center justify-between">
                <Link href="/" className="flex items-center gap-2 group">
                    <div className="w-8 h-8 bg-gradient-to-tr from-blue-600 to-violet-600 rounded-lg flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
                        <Video className="text-white w-5 h-5" />
                    </div>
                    <span className="text-xl font-bold bg-gradient-to-r from-blue-600 to-violet-600 bg-clip-text text-transparent">
                        clipsmith
                    </span>
                </Link>

                <div className="flex items-center gap-4">
                    {user ? (
                        <div className="flex items-center gap-3">
                            <UploadModal onUploadSuccess={() => window.location.reload()} />
                            <Link href={`/profile/${user.username}`}>
                                <Button variant="ghost" size="icon" className="rounded-full hover:bg-zinc-100 dark:hover:bg-zinc-900">
                                    <User className="w-5 h-5" />
                                </Button>
                            </Link>
                            <Button
                                variant="ghost"
                                size="icon"
                                onClick={logout}
                                className="rounded-full text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950/30"
                            >
                                <LogOut className="w-5 h-5" />
                            </Button>
                        </div>
                    ) : (
                        <div className="flex items-center gap-2">
                            <Link href="/login">
                                <Button variant="ghost" className="rounded-full">Log In</Button>
                            </Link>
                            <Link href="/register">
                                <Button className="rounded-full bg-gradient-to-r from-blue-600 to-violet-600 hover:shadow-lg transition-all">
                                    Get Started
                                </Button>
                            </Link>
                        </div>
                    )}
                </div>
            </div>
        </motion.nav>
    );
}

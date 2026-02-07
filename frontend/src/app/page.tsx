'use client';

import Link from 'next/link';
import { useAuthStore } from '@/lib/auth/auth-store';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Sparkles, ArrowRight, Play, Zap, Shield, Heart } from 'lucide-react';
import { VideoFeed } from '@/components/video/video-feed';
import { CreatorDashboard } from '@/components/CreatorDashboard';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Sparkles, ArrowRight, Play, Zap, Shield, Heart } from 'lucide-react';

export default function Home() {
    const { user } = useAuthStore();
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
    }, []);

    if (!mounted) return null;

    return (
        <div className="flex flex-col gap-20 pb-40 overflow-hidden">
            {/* Hero Section */}
            <section className="relative pt-20 pb-10 px-6">
                <div className="max-w-7xl mx-auto flex flex-col items-center text-center relative z-10">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-500 text-sm font-semibold mb-8"
                    >
                        <Sparkles size={16} />
                        <span>The Future of Social Video</span>
                    </motion.div>

                    <motion.h1
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className="text-6xl md:text-8xl font-black tracking-tight mb-8 leading-[1.1]"
                    >
                        Create. Share. <br />
                        <span className="bg-gradient-to-r from-blue-600 via-violet-600 to-indigo-600 bg-clip-text text-transparent">
                            Inspire the World.
                        </span>
                    </motion.h1>

                    <motion.p
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className="text-xl text-zinc-600 dark:text-zinc-400 max-w-2xl mb-12 leading-relaxed"
                    >
                        Clipsmith gives you the tools to craft stunning short-form videos, build your community, and share your unique vision with the universe.
                    </motion.p>

                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.3 }}
                        className="flex flex-col sm:flex-row gap-4 items-center"
                    >
                        {!user ? (
                            <>
                                <Link href="/register">
                                    <Button size="lg" className="h-14 px-8 rounded-full text-lg bg-blue-600 hover:bg-blue-700 shadow-xl shadow-blue-500/20">
                                        Get Started Free
                                        <ArrowRight className="ml-2" />
                                    </Button>
                                </Link>
                                <Button size="lg" variant="outline" className="h-14 px-8 rounded-full text-lg border-zinc-200 dark:border-zinc-800">
                                    Watch the Demo
                                    <Play className="ml-2 fill-current" size={16} />
                                </Button>
                            </>
                        ) : (
                            <Link href={`/profile/${user.username}`}>
                                <Button size="lg" className="h-14 px-8 rounded-full text-lg bg-zinc-900 dark:bg-white text-white dark:text-black">
                                    Go to Dashboard
                                    <ArrowRight className="ml-2" />
                                </Button>
                            </Link>
                        )}
                    </motion.div>
                </div>

                {/* Background Decorative Elements */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full -z-0">
                    <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-[120px] animate-pulse" />
                    <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-violet-500/10 rounded-full blur-[120px] animate-pulse delay-1000" />
                </div>
            </section>

            {/* Feature Stats */}
            <motion.section
                initial={{ opacity: 0 }}
                whileInView={{ opacity: 1 }}
                viewport={{ once: true }}
                className="max-w-7xl mx-auto w-full px-6"
            >
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8 p-8 rounded-[3rem] bg-zinc-900/5 dark:bg-zinc-900/40 border border-zinc-200/50 dark:border-zinc-800/50 backdrop-blur-sm">
                    <div className="flex items-center gap-4 px-6 py-4">
                        <div className="w-12 h-12 rounded-2xl bg-blue-500/10 flex items-center justify-center text-blue-500">
                            <Zap size={24} />
                        </div>
                        <div>
                            <h4 className="font-bold text-lg">Lightning Fast</h4>
                            <p className="text-sm text-zinc-500">Real-time uploads & processing</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-4 px-6 py-4 border-l border-zinc-200/50 dark:border-zinc-800/50">
                        <div className="w-12 h-12 rounded-2xl bg-violet-500/10 flex items-center justify-center text-violet-500">
                            <Shield size={24} />
                        </div>
                        <div>
                            <h4 className="font-bold text-lg">Secure & Private</h4>
                            <p className="text-sm text-zinc-500">Encryption at every layer</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-4 px-6 py-4 border-l border-zinc-200/50 dark:border-zinc-800/50">
                        <div className="w-12 h-12 rounded-2xl bg-pink-500/10 flex items-center justify-center text-pink-500">
                            <Heart size={24} />
                        </div>
                        <div>
                            <h4 className="font-bold text-lg">Community Driven</h4>
                            <p className="text-sm text-zinc-500">Built for creators, by creators</p>
                        </div>
                    </div>
                </div>
            </motion.section>

            {/* Video Feed Section */}
            <section className="max-w-7xl mx-auto w-full px-6">
                <div className="flex flex-col md:flex-row items-end justify-between gap-6 mb-12">
                    <div className="space-y-2">
                        <h2 className="text-4xl font-black tracking-tight">Trending Now</h2>
                        <p className="text-zinc-500">Catch the latest viral moments on Clipsmith</p>
                    </div>
                    <div className="flex gap-2 p-1.5 rounded-full bg-zinc-100 dark:bg-zinc-900">
                        <Button variant="secondary" size="sm" className="rounded-full shadow-sm">All</Button>
                        <Button variant="ghost" size="sm" className="rounded-full">Gaming</Button>
                        <Button variant="ghost" size="sm" className="rounded-full">Tech</Button>
                        <Button variant="ghost" size="sm" className="rounded-full">Life</Button>
                    </div>
                </div>

                <VideoFeed />
            </section>
        </div>
    );
}


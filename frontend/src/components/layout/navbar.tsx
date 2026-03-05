'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState, useEffect } from 'react';
import { useAuthStore } from '@/lib/auth/auth-store';
import { Button } from '@/components/ui/button';
import { motion } from 'framer-motion';
import { LogOut, User, Video, Search, Moon, Sun, X, DollarSign, Layout, Compass, Users, MessageSquare, GraduationCap, Menu } from 'lucide-react';
import { UploadModal } from '@/components/video/upload-modal';

export function Navbar() {
    const { user, logout } = useAuthStore();
    const router = useRouter();
    const [searchQuery, setSearchQuery] = useState('');
    const [showSearch, setShowSearch] = useState(false);
    const [isDark, setIsDark] = useState(false);
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

    useEffect(() => {
        const savedTheme = localStorage.getItem('theme');
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const isDarkMode = savedTheme === 'dark' || (!savedTheme && prefersDark);
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setIsDark(isDarkMode);
        document.documentElement.classList.toggle('dark', isDarkMode);
    }, []);

    const toggleDarkMode = () => {
        const newDark = !isDark;
        setIsDark(newDark);
        localStorage.setItem('theme', newDark ? 'dark' : 'light');
        document.documentElement.classList.toggle('dark', newDark);
    };

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        if (searchQuery.trim()) {
            router.push(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
            setShowSearch(false);
            setSearchQuery('');
        }
    };

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
                    {showSearch ? (
                        <form onSubmit={handleSearch} className="flex items-center gap-2">
                            <input
                                type="text"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                placeholder="Search videos..."
                                className="px-3 py-1.5 rounded-full bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 w-48"
                                autoFocus
                            />
                            <Button type="button" variant="ghost" size="icon" className="rounded-full" onClick={() => setShowSearch(false)}>
                                <X className="w-4 h-4" />
                            </Button>
                        </form>
                    ) : (
                        <Button variant="ghost" size="icon" className="rounded-full hover:bg-zinc-100 dark:hover:bg-zinc-900" onClick={() => setShowSearch(true)}>
                            <Search className="w-5 h-5" />
                        </Button>
                    )}

                    <Button variant="ghost" size="icon" className="rounded-full hover:bg-zinc-100 dark:hover:bg-zinc-900" onClick={toggleDarkMode}>
                        {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                    </Button>

                    {user ? (
                        <>
                            {/* Desktop nav links */}
                            <div className="hidden md:flex items-center gap-2">
                                <Link href="/discover">
                                    <Button variant="ghost" size="sm" className="rounded-full gap-1">
                                        <Compass className="w-4 h-4" />
                                        <span className="hidden sm:inline">Discover</span>
                                    </Button>
                                </Link>
                                <Link href="/templates">
                                    <Button variant="ghost" size="sm" className="rounded-full gap-1">
                                        <Layout className="w-4 h-4" />
                                        <span className="hidden sm:inline">Templates</span>
                                    </Button>
                                </Link>
                                <Link href="/monetization">
                                    <Button variant="ghost" size="sm" className="rounded-full gap-1">
                                        <DollarSign className="w-4 h-4" />
                                        <span className="hidden sm:inline">Earn</span>
                                    </Button>
                                </Link>
                                <Link href="/community">
                                    <Button variant="ghost" size="sm" className="rounded-full gap-1">
                                        <Users className="w-4 h-4" />
                                        <span className="hidden sm:inline">Community</span>
                                    </Button>
                                </Link>
                                <Link href="/messages">
                                    <Button variant="ghost" size="sm" className="rounded-full gap-1">
                                        <MessageSquare className="w-4 h-4" />
                                        <span className="hidden sm:inline">Messages</span>
                                    </Button>
                                </Link>
                                <Link href="/courses">
                                    <Button variant="ghost" size="sm" className="rounded-full gap-1">
                                        <GraduationCap className="w-4 h-4" />
                                        <span className="hidden sm:inline">Courses</span>
                                    </Button>
                                </Link>
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
                            {/* Mobile hamburger button */}
                            <Button
                                variant="ghost"
                                size="icon"
                                className="md:hidden rounded-full"
                                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                            >
                                {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
                            </Button>
                        </>
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

            {/* Mobile Menu */}
            {mobileMenuOpen && user && (
                <div className="md:hidden mt-2 bg-white/70 dark:bg-zinc-950/70 backdrop-blur-xl border border-white/20 dark:border-zinc-800/50 rounded-2xl px-4 py-4 shadow-2xl flex flex-col gap-1 pb-[env(safe-area-inset-bottom)]">
                    <Link href="/discover" onClick={() => setMobileMenuOpen(false)}>
                        <Button variant="ghost" className="w-full justify-start gap-3 rounded-xl">
                            <Compass className="w-5 h-5" /> Discover
                        </Button>
                    </Link>
                    <Link href="/templates" onClick={() => setMobileMenuOpen(false)}>
                        <Button variant="ghost" className="w-full justify-start gap-3 rounded-xl">
                            <Layout className="w-5 h-5" /> Templates
                        </Button>
                    </Link>
                    <Link href="/monetization" onClick={() => setMobileMenuOpen(false)}>
                        <Button variant="ghost" className="w-full justify-start gap-3 rounded-xl">
                            <DollarSign className="w-5 h-5" /> Earn
                        </Button>
                    </Link>
                    <Link href="/community" onClick={() => setMobileMenuOpen(false)}>
                        <Button variant="ghost" className="w-full justify-start gap-3 rounded-xl">
                            <Users className="w-5 h-5" /> Community
                        </Button>
                    </Link>
                    <Link href="/messages" onClick={() => setMobileMenuOpen(false)}>
                        <Button variant="ghost" className="w-full justify-start gap-3 rounded-xl">
                            <MessageSquare className="w-5 h-5" /> Messages
                        </Button>
                    </Link>
                    <Link href="/courses" onClick={() => setMobileMenuOpen(false)}>
                        <Button variant="ghost" className="w-full justify-start gap-3 rounded-xl">
                            <GraduationCap className="w-5 h-5" /> Courses
                        </Button>
                    </Link>
                    <Link href={`/profile/${user.username}`} onClick={() => setMobileMenuOpen(false)}>
                        <Button variant="ghost" className="w-full justify-start gap-3 rounded-xl">
                            <User className="w-5 h-5" /> Profile
                        </Button>
                    </Link>
                    <div className="border-t border-zinc-200 dark:border-zinc-800 my-1" />
                    <Button
                        variant="ghost"
                        onClick={() => { logout(); setMobileMenuOpen(false); }}
                        className="w-full justify-start gap-3 rounded-xl text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950/30"
                    >
                        <LogOut className="w-5 h-5" /> Log Out
                    </Button>
                </div>
            )}
        </motion.nav>
    );
}

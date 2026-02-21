'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api/client';
import { VideoCard } from '@/components/video/video-card';
import { TrendingUp, Compass, Flame, Music, Gamepad2, BookOpen, Newspaper, Laptop, Shirt, Utensils, Plane, Dumbbell } from 'lucide-react';

interface Video {
  id: string;
  title: string;
  description: string;
  url: string;
  thumbnail_url: string;
  creator_id: string;
  views: number;
  likes: number;
  duration: number;
  created_at: string;
}

interface Category {
  id: string;
  name: string;
  icon: string;
}

const categoryIcons: Record<string, React.ElementType> = {
  entertainment: TrendingUp,
  gaming: Gamepad2,
  music: Music,
  education: BookOpen,
  sports: Flame,
  comedy: TrendingUp,
  news: Newspaper,
  tech: Laptop,
  fashion: Shirt,
  food: Utensils,
  travel: Plane,
  fitness: Dumbbell,
};

export default function DiscoverPage() {
  const [activeTab, setActiveTab] = useState<'trending' | 'categories' | 'recommended'>('trending');
  const [videos, setVideos] = useState<Video[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadCategories();
  }, []);

  useEffect(() => {
    if (activeTab === 'trending') {
      loadTrending();
    } else if (activeTab === 'recommended') {
      loadRecommended();
    } else if (activeTab === 'categories' && selectedCategory) {
      loadCategoryVideos(selectedCategory);
    }
  }, [activeTab, selectedCategory]);

  const loadCategories = async () => {
    try {
      const data = await apiClient<{ categories: Category[] }>('/feed/categories');
      setCategories(data.categories);
    } catch (e) {
      console.error('Error loading categories:', e);
    }
  };

  const loadTrending = async () => {
    setIsLoading(true);
    try {
      const data = await apiClient<{ items: Video[] }>('/feed/trending?page=1&page_size=20');
      setVideos(data.items || []);
    } catch (e) {
      console.error('Error loading trending:', e);
    } finally {
      setIsLoading(false);
    }
  };

  const loadRecommended = async () => {
    setIsLoading(true);
    try {
      const data = await apiClient<{ items: Video[] }>('/feed/recommended?page=1&page_size=20');
      setVideos(data.items || []);
    } catch (e) {
      console.error('Error loading recommended:', e);
    } finally {
      setIsLoading(false);
    }
  };

  const loadCategoryVideos = async (categoryId: string) => {
    setIsLoading(true);
    try {
      const data = await apiClient<{ items: Video[] }>(`/feed/categories/${categoryId}?page=1&page_size=20`);
      setVideos(data.items || []);
    } catch (e) {
      console.error('Error loading category videos:', e);
    } finally {
      setIsLoading(false);
    }
  };

  const tabs = [
    { id: 'trending', label: 'Trending', icon: Flame },
    { id: 'recommended', label: 'For You', icon: Compass },
    { id: 'categories', label: 'Categories', icon: TrendingUp },
  ] as const;

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6 flex items-center gap-2">
        <Compass className="text-blue-500" />
        Discover
      </h1>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => { setActiveTab(tab.id); setSelectedCategory(null); }}
            className={`flex items-center gap-2 px-4 py-2 rounded-full font-medium transition-colors whitespace-nowrap ${
              activeTab === tab.id
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700'
            }`}
          >
            <tab.icon size={18} />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Categories Grid */}
      {activeTab === 'categories' && !selectedCategory && (
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-4">
          {categories.map((cat) => {
            const Icon = categoryIcons[cat.id] || TrendingUp;
            return (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                className="flex flex-col items-center gap-2 p-4 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 hover:border-blue-500 hover:shadow-md transition-all"
              >
                <span className="text-3xl">{cat.icon}</span>
                <span className="text-sm font-medium">{cat.name}</span>
              </button>
            );
          })}
        </div>
      )}

      {/* Category Header */}
      {activeTab === 'categories' && selectedCategory && (
        <div className="mb-4">
          <button
            onClick={() => setSelectedCategory(null)}
            className="text-blue-500 hover:underline mb-2"
          >
            ← Back to Categories
          </button>
          <h2 className="text-xl font-semibold">
            {categories.find(c => c.id === selectedCategory)?.name}
          </h2>
        </div>
      )}

      {/* Video Grid */}
      {(activeTab !== 'categories' || selectedCategory) && (
        <>
          {isLoading ? (
            <div className="text-center py-12">Loading...</div>
          ) : videos.length === 0 ? (
            <div className="text-center py-12 text-gray-500">No videos found</div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {videos.map((video) => (
                <VideoCard key={video.id} video={video} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

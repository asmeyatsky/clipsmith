'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api/client';
import { Search, Filter, Star, Sparkles, Grid, List } from 'lucide-react';

interface AITemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  style: string;
  thumbnail_url: string;
  is_premium: boolean;
  price: number;
  usage_count: number;
  tags: string[];
}

const categories = ['all', 'intro', 'outro', 'social', 'promo', 'vlog', 'music', 'gaming'];
const styles = ['all', 'modern', 'vintage', 'cinematic', 'minimal', 'energetic', 'elegant'];

export function TemplateBrowser() {
  const [templates, setTemplates] = useState<AITemplate[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('all');
  const [style, setStyle] = useState('all');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  useEffect(() => {
    loadTemplates();
  }, [category, style]);

  const loadTemplates = async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams();
      if (category !== 'all') params.append('category', category);
      if (style !== 'all') params.append('style', style);
      
      const data = await apiClient<{ templates: AITemplate[] }>(
        `/api/ai/templates?${params.toString()}`
      );
      setTemplates(data.templates);
    } catch (e) {
      console.error('Error loading templates:', e);
    } finally {
      setIsLoading(false);
    }
  };

  const filteredTemplates = templates.filter(t =>
    t.name.toLowerCase().includes(search.toLowerCase()) ||
    t.description?.toLowerCase().includes(search.toLowerCase()) ||
    t.tags?.some(tag => tag.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="text-blue-500" />
          <h2 className="text-xl font-bold">Template Library</h2>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={() => setViewMode('grid')}
            className={`p-2 rounded ${viewMode === 'grid' ? 'bg-blue-100 dark:bg-blue-900' : 'bg-gray-100 dark:bg-gray-800'}`}
          >
            <Grid size={16} />
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`p-2 rounded ${viewMode === 'list' ? 'bg-blue-100 dark:bg-blue-900' : 'bg-gray-100 dark:bg-gray-800'}`}
          >
            <List size={16} />
          </button>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search templates..."
            className="w-full pl-10 pr-4 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
          />
        </div>
        
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="px-4 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
        >
          {categories.map(cat => (
            <option key={cat} value={cat}>{cat === 'all' ? 'All Categories' : cat.charAt(0).toUpperCase() + cat.slice(1)}</option>
          ))}
        </select>
        
        <select
          value={style}
          onChange={(e) => setStyle(e.target.value)}
          className="px-4 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
        >
          {styles.map(s => (
            <option key={s} value={s}>{s === 'all' ? 'All Styles' : s.charAt(0).toUpperCase() + s.slice(1)}</option>
          ))}
        </select>
      </div>

      {isLoading ? (
        <div className="text-center py-12">Loading templates...</div>
      ) : filteredTemplates.length === 0 ? (
        <div className="text-center py-12 text-gray-500">No templates found</div>
      ) : (
        <div className={viewMode === 'grid' ? 'grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4' : 'space-y-4'}>
          {filteredTemplates.map((template) => (
            <div
              key={template.id}
              className={`border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden hover:border-blue-500 hover:shadow-lg transition-all cursor-pointer ${
                viewMode === 'list' ? 'flex' : ''
              }`}
            >
              {template.thumbnail_url ? (
                <img src={template.thumbnail_url} alt={template.name} className={viewMode === 'grid' ? 'w-full h-32 object-cover' : 'w-32 h-24 object-cover'} />
              ) : (
                <div className={`bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center ${viewMode === 'grid' ? 'w-full h-32' : 'w-32 h-24'}`}>
                  <Sparkles className="text-white/50" size={24} />
                </div>
              )}
              
              <div className="p-3 flex-1">
                <div className="flex items-start justify-between">
                  <h3 className="font-medium text-sm truncate">{template.name}</h3>
                  {template.is_premium && (
                    <Star className="text-yellow-500 fill-yellow-500" size={14} />
                  )}
                </div>
                <p className="text-xs text-gray-500 mt-1 line-clamp-2">{template.description}</p>
                
                <div className="flex items-center justify-between mt-2">
                  <span className="text-xs text-gray-400 capitalize">{template.category}</span>
                  {template.is_premium ? (
                    <span className="text-xs font-medium text-yellow-600">${template.price}</span>
                  ) : (
                    <span className="text-xs text-green-600">Free</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

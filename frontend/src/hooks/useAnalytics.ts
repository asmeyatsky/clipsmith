import { useState, useEffect } from 'react';

// Types for analytics
interface AnalyticsDataPoint {
  timestamp: string;
  value: number;
}

interface TimeSeriesData {
  metric: string;
  time_period: string;
  data_points: AnalyticsDataPoint[];
}

interface TrendingContent {
  video_id: string;
  views: number;
  likes: number;
  engagement_rate: number;
  user_id: string;
}

// API service for analytics
class AnalyticsAPI {
  private baseUrl: string;

  constructor() {
    this.baseUrl = process.env.NODE_ENV === 'production' 
      ? 'https://clipsmith.com' 
      : 'http://localhost:8000';
  }

  private async request(endpoint: string, options: RequestInit = {}) {
    const token = localStorage.getItem('token');
    const response = await fetch(`${this.baseUrl}/api${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        ...options.headers,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch analytics data');
    }

    return response.json();
  }

  async getTimeSeriesData(metric: string, timePeriod: string): Promise<TimeSeriesData> {
    try {
      const response = await this.request(`/analytics/time-series/${metric}?time_period=${timePeriod}`);
      return response.time_series;
    } catch (error) {
      console.error('Failed to fetch time series data:', error);
      return { data_points: [] };
    }
  }

  async getTrendingContent(contentType: string = 'video'): Promise<TrendingContent[]> {
    try {
      const response = await this.request(`/analytics/trending/content?content_type=${contentType}`);
      return response.trending_content || [];
    } catch (error) {
      console.error('Failed to fetch trending content:', error);
      return [];
    }
  }

  async trackEvent(videoId: string, eventType: string, value?: number): Promise<void> {
    try {
      await this.request(`/analytics/videos/${videoId}/track`, {
        method: 'POST',
        body: JSON.stringify({
          event_type: eventType,
          value: value || 1,
        }),
      });
    } catch (error) {
      console.error('Failed to track event:', error);
    }
  }
}

// React hook for analytics
export const useAnalytics = () => {
  const [timeSeriesData, setTimeSeriesData] = useState<Record<string, TimeSeriesData>>({});
  const [trendingContent, setTrendingContent] = useState<TrendingContent[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedMetric, setSelectedMetric] = useState('views');
  const [selectedTimePeriod, setSelectedTimePeriod] = useState('week');
  const [videoViews, setVideoViews] = useState<Record<string, number>>({});

  const analyticsAPI = new AnalyticsAPI();

  useEffect(() => {
    loadAnalyticsData();
  }, []);

  const loadAnalyticsData = async () => {
    try {
      setLoading(true);
      
      // Load time series data
      const [viewsData, likesData] = await Promise.all([
        analyticsAPI.getTimeSeriesData('views', selectedTimePeriod),
        analyticsAPI.getTimeSeriesData('engagement_rate', selectedTimePeriod),
      ]);
      
      setTimeSeriesData({
        views: viewsData,
        engagement_rate: likesData,
      });
      
      // Load trending content
      const trending = await analyticsAPI.getTrendingContent('video');
      setTrendingContent(trending);
    } catch (error) {
      console.error('Failed to load analytics data:', error);
    } finally {
      setLoading(false);
    }
  };

  const changeTimePeriod = async (period: string) => {
    setSelectedTimePeriod(period);
    await loadAnalyticsData();
  };

  const trackVideoView = async (videoId: string) => {
    await analyticsAPI.trackEvent(videoId, 'view');
    };
  
  const trackVideoEngagement = async (videoId: string, engagementType: 'like' | 'comment' | 'share') => {
    await analyticsAPI.trackEvent(videoId, engagementType);
    
    // Update local view count
    setVideoViews(prev => ({
      ...prev,
      [videoId]: (prev[videoId] || 0) + 1,
    }));
  };

  return {
    timeSeriesData,
    trendingContent,
    loading,
    selectedMetric,
    selectedTimePeriod,
    videoViews,
    changeTimePeriod,
    trackVideoView,
    trackVideoEngagement,
    refreshData: loadAnalyticsData,
  };
};
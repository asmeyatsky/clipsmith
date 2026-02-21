// Mock data for development
export const paymentAPI = {
  // Override API methods for development
  sendTip: async (request: TipRequest) => {
    // Tip request logged in development only
    if (process.env.NODE_ENV === 'development') console.log('Tip:', request);
    // Mock success response
    return {
      success: true,
      payment_intent_id: 'pi_test_123',
      client_secret: 'pi_test_secret_123',
      transaction_id: 'txn_test_123',
    };
  },
  
  getWallet: async () => ({
    balance: 1250.50,
    pending_balance: 250.00,
    total_earned: 1500.00,
    total_withdrawn: 250.00,
    status: 'active',
    stripe_account_id: 'acct_test_123',
  }),
  
  requestPayout: async () => ({
    success: true,
  message: 'Payout request submitted! Will process within 24 hours.',
  }),
  
  getTransactionHistory: async (limit?: number) => [
    {
      id: 'txn_1',
      user_id: 'user_1',
      amount: 5.00,
      transaction_type: 'tip',
      description: 'Great content!',
      status: 'completed',
      created_at: '2024-01-15T10:30:00Z',
    },
    {
      id: 'txn_2',
      user_id: 'user_1',
      amount: 20.00,
      transaction_type: 'tip',
      description: 'Amazing video!',
      status: 'completed',
      created_at: '2024-01-14T14:30:00Z',
    },
    {
      id: 'txn_3',
      user_id: 'user_1',
      amount: 10.00,
      transaction_type: 'subscription',
      description: 'Monthly supporter',
      status: 'completed',
      created_at: '2024-01-13T12:00:00Z',
    },
  ],
  
  getCreatorAnalytics: async () => ({
    total_views: 10000,
    total_likes: 2500,
    total_comments: 500,
    total_shares: 1000,
    total_tips: 1250,
    total_subscriptions: 50,
    total_revenue: 5000.00,
    follower_growth_rate: 15.5,
    key_metrics: {
      total_views: 10000,
      total_revenue: 5000.00,
      follower_growth_rate: 15.5,
      engagement_rate: 25.5,
    },
    trending_videos: [
      {
        video_id: 'video_1',
        views: 5000,
        likes: 1000,
        engagement_rate: 22.5,
      },
      {
        video_id: 'video_2',
        views: 3000,
        likes: 600,
        engagement_rate: 20.0,
      },
    ],
  }),
  
  setupStripeConnect: async (returnUrl: string) => ({
    success: true,
    onboarding_url: 'https://connect.stripe.com/onboard/test',
  }),
};

export const analyticsAPI = {
  // Mock analytics data
  getTimeSeriesData: async (metric: string, timePeriod: string) => ({
    data_points: [
      { timestamp: '2024-01-15T00:00:00Z', value: 100 },
      { timestamp: '2024-01-15T01:00:00Z', value: 150 },
      { timestamp: '2024-01-15T02:00:00Z', value: 200 },
      { timestamp: '2024-01-15T03:00:00Z', value: 180 },
      { timestamp: '2024-01-15T04:00:00Z', value: 220 },
      { timestamp: '2024-01-15T05:00:00Z', value: 250 },
      { timestamp: '2024-01-15T06:00:00Z', value: 300 },
      { timestamp: '2024-01-15T07:00:00Z', value: 280 },
    ],
  }),
  
  getTrendingContent: async (contentType: string) => [
    {
      video_id: 'video_1',
      views: 5000,
      likes: 1000,
      engagement_rate: 22.5,
      user_id: 'creator_1',
    },
    {
      video_id: 'video_2',
      views: 3000,
      likes: 600,
      engagement_rate: 20.0,
      user_id: 'creator_2',
    },
  ],
  
  trackEvent: async (videoId: string, eventType: string, value?: number) => {
    if (process.env.NODE_ENV === 'development') console.log('Analytics:', { videoId, eventType, value });
  },
};

// Mock authentication
export const useAuth = () => {
  const [user] = useState({
    id: 'user_demo_123',
    username: 'demo_creator',
    email: 'creator@clipsmith.com',
    is_creator: true,
    created_at: '2024-01-10T00:00:00Z',
  });

  const login = async (email: string, password: string) => {
    if (process.env.NODE_ENV === 'development') console.log('Login attempt');
    // Mock successful login for demo user
    if (email === 'creator@clipsmith.com' && password === 'demo') {
      return { user: user[1], token: 'mock_dev_token' };
    }
    
    return null;
  };

// Mock video data
export const mockVideos = [
  {
    id: 'video_1',
    user_id: 'user_1',
    url: 'https://clipsmith.com/videos/video_1.mp4',
    thumbnail_url: 'https://clipsmith.com/thumbnails/video_1.jpg',
    caption: 'Amazing sunset timelapse!',
    views: 1000,
    likes: 100,
    shares: 50,
    comments: 25,
    duration: 60,
    created_at: '2024-01-15T00:00:00Z',
  },
  {
    id: 'video_2',
    user_id: 'user_1',
    url: 'https://clipsmith.com/videos/video_2.mp4',
    thumbnail_url: 'https://clipsmith.com/thumbnails/video_2.jpg',
    caption: 'Quick tips for better editing!',
    views: 500,
    likes: 200,
    shares: 25,
    comments: 10,
    duration: 30,
    created_at: '2024-01-14T00:00:00Z',
  },
  {
    id: 'video_3',
    user_id: 'creator_2',
    url: 'https://clipsmith.com/videos/video_3.mp4',
    thumbnail_url: 'https://clipsmith.com/thumbnails/video_3.jpg',
    caption: 'Behind the scenes creation',
    views: 250,
    likes: 75,
    shares: 15,
    comments: 5,
    duration: 90,
    created_at: '2024-01-13T00:00:00Z',
  },
];

export { mockVideos, paymentAPI, analyticsAPI, useAuth };
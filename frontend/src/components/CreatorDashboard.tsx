import React, { useState, useEffect } from 'react';
import { usePayment } from '../hooks/usePayment';
import { useAnalytics } from '../hooks/useAnalytics';
import { 
  TrendingUp, 
  DollarSign, 
  Users, 
  Eye, 
  Heart, 
  MessageCircle,
  Calendar,
  BarChart3,
  PieChart,
  Download,
  Settings,
  CreditCard,
  Target,
  Zap
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';

interface DashboardProps {
  className?: string;
}

const CreatorDashboard: React.FC<DashboardProps> = ({ className = '' }) => {
  const { wallet, transactions, analytics, loading, error, refreshData } = usePayment();
  const { views, timeSeriesData, trackEvent } = useAnalytics();
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d'>('30d');
  const [selectedMetric, setSelectedMetric] = useState<'revenue' | 'views' | 'engagement'>('revenue');

  if (loading) {
    return (
      <div className={`p-8 ${className}`}>
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse">
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                Loading creator dashboard...
              </div>
              <div className="w-16 h-1 bg-blue-500 rounded-full animate-pulse"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`p-8 ${className}`}>
        <div className="max-w-7xl mx-auto">
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600 mb-4">
              Error loading dashboard
            </div>
            <div className="text-gray-600 dark:text-gray-300">
              {error}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`p-4 sm:p-6 lg:p-8 ${className}`}>
      <div className="max-w-7xl mx-auto space-y-4 sm:space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white">Creator Dashboard</h1>
            <p className="text-gray-600 dark:text-gray-300 text-sm sm:text-base">Track your performance and earnings</p>
          </div>
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 sm:gap-4">
            <div className="flex items-center justify-center space-x-2 bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
              {(['7d', '30d', '90d'] as const).map((range) => (
                <button
                  key={range}
                  onClick={() => setTimeRange(range)}
                  className={`px-2 sm:px-3 py-1 rounded-md text-xs sm:text-sm font-medium transition-colors ${
                    timeRange === range
                      ? 'bg-blue-500 text-white'
                      : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
                  }`}
                >
                  {range === '7d' ? '7d' : range === '30d' ? '30d' : '90d'}
                </button>
              ))}
            </div>
            <Button variant="outline" size="sm" className="w-full sm:w-auto">
              <Download size={16} className="mr-2" />
              Export
            </Button>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
          <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white">
            <CardContent className="p-4 sm:p-6">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <p className="text-blue-100 text-xs sm:text-sm">Total Revenue</p>
                  <p className="text-xl sm:text-3xl font-bold mt-1">
                    ${analytics?.total_revenue?.toFixed(2) || '0.00'}
                  </p>
                  <div className="flex items-center mt-1 sm:mt-2 text-xs sm:text-sm">
                    <TrendingUp size={12} className="mr-1 sm:size-4" />
                    <span>+12.5%</span>
                  </div>
                </div>
                <DollarSign className="h-6 w-6 sm:h-8 sm:w-8 text-blue-200 ml-2" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white">
            <CardContent className="p-4 sm:p-6">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <p className="text-green-100 text-xs sm:text-sm">Total Views</p>
                  <p className="text-xl sm:text-3xl font-bold mt-1">
                    {analytics?.total_views?.toLocaleString() || '0'}
                  </p>
                  <div className="flex items-center mt-1 sm:mt-2 text-xs sm:text-sm">
                    <TrendingUp size={12} className="mr-1 sm:size-4" />
                    <span>+8.2%</span>
                  </div>
                </div>
                <Eye className="h-6 w-6 sm:h-8 sm:w-8 text-green-200 ml-2" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white">
            <CardContent className="p-4 sm:p-6">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <p className="text-purple-100 text-xs sm:text-sm">Subscribers</p>
                  <p className="text-xl sm:text-3xl font-bold mt-1">
                    {analytics?.total_subscriptions?.toLocaleString() || '0'}
                  </p>
                  <div className="flex items-center mt-1 sm:mt-2 text-xs sm:text-sm">
                    <TrendingUp size={12} className="mr-1 sm:size-4" />
                    <span>+15.3%</span>
                  </div>
                </div>
                <Users className="h-6 w-6 sm:h-8 sm:w-8 text-purple-200 ml-2" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-orange-500 to-orange-600 text-white">
            <CardContent className="p-4 sm:p-6">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <p className="text-orange-100 text-xs sm:text-sm">Engagement Rate</p>
                  <p className="text-xl sm:text-3xl font-bold mt-1">
                    {analytics?.key_metrics?.engagement_rate?.toFixed(1) || '0.0'}%
                  </p>
                  <div className="flex items-center mt-1 sm:mt-2 text-xs sm:text-sm">
                    <TrendingUp size={12} className="mr-1 sm:size-4" />
                    <span>+3.7%</span>
                  </div>
                </div>
                <Heart className="h-6 w-6 sm:h-8 sm:w-8 text-orange-200 ml-2" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 sm:gap-6">
          
          {/* Revenue & Analytics */}
          <div className="xl:col-span-2 space-y-4 sm:space-y-6">
            {/* Performance Chart */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 size={20} />
                    Performance Analytics
                  </CardTitle>
                  <div className="flex flex-wrap gap-1 sm:gap-2">
                    {(['revenue', 'views', 'engagement'] as const).map((metric) => (
                      <Button
                        key={metric}
                        variant={selectedMetric === metric ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setSelectedMetric(metric)}
                        className="text-xs sm:text-sm"
                      >
                        {metric.charAt(0).toUpperCase() + metric.slice(1)}
                      </Button>
                    ))}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="h-64 flex items-center justify-center bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <div className="text-center">
                    <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500 dark:text-gray-400">
                      {selectedMetric} chart visualization
                    </p>
                    <p className="text-sm text-gray-400 dark:text-gray-500 mt-2">
                      Last {timeRange === '7d' ? '7 days' : timeRange === '30d' ? '30 days' : '90 days'}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Wallet & Balance */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CreditCard size={20} />
                  Wallet & Balance
                </CardTitle>
              </CardHeader>
              <CardContent>
                {wallet ? (
                  <div className="space-y-4">
                    <div className="flex justify-between items-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                      <div>
                        <p className="text-sm text-gray-600 dark:text-gray-300">Available Balance</p>
                        <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                          ${wallet.balance.toFixed(2)}
                        </p>
                      </div>
                      <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                        wallet.status === 'active' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {wallet.status}
                      </div>
                    </div>

                    {wallet.pending_balance > 0 && (
                      <div className="flex justify-between items-center p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                        <div>
                          <p className="text-sm text-gray-600 dark:text-gray-300">Pending Balance</p>
                          <p className="font-semibold text-yellow-600 dark:text-yellow-400">
                            ${wallet.pending_balance.toFixed(2)}
                          </p>
                        </div>
                      </div>
                    )}

                    <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
                      <Button 
                        className="flex-1"
                        disabled={wallet.balance < 10}
                        onClick={() => trackEvent('payout_requested', { amount: wallet.balance })}
                        size="sm"
                      >
                        <DollarSign size={14} className="mr-2" />
                        Request Payout
                      </Button>
                      <Button variant="outline" className="flex-1" size="sm">
                        <Settings size={14} className="mr-2" />
                        Configure
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                    No wallet information available
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Revenue Breakdown */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <PieChart size={20} />
                  Revenue Breakdown
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                      <span className="text-sm">Tips</span>
                    </div>
                    <span className="font-semibold">${analytics?.total_tips?.toFixed(2) || '0.00'}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
                      <span className="text-sm">Subscriptions</span>
                    </div>
                    <span className="font-semibold">${((analytics?.total_subscriptions || 0) * 9.99).toFixed(2)}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                      <span className="text-sm">Other Revenue</span>
                    </div>
                    <span className="font-semibold">$0.00</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-4 bg-blue-50 dark:bg-blue-900 rounded-lg">
                  <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                    ${analytics?.total_views.toLocaleString() || '0'}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-300">
                    Total Views
                  </div>
                </div>
                
                <div className="text-center p-4 bg-green-50 dark:bg-green-900 rounded-lg">
                  <div className="text-3xl font-bold text-green-600 dark:text-green-400">
                    ${analytics?.total_likes.toLocaleString() || '0'}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-300">
                    Total Likes
                  </div>
                </div>
                
                <div className="text-center p-4 bg-purple-50 dark:bg-purple-900 rounded-lg">
                  <div className="text-3xl font-bold text-purple-600 dark:text-purple-400">
                    ${analytics?.total_comments.toLocaleString() || '0'}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-300">
                    Total Comments
                  </div>
                </div>
              </div>
              
              <div className="mt-6">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500 dark:text-gray-400">
                    Current Balance
                  </span>
                  <button
                    onClick={refreshData}
                    className="px-3 py-1 text-sm bg-gray-200 dark:bg-gray-700 rounded hover:bg-gray-300 dark:hover:bg-gray-600"
                  >
                    Refresh
                  </button>
                </div>
                
                {wallet && (
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-lg font-semibold">
                        ${wallet.balance > 0 ? '$' : ''}
                        {wallet.balance.toFixed(2)}
                      </span>
                      <span className={`text-sm px-2 py-1 rounded ${
                        wallet.status === 'active' 
                          ? 'bg-green-100 text-green-800' 
                          : wallet.status === 'frozen' 
                          ? 'bg-red-100 text-red-800' 
                          : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {wallet.status}
                      </span>
                    </div>
                    
                    {wallet.pending_balance > 0 && (
                      <div className="text-sm text-yellow-600 dark:text-yellow-400">
                        +${wallet.pending_balance.toFixed(2)} pending
                      </div>
                    )}
                    
                    <div className="flex space-x-4 mt-2">
                      <button
                        onClick={() => {/* Request payout logic */}}
                        className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
                        disabled={wallet.balance < 10}
                      >
                        Request Payout
                      </button>
                      
                      {wallet.stripe_account_id && (
                        <button
                          onClick={async () => {
                            await setupStripeConnect();
                          }}
                          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                        >
                          Configure Payouts
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Revenue Card */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Revenue</h2>
              
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500">Total Revenue</span>
                  <span className="text-lg font-bold text-green-600">
                    ${analytics?.total_revenue > 0 ? '$' : ''}
                    {analytics?.total_revenue.toFixed(2)}
                  </span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500">Total Tips</span>
                  <span className="text-lg font-bold text-blue-600">
                    ${analytics?.total_tips > 0 ? '$' : ''}
                    {analytics?.total_tips.toFixed(2)}
                  </span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500">Subscriptions</span>
                  <span className="text-lg font-bold text-purple-600">
                    {analytics?.total_subscriptions > 0 ? analytics.total_subscriptions : 0}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-4 sm:space-y-6">
            {/* Quick Stats */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap size={20} />
                  Quick Stats
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 dark:text-gray-300">Avg. View Duration</span>
                    <span className="font-semibold">2m 34s</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 dark:text-gray-300">Follower Growth</span>
                    <span className="font-semibold text-green-600">
                      +{analytics?.follower_growth_rate?.toFixed(1) || '0.0'}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 dark:text-gray-300">Total Likes</span>
                    <span className="font-semibold">{analytics?.total_likes?.toLocaleString() || '0'}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 dark:text-gray-300">Total Comments</span>
                    <span className="font-semibold">{analytics?.total_comments?.toLocaleString() || '0'}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Goals Progress */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target size={20} />
                  Monthly Goals
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm">Revenue Goal</span>
                      <span className="text-sm font-medium">$750 / $1000</span>
                    </div>
                    <Progress value={75} className="h-2" />
                  </div>
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm">Views Goal</span>
                      <span className="text-sm font-medium">45K / 50K</span>
                    </div>
                    <Progress value={90} className="h-2" />
                  </div>
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm">Subscribers Goal</span>
                      <span className="text-sm font-medium">18 / 25</span>
                    </div>
                    <Progress value={72} className="h-2" />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Top Performing Content */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp size={20} />
                  Top Content
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {[
                    { title: "How to Edit Like a Pro", views: "12.3K", revenue: "$234" },
                    { title: "Best Camera Settings 2024", views: "8.7K", revenue: "$156" },
                    { title: "Color Grading Tutorial", views: "6.2K", revenue: "$98" }
                  ].map((content, index) => (
                    <div key={index} className="flex items-center justify-between p-2 hover:bg-gray-50 dark:hover:bg-gray-800 rounded-lg transition-colors">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{content.title}</p>
                        <div className="flex items-center gap-2 text-xs text-gray-500">
                          <Eye size={12} />
                          {content.views}
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-semibold text-green-600">{content.revenue}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Recent Transactions */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Calendar size={20} />
                Recent Transactions
              </CardTitle>
              <Button variant="outline" size="sm">
                View All
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {transactions.length === 0 ? (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                <DollarSign className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                <p>No transactions yet</p>
                <p className="text-sm text-gray-400 mt-2">Start earning to see your transactions here</p>
              </div>
            ) : (
              <div className="space-y-2">
                {transactions.slice(0, 10).map((transaction) => (
                  <div key={transaction.id} className="flex items-center justify-between p-4 hover:bg-gray-50 dark:hover:bg-gray-800 rounded-lg transition-colors">
                    <div className="flex items-center space-x-3">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        transaction.amount > 0 
                          ? 'bg-green-100 dark:bg-green-900/20' 
                          : 'bg-red-100 dark:bg-red-900/20'
                      }`}>
                        {transaction.amount > 0 ? (
                          <DollarSign className="h-5 w-5 text-green-600 dark:text-green-400" />
                        ) : (
                          <CreditCard className="h-5 w-5 text-red-600 dark:text-red-400" />
                        )}
                      </div>
                      <div>
                        <div className="font-medium text-gray-900 dark:text-white">
                          {transaction.description}
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          {new Date(transaction.created_at).toLocaleDateString()} • {transaction.transaction_type}
                        </div>
                      </div>
                    </div>
                    
                    <div className="text-right">
                      <div className={`font-bold ${
                        transaction.amount > 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                      }`}>
                        {transaction.amount > 0 ? '+' : ''}
                        ${Math.abs(transaction.amount).toFixed(2)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
      </div>
    </div>
  );
};

export default CreatorDashboard;
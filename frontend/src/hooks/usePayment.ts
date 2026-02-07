// Payment API integration for clipsmith frontend
import { useState, useEffect } from 'react';

// Types for payment system
interface TipRequest {
  creator_id: string;
  amount: number;
  video_id?: string;
  message?: string;
}

interface Wallet {
  balance: number;
  pending_balance: number;
  total_earned: number;
  total_withdrawn: number;
  status: 'active' | 'frozen' | 'suspended';
  stripe_account_id?: string;
}

interface Transaction {
  id: string;
  user_id: string;
  amount: number;
  transaction_type: 'tip' | 'subscription' | 'payout' | 'refund';
  status: 'pending' | 'completed' | 'failed';
  description: string;
  created_at: string;
  updated_at?: string;
  completed_at?: string;
}

interface CreatorAnalytics {
  total_views: number;
  total_likes: number;
  total_comments: number;
  total_shares: number;
  total_tips: number;
  total_subscriptions: number;
  total_revenue: number;
  follower_growth_rate: number;
  key_metrics: {
    total_views: number;
    total_revenue: number;
    follower_growth: number;
    engagement_rate: number;
  };
  trending_videos: Array<any>;
}

// API service
class PaymentAPI {
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
      const error = await response.json();
      throw new Error(error.detail || 'Request failed');
    }

    return response.json();
  }

  // Tip functionality
  async sendTip(request: TipRequest): Promise<any> {
    try {
      const response = await this.request('/payments/tip', {
        method: 'POST',
        body: JSON.stringify({
          creator_id: request.creator_id,
          amount: request.amount,
          video_id: request.video_id,
          message: request.message || 'Great content!',
        }),
      });

      if (response.success) {
        // Show success message
        this.showNotification('Tip sent successfully!', 'success');
        
        // Update local wallet if needed
        this.updateLocalWallet();
      }

      return response;
    } catch (error) {
      this.showNotification('Failed to send tip: ' + error.message, 'error');
      throw error;
    }
  }

  // Wallet management
  async getWallet(): Promise<Wallet> {
    try {
      const response = await this.request('/payments/wallet');
      return response.wallet;
    } catch (error) {
      console.error('Failed to get wallet:', error);
      throw error;
    }
  }

  async getTransactionHistory(limit: number = 20): Promise<Transaction[]> {
    try {
      const response = await this.request(`/payments/transactions?limit=${limit}`);
      return response.transactions || [];
    } catch (error) {
      console.error('Failed to get transaction history:', error);
      return [];
    }
  }

  async requestPayout(): Promise<any> {
    try {
      const response = await this.request('/payments/payouts/request');
      
      if (response.success) {
        this.showNotification('Payout request submitted!', 'success');
      }

      return response;
    } catch (error) {
      this.showNotification('Failed to request payout: ' + error.message, 'error');
      throw error;
    }
  }

  // Creator analytics
  async getCreatorAnalytics(): Promise<CreatorAnalytics> {
    try {
      const response = await this.request('/analytics/creator/dashboard');
      return response.analytics;
    } catch (error) {
      console.error('Failed to get analytics:', error);
      return this.getDefaultAnalytics();
    }
  }

  // Stripe Connect setup
  async setupStripeConnect(returnUrl: string): Promise<any> {
    try {
      const response = await this.request('/payments/wallet/setup-connect', {
        method: 'POST',
        body: JSON.stringify({
          return_url,
          refresh_url: `${window.location.origin}/settings/payouts`,
        }),
      });

      if (response.success && response.onboarding_url) {
        // Open Stripe Connect in new window
        window.open(response.onboarding_url, '_blank');
      }

      return response;
    } catch (error) {
      this.showNotification('Failed to setup Stripe Connect: ' + error.message, 'error');
      throw error;
    }
  }

  // Helper methods
  private showNotification(message: string, type: 'success' | 'error' | 'info') {
    // Create a simple notification (could be enhanced with toast library)
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 p-4 rounded-lg text-white text-sm font-medium z-50 ${
      type === 'success' ? 'bg-green-500' : 
      type === 'error' ? 'bg-red-500' : 
      'bg-blue-500'
    } shadow-lg`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
      notification.remove();
    }, 3000);
  }

  private updateLocalWallet() {
    // Simple wallet update for UI consistency
    const event = new CustomEvent('walletUpdated');
    window.dispatchEvent(event);
  }

  private getDefaultAnalytics(): CreatorAnalytics {
    return {
      total_views: 0,
      total_likes: 0,
      total_comments: 0,
      total_shares: 0,
      total_tips: 0,
      total_subscriptions: 0,
      total_revenue: 0,
      follower_growth_rate: 0,
      key_metrics: {
        total_views: 0,
        total_revenue: 0,
        follower_growth: 0,
        engagement_rate: 0,
      },
      trending_videos: [],
    };
  }
}

// React Hook for payment functionality
export const usePayment = () => {
  const [wallet, setWallet] = useState<Wallet | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [analytics, setAnalytics] = useState<CreatorAnalytics | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const paymentAPI = new PaymentAPI();

  // Load initial data
  useEffect(() => {
    loadPaymentData();
  }, []);

  const loadPaymentData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [walletData, analyticsData] = await Promise.all([
        paymentAPI.getWallet(),
        paymentAPI.getCreatorAnalytics(),
      ]);
      
      setWallet(walletData);
      setAnalytics(analyticsData);
      setTransactions(await paymentAPI.getTransactionHistory());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load payment data');
    } finally {
      setLoading(false);
    }
  };

  const sendTip = async (creatorId: string, amount: number, videoId?: string, message?: string) => {
    try {
      await paymentAPI.sendTip({
        creator_id: creatorId,
        amount,
        video_id: videoId,
        message,
      });
      
      // Reload data after tip
      await loadPaymentData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send tip');
    }
  };

  const requestPayout = async () => {
    try {
      await paymentAPI.requestPayout();
      await loadPaymentData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to request payout');
    }
  };

  const setupStripeConnect = async () => {
    try {
      await paymentAPI.setupStripeConnect(
        `${window.location.origin}/settings/payouts/complete`
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to setup Stripe Connect');
    }
  };

  return {
    wallet,
    transactions,
    analytics,
    loading,
    error,
    sendTip,
    requestPayout,
    setupStripeConnect,
    refreshData: loadPaymentData,
  };
};
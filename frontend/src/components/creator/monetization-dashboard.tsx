'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api/client';
import { DollarSign, TrendingUp, Users, CreditCard, Wallet, ArrowUpRight, ArrowDownRight } from 'lucide-react';

interface WalletData {
  balance: number;
  pending_balance: number;
  total_earned: number;
  total_withdrawn: number;
  stripe_account_id?: string;
}

interface Transaction {
  id: string;
  amount: number;
  transaction_type: string;
  description: string;
  status: string;
  created_at: string;
}

interface Subscription {
  id: string;
  subscriber_id: string;
  amount: number;
  status: string;
  created_at: string;
}

interface Analytics {
  total_tips: number;
  total_subscriptions: number;
  total_revenue: number;
  new_subscribers: number;
}

export function CreatorMonetizationDashboard() {
  const [wallet, setWallet] = useState<WalletData | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [payoutAmount, setPayoutAmount] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [walletData, transData, subData, analyticsData] = await Promise.all([
        apiClient<{ wallet: WalletData }>('/api/payments/wallet'),
        apiClient<{ transactions: Transaction[] }>('/api/payments/transactions?limit=10'),
        apiClient<{ subscriptions: Subscription[] }>('/api/payments/subscriptions'),
        apiClient<{ analytics: Analytics }>('/api/analytics/creator/dashboard'),
      ]);
      
      setWallet(walletData.wallet);
      setTransactions(transData.transactions || []);
      setSubscriptions(subscriptions.subscriptions || []);
      setAnalytics(analyticsData.analytics);
    } catch (e) {
      console.error('Error loading monetization data:', e);
    } finally {
      setIsLoading(false);
    }
  };

  const requestPayout = async () => {
    try {
      await apiClient('/api/payments/payouts/request', { method: 'POST' });
      alert('Payout requested successfully!');
      loadData();
    } catch (e) {
      alert('Failed to request payout');
    }
  };

  const setupStripe = async () => {
    try {
      const result = await apiClient<{ success: boolean; onboarding_url: string }>('/api/payments/wallet/setup-connect', {
        method: 'POST',
        body: JSON.stringify({
          return_url: window.location.origin + '/settings',
          refresh_url: window.location.origin + '/settings'
        })
      });
      if (result.onboarding_url) {
        window.open(result.onboarding_url, '_blank');
      }
    } catch (e) {
      alert('Failed to setup Stripe');
    }
  };

  if (isLoading) {
    return <div className="text-center py-12">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <DollarSign className="text-green-500" />
          Monetization Dashboard
        </h2>
      </div>

      {!wallet?.stripe_account_id && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-medium">Setup Payouts</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">Connect your bank account to receive payments</p>
            </div>
            <button
              onClick={setupStripe}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Connect Stripe
            </button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2 text-gray-500 mb-1">
            <Wallet size={16} />
            <span className="text-sm">Available Balance</span>
          </div>
          <p className="text-2xl font-bold text-green-600">${wallet?.balance?.toFixed(2) || '0.00'}</p>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2 text-gray-500 mb-1">
            <TrendingUp size={16} />
            <span className="text-sm">Total Earned</span>
          </div>
          <p className="text-2xl font-bold">${wallet?.total_earned?.toFixed(2) || '0.00'}</p>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2 text-gray-500 mb-1">
            <Users size={16} />
            <span className="text-sm">Active Subscribers</span>
          </div>
          <p className="text-2xl font-bold">{subscriptions.filter(s => s.status === 'active').length}</p>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2 text-gray-500 mb-1">
            <CreditCard size={16} />
            <span className="text-sm">Pending</span>
          </div>
          <p className="text-2xl font-bold text-yellow-600">${wallet?.pending_balance?.toFixed(2) || '0.00'}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <h3 className="font-semibold mb-4">Request Payout</h3>
          <div className="flex gap-2">
            <input
              type="number"
              value={payoutAmount}
              onChange={(e) => setPayoutAmount(e.target.value)}
              placeholder="Amount"
              className="flex-1 px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
            />
            <button
              onClick={requestPayout}
              disabled={!wallet?.stripe_account_id || !payoutAmount}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
            >
              Withdraw
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-2">Minimum payout: $10</p>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <h3 className="font-semibold mb-4">Quick Stats</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-500">Total Tips</span>
              <span className="font-medium">${analytics?.total_tips?.toFixed(2) || '0.00'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Subscription Revenue</span>
              <span className="font-medium">${analytics?.total_subscriptions?.toFixed(2) || '0.00'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">New Subscribers</span>
              <span className="font-medium">{analytics?.new_subscribers || 0}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
        <h3 className="font-semibold p-4 border-b border-gray-200 dark:border-gray-700">Recent Transactions</h3>
        <div className="divide-y divide-gray-200 dark:divide-gray-700">
          {transactions.length === 0 ? (
            <p className="p-4 text-gray-500 text-center">No transactions yet</p>
          ) : (
            transactions.map((trans) => (
              <div key={trans.id} className="p-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-full ${trans.amount > 0 ? 'bg-green-100 dark:bg-green-900' : 'bg-red-100 dark:bg-red-900'}`}>
                    {trans.amount > 0 ? <ArrowUpRight className="text-green-600" size={16} /> : <ArrowDownRight className="text-red-600" size={16} />}
                  </div>
                  <div>
                    <p className="font-medium capitalize">{trans.transaction_type?.replace('_', ' ')}</p>
                    <p className="text-sm text-gray-500">{trans.description}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className={`font-bold ${trans.amount > 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {trans.amount > 0 ? '+' : ''}{trans.amount?.toFixed(2)}
                  </p>
                  <p className="text-xs text-gray-500">{new Date(trans.created_at).toLocaleDateString()}</p>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

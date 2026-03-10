"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import DashboardLayout from "@/components/dashboard-layout";
import { useAuth } from "@/lib/auth-context";
import {
  creditsApi,
  CreditBalance,
  CreditTransaction,
  UsageStats,
} from "@/lib/api";

function formatCurrency(amount: string | number): string {
  const num = typeof amount === "string" ? parseFloat(amount) : amount;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(num);
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatDuration(seconds: number | null): string {
  if (!seconds) return "-";
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}m ${remainingSeconds}s`;
}

function TransactionTypeIcon({ type }: { type: CreditTransaction["transaction_type"] }) {
  const icons: Record<CreditTransaction["transaction_type"], { icon: string; color: string }> = {
    purchase: { icon: "↑", color: "text-green-600 bg-green-100" },
    call_usage: { icon: "↓", color: "text-red-600 bg-red-100" },
    refund: { icon: "↩", color: "text-blue-600 bg-blue-100" },
    adjustment: { icon: "⚙", color: "text-gray-600 bg-gray-100" },
    bonus: { icon: "★", color: "text-yellow-600 bg-yellow-100" },
  };

  const { icon, color } = icons[type];

  return (
    <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full ${color} font-bold`}>
      {icon}
    </span>
  );
}

function TransactionTypeBadge({ type }: { type: CreditTransaction["transaction_type"] }) {
  const labels: Record<CreditTransaction["transaction_type"], { label: string; color: string }> = {
    purchase: { label: "Purchase", color: "bg-green-100 text-green-800" },
    call_usage: { label: "Call Usage", color: "bg-red-100 text-red-800" },
    refund: { label: "Refund", color: "bg-blue-100 text-blue-800" },
    adjustment: { label: "Adjustment", color: "bg-gray-100 text-gray-800" },
    bonus: { label: "Bonus", color: "bg-yellow-100 text-yellow-800" },
  };

  const { label, color } = labels[type];

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${color}`}>
      {label}
    </span>
  );
}

export default function CreditsPage() {
  const { token, loading: authLoading } = useAuth();
  const [balance, setBalance] = useState<CreditBalance | null>(null);
  const [usageStats, setUsageStats] = useState<UsageStats | null>(null);
  const [transactions, setTransactions] = useState<CreditTransaction[]>([]);
  const [totalTransactions, setTotalTransactions] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>("");
  const [offset, setOffset] = useState(0);
  const limit = 20;

  useEffect(() => {
    if (authLoading) return;
    if (token) {
      loadData();
    } else {
      setLoading(false);
    }
  }, [token, authLoading, filter, offset]);

  async function loadData() {
    if (!token) return;

    try {
      setLoading(true);
      const [balanceData, statsData, historyData] = await Promise.all([
        creditsApi.getBalance(token),
        creditsApi.getUsageStats(token),
        creditsApi.getHistory(token, {
          transaction_type: filter || undefined,
          limit,
          offset,
        }),
      ]);

      setBalance(balanceData);
      setUsageStats(statsData);
      setTransactions(historyData.results);
      setTotalTransactions(historyData.total);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  }

  const totalPages = Math.ceil(totalTransactions / limit);
  const currentPage = Math.floor(offset / limit) + 1;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Credits</h1>
            <p className="text-gray-500">Manage your credits and view transaction history</p>
          </div>
          <Link
            href="/dashboard/credits/add"
            className="inline-flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors"
          >
            Add Credits
          </Link>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {/* Stats Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-xl shadow-sm p-5">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center text-2xl">
                💰
              </div>
              <div>
                <p className="text-sm text-gray-500">Current Balance</p>
                <p className="text-2xl font-bold text-gray-900">
                  {balance ? formatCurrency(balance.balance) : "-"}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-5">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center text-2xl">
                📈
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Purchased</p>
                <p className="text-2xl font-bold text-green-600">
                  {balance ? formatCurrency(balance.total_purchased) : "-"}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-5">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center text-2xl">
                📉
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Used</p>
                <p className="text-2xl font-bold text-red-600">
                  {balance ? formatCurrency(balance.total_used) : "-"}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-5">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center text-2xl">
                📞
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Calls</p>
                <p className="text-2xl font-bold text-gray-900">
                  {usageStats?.total_calls ?? "-"}
                  <span className="text-sm font-normal text-gray-500 ml-1">
                    ({usageStats?.total_minutes ?? 0} min)
                  </span>
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Transaction History */}
        <div className="bg-white rounded-xl shadow-sm">
          <div className="px-6 py-4 border-b flex flex-wrap items-center justify-between gap-4">
            <h3 className="text-lg font-medium text-gray-900">Transaction History</h3>
            <select
              value={filter}
              onChange={(e) => {
                setFilter(e.target.value);
                setOffset(0);
              }}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">All Transactions</option>
              <option value="purchase">Purchases</option>
              <option value="call_usage">Call Usage</option>
              <option value="refund">Refunds</option>
              <option value="adjustment">Adjustments</option>
              <option value="bonus">Bonuses</option>
            </select>
          </div>

          {loading ? (
            <div className="p-8 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
            </div>
          ) : transactions.length === 0 ? (
            <div className="px-6 py-12 text-center">
              <p className="text-gray-500">No transactions found</p>
            </div>
          ) : (
            <>
              <ul className="divide-y divide-gray-200">
                {transactions.map((transaction) => (
                  <li key={transaction.id} className="px-6 py-4 hover:bg-gray-50">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center min-w-0">
                        <TransactionTypeIcon type={transaction.transaction_type} />
                        <div className="ml-4 min-w-0">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {transaction.description}
                          </p>
                          <div className="flex items-center gap-2 mt-1">
                            <TransactionTypeBadge type={transaction.transaction_type} />
                            {transaction.phone_number && (
                              <span className="text-xs text-gray-500">
                                {transaction.phone_number}
                              </span>
                            )}
                            {transaction.call_duration_seconds && (
                              <span className="text-xs text-gray-500">
                                • {formatDuration(transaction.call_duration_seconds)}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="ml-4 flex-shrink-0 text-right">
                        <p
                          className={`text-sm font-semibold ${
                            parseFloat(transaction.amount) >= 0
                              ? "text-green-600"
                              : "text-red-600"
                          }`}
                        >
                          {parseFloat(transaction.amount) >= 0 ? "+" : ""}
                          {formatCurrency(transaction.amount)}
                        </p>
                        <p className="text-xs text-gray-500">
                          {formatDate(transaction.created_at)}
                        </p>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>

              {totalPages > 1 && (
                <div className="px-6 py-3 flex items-center justify-between border-t">
                  <p className="text-sm text-gray-700">
                    Showing {offset + 1} to {Math.min(offset + limit, totalTransactions)} of{" "}
                    {totalTransactions} results
                  </p>
                  <nav className="inline-flex rounded-md shadow-sm -space-x-px">
                    <button
                      onClick={() => setOffset(Math.max(0, offset - limit))}
                      disabled={offset === 0}
                      className="px-3 py-2 rounded-l-md border border-gray-300 bg-white text-sm text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                    >
                      ←
                    </button>
                    <span className="px-4 py-2 border-t border-b border-gray-300 bg-white text-sm text-gray-700">
                      {currentPage} / {totalPages}
                    </span>
                    <button
                      onClick={() => setOffset(offset + limit)}
                      disabled={currentPage >= totalPages}
                      className="px-3 py-2 rounded-r-md border border-gray-300 bg-white text-sm text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                    >
                      →
                    </button>
                  </nav>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}

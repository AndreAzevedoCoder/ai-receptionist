"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import DashboardLayout from "@/components/dashboard-layout";
import { useAuth } from "@/lib/auth-context";
import { creditsApi, CreditBalance } from "@/lib/api";

const PRESET_AMOUNTS = [
  { value: 10, label: "$10", minutes: "~42 min" },
  { value: 25, label: "$25", minutes: "~104 min" },
  { value: 50, label: "$50", minutes: "~208 min" },
  { value: 100, label: "$100", minutes: "~417 min" },
];

const COST_PER_MINUTE = 0.24;

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(amount);
}

export default function AddCreditsPage() {
  const { token, loading: authLoading } = useAuth();
  const [selectedAmount, setSelectedAmount] = useState<number>(25);
  const [customAmount, setCustomAmount] = useState<string>("");
  const [isCustom, setIsCustom] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [balance, setBalance] = useState<CreditBalance | null>(null);

  useEffect(() => {
    if (authLoading) return;
    if (token) {
      loadBalance();
    }
  }, [token, authLoading]);

  async function loadBalance() {
    if (!token) return;

    try {
      const data = await creditsApi.getBalance(token);
      setBalance(data);
    } catch (err) {
      console.error("Failed to load balance:", err);
    }
  }

  const amount = isCustom ? parseFloat(customAmount) || 0 : selectedAmount;
  const estimatedMinutes = Math.floor(amount / COST_PER_MINUTE);

  async function handlePurchase() {
    if (amount < 5) {
      setError("Minimum purchase amount is $5.00");
      return;
    }

    if (!token) {
      setError("Please log in to purchase credits");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await creditsApi.createCheckoutSession(token, {
        amount,
        success_url: `${window.location.origin}/dashboard/credits?success=true`,
        cancel_url: `${window.location.origin}/dashboard/credits/add?canceled=true`,
      });

      window.location.href = result.checkout_url;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create checkout session");
      setLoading(false);
    }
  }

  return (
    <DashboardLayout>
      <div className="max-w-2xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <Link
            href="/dashboard/credits"
            className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700 mb-4"
          >
            ← Back to Credits
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">Add Credits</h1>
          <p className="text-gray-500">Purchase credits to use for AI receptionist calls</p>
        </div>

        {/* Current Balance */}
        {balance && (
          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Current Balance</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(parseFloat(balance.balance))}
                </p>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-500">Rate</p>
                <p className="text-lg font-semibold text-gray-900">${COST_PER_MINUTE}/min</p>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {/* Amount Selection */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Select Amount</h2>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
            {PRESET_AMOUNTS.map((preset) => (
              <button
                key={preset.value}
                onClick={() => {
                  setSelectedAmount(preset.value);
                  setIsCustom(false);
                }}
                className={`relative flex flex-col items-center justify-center p-4 border-2 rounded-xl transition-colors ${
                  !isCustom && selectedAmount === preset.value
                    ? "border-indigo-600 bg-indigo-50"
                    : "border-gray-200 hover:border-gray-300"
                }`}
              >
                <span className="text-2xl font-bold text-gray-900">{preset.label}</span>
                <span className="text-sm text-gray-500 mt-1">{preset.minutes}</span>
                {!isCustom && selectedAmount === preset.value && (
                  <div className="absolute top-2 right-2">
                    <span className="flex h-5 w-5 items-center justify-center rounded-full bg-indigo-600 text-white text-xs">
                      ✓
                    </span>
                  </div>
                )}
              </button>
            ))}
          </div>

          <div className="mt-4">
            <div className="flex items-center mb-2">
              <input
                type="checkbox"
                id="custom-amount"
                checked={isCustom}
                onChange={(e) => setIsCustom(e.target.checked)}
                className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
              />
              <label htmlFor="custom-amount" className="ml-2 text-sm font-medium text-gray-700">
                Custom amount
              </label>
            </div>

            {isCustom && (
              <div className="mt-2">
                <div className="relative rounded-lg shadow-sm">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <span className="text-gray-500">$</span>
                  </div>
                  <input
                    type="number"
                    min="5"
                    step="0.01"
                    value={customAmount}
                    onChange={(e) => setCustomAmount(e.target.value)}
                    placeholder="0.00"
                    className="block w-full pl-7 pr-12 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                  <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                    <span className="text-gray-500">USD</span>
                  </div>
                </div>
                <p className="mt-1 text-xs text-gray-500">Minimum purchase: $5.00</p>
              </div>
            )}
          </div>
        </div>

        {/* Summary */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Summary</h2>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-500">Credit amount</span>
              <span className="font-medium">{formatCurrency(amount)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Estimated call time</span>
              <span className="font-medium">~{estimatedMinutes} minutes</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Rate</span>
              <span className="font-medium">${COST_PER_MINUTE}/minute</span>
            </div>
            <hr />
            <div className="flex justify-between text-lg">
              <span className="font-medium">Total</span>
              <span className="font-bold">{formatCurrency(amount)}</span>
            </div>
          </div>
        </div>

        {/* Purchase Button */}
        <button
          onClick={handlePurchase}
          disabled={loading || amount < 5}
          className="w-full flex items-center justify-center px-6 py-4 bg-indigo-600 text-white rounded-xl font-semibold text-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <>
              <svg
                className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              Processing...
            </>
          ) : (
            <>Purchase {formatCurrency(amount)} in Credits</>
          )}
        </button>

        <p className="text-center text-sm text-gray-500">
          Secure payment powered by Stripe. Credits are added instantly.
        </p>
      </div>
    </DashboardLayout>
  );
}

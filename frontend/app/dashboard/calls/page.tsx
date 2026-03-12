"use client";

import { useEffect, useState } from "react";
import DashboardLayout from "@/components/dashboard-layout";
import { useAuth } from "@/lib/auth-context";
import { callsApi, CallLog } from "@/lib/api";

export default function CallsPage() {
  const { token, loading: authLoading } = useAuth();
  const [calls, setCalls] = useState<CallLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalCalls, setTotalCalls] = useState(0);
  const [offset, setOffset] = useState(0);
  const limit = 20;

  useEffect(() => {
    if (authLoading) return;
    if (token) {
      loadCalls();
    } else {
      setLoading(false);
    }
  }, [token, authLoading, offset]);

  async function loadCalls() {
    if (!token) return;

    try {
      setLoading(true);
      const data = await callsApi.getAll(token, { limit, offset });
      setCalls(data.results);
      setTotalCalls(data.count);
    } catch (error) {
      console.error("Failed to load calls:", error);
    } finally {
      setLoading(false);
    }
  }

  function formatDate(dateString: string) {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  function formatDuration(seconds: number) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  }

  function getStatusBadge(status: CallLog["status"]) {
    const styles: Record<CallLog["status"], string> = {
      incoming: "bg-blue-100 text-blue-800",
      forwarded: "bg-yellow-100 text-yellow-800",
      vapi: "bg-purple-100 text-purple-800",
      completed: "bg-green-100 text-green-800",
      failed: "bg-red-100 text-red-800",
      no_answer: "bg-gray-100 text-gray-800",
      busy: "bg-orange-100 text-orange-800",
    };

    const labels: Record<CallLog["status"], string> = {
      incoming: "Incoming",
      forwarded: "Forwarded",
      vapi: "AI Handled",
      completed: "Completed",
      failed: "Failed",
      no_answer: "No Answer",
      busy: "Busy",
    };

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[status]}`}>
        {labels[status]}
      </span>
    );
  }

  const totalPages = Math.ceil(totalCalls / limit);
  const currentPage = Math.floor(offset / limit) + 1;

  // Calculate stats
  const totalMinutes = calls.reduce((acc, call) => acc + call.duration, 0) / 60;
  const completedCalls = calls.filter((c) => c.status === "completed").length;
  const aiHandledCalls = calls.filter((c) => c.status === "vapi" || c.status === "completed").length;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Call History</h1>
          <p className="text-gray-500">View all calls handled by your AI receptionist</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <div className="bg-white rounded-xl shadow-sm p-4">
            <p className="text-sm text-gray-500">Total Calls</p>
            <p className="text-2xl font-bold text-gray-900">{totalCalls}</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-4">
            <p className="text-sm text-gray-500">AI Handled</p>
            <p className="text-2xl font-bold text-purple-600">{aiHandledCalls}</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-4">
            <p className="text-sm text-gray-500">Completed</p>
            <p className="text-2xl font-bold text-green-600">{completedCalls}</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-4">
            <p className="text-sm text-gray-500">Total Minutes</p>
            <p className="text-2xl font-bold text-gray-900">{Math.round(totalMinutes)}</p>
          </div>
        </div>

        {/* Calls Table */}
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          {loading ? (
            <div className="p-8 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
            </div>
          ) : calls.length === 0 ? (
            <div className="p-12 text-center">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-1">No calls yet</h3>
              <p className="text-gray-500">
                Calls will appear here once your AI receptionist starts handling them
              </p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Caller
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Duration
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Credits
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Lead
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Date
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {calls.map((call) => (
                      <tr key={call.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <div
                              className={`w-10 h-10 rounded-full flex items-center justify-center ${
                                call.status === "completed"
                                  ? "bg-green-100"
                                  : call.status === "failed"
                                  ? "bg-red-100"
                                  : "bg-gray-100"
                              }`}
                            >
                              <svg
                                className={`w-5 h-5 ${
                                  call.status === "completed"
                                    ? "text-green-600"
                                    : call.status === "failed"
                                    ? "text-red-600"
                                    : "text-gray-600"
                                }`}
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
                                />
                              </svg>
                            </div>
                            <div className="ml-4">
                              <div className="text-sm font-medium text-gray-900">
                                {call.from_number}
                              </div>
                              <div className="text-sm text-gray-500">→ {call.to_number}</div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {getStatusBadge(call.status)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatDuration(call.duration)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {parseFloat(call.credits_spent) > 0 ? (
                            <span className="text-amber-600 font-medium">
                              {parseFloat(call.credits_spent).toFixed(2)}
                            </span>
                          ) : (
                            "-"
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {call.lead ? (
                            <span className="text-indigo-600 font-medium">
                              {call.lead.name || "Unknown"}
                            </span>
                          ) : (
                            "-"
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDate(call.created_at)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <a
                            href={`tel:${call.from_number}`}
                            className="text-green-600 hover:text-green-900"
                          >
                            Call Back
                          </a>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
                  <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                    <p className="text-sm text-gray-700">
                      Showing <span className="font-medium">{offset + 1}</span> to{" "}
                      <span className="font-medium">{Math.min(offset + limit, totalCalls)}</span> of{" "}
                      <span className="font-medium">{totalCalls}</span> results
                    </p>
                    <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                      <button
                        onClick={() => setOffset(Math.max(0, offset - limit))}
                        disabled={offset === 0}
                        className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                      >
                        ←
                      </button>
                      <span className="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700">
                        Page {currentPage} of {totalPages}
                      </span>
                      <button
                        onClick={() => setOffset(offset + limit)}
                        disabled={currentPage >= totalPages}
                        className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                      >
                        →
                      </button>
                    </nav>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}

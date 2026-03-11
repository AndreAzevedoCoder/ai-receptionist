"use client";

import { useEffect, useState } from "react";
import DashboardLayout from "@/components/dashboard-layout";
import { useAuth } from "@/lib/auth-context";
import { leadsApi, leadAnswersApi, agentsApi, Lead, LeadAnswer, Question } from "@/lib/api";

export default function LeadsPage() {
  const { token, loading: authLoading } = useAuth();
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [sourceFilter, setSourceFilter] = useState("");
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [loadingLead, setLoadingLead] = useState(false);
  const [totalLeads, setTotalLeads] = useState(0);
  const [offset, setOffset] = useState(0);
  const limit = 20;

  // Editing state
  const [agentQuestions, setAgentQuestions] = useState<Question[]>([]);
  const [editingAnswer, setEditingAnswer] = useState<LeadAnswer | null>(null);
  const [newAnswer, setNewAnswer] = useState<{ question_type: string; question_label: string; answer: string } | null>(null);
  const [savingAnswer, setSavingAnswer] = useState(false);

  useEffect(() => {
    if (authLoading) return;
    if (token) {
      loadLeads();
      loadAgentQuestions();
    } else {
      setLoading(false);
    }
  }, [token, authLoading, search, sourceFilter, offset]);

  async function loadAgentQuestions() {
    if (!token) return;
    try {
      const questions = await agentsApi.getQuestions(token);
      setAgentQuestions(questions);
    } catch (error) {
      console.error("Failed to load agent questions:", error);
    }
  }

  async function loadLeads() {
    if (!token) return;

    try {
      setLoading(true);
      const data = await leadsApi.getAll(token, {
        search: search || undefined,
        source: sourceFilter || undefined,
        limit,
        offset,
      });
      setLeads(data.results || []);
      setTotalLeads(data.count || 0);
    } catch (error) {
      console.error("Failed to load leads:", error);
      setLeads([]);
      setTotalLeads(0);
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

  function getSourceBadge(source: Lead["source"]) {
    const styles: Record<Lead["source"], string> = {
      telnyx_ai: "bg-amber-100 text-amber-800",
      vapi_ai: "bg-purple-100 text-purple-800",
      manual: "bg-blue-100 text-blue-800",
      web: "bg-green-100 text-green-800",
    };

    const labels: Record<Lead["source"], string> = {
      telnyx_ai: "AI Call",
      vapi_ai: "Vapi AI",
      manual: "Manual",
      web: "Website",
    };

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[source] || 'bg-gray-100 text-gray-800'}`}>
        {labels[source] || source}
      </span>
    );
  }

  function getAnswerIcon(questionType: LeadAnswer["question_type"]) {
    const icons: Record<string, string> = {
      budget: "💰",
      credit_score: "📊",
      location: "📍",
      move_in_date: "📅",
      num_people: "👥",
      name: "👤",
      email: "✉️",
      phone: "📞",
      custom: "💬",
    };
    return icons[questionType] || "💬";
  }

  async function viewLead(lead: Lead) {
    if (!token) return;
    setLoadingLead(true);
    setEditingAnswer(null);
    setNewAnswer(null);
    try {
      // Fetch full lead details with answers
      const fullLead = await leadsApi.getById(token, lead.id);
      setSelectedLead(fullLead);
    } catch (error) {
      console.error("Failed to load lead details:", error);
      // Fallback to list data
      setSelectedLead(lead);
    } finally {
      setLoadingLead(false);
    }
  }

  async function saveEditedAnswer() {
    if (!token || !editingAnswer) return;
    setSavingAnswer(true);
    try {
      await leadAnswersApi.update(token, editingAnswer.id, {
        answer: editingAnswer.answer,
      });
      // Refresh the lead
      if (selectedLead) {
        const fullLead = await leadsApi.getById(token, selectedLead.id);
        setSelectedLead(fullLead);
      }
      setEditingAnswer(null);
    } catch (error) {
      console.error("Failed to save answer:", error);
    } finally {
      setSavingAnswer(false);
    }
  }

  async function saveNewAnswer() {
    if (!token || !selectedLead || !newAnswer || !newAnswer.answer) return;
    setSavingAnswer(true);
    try {
      await leadsApi.createAnswer(token, selectedLead.id, {
        question_type: newAnswer.question_type,
        question_label: newAnswer.question_label,
        answer: newAnswer.answer,
      });
      // Refresh the lead
      const fullLead = await leadsApi.getById(token, selectedLead.id);
      setSelectedLead(fullLead);
      setNewAnswer(null);
    } catch (error) {
      console.error("Failed to create answer:", error);
    } finally {
      setSavingAnswer(false);
    }
  }

  async function deleteAnswer(answerId: string) {
    if (!token || !confirm("Are you sure you want to delete this answer?")) return;
    try {
      await leadAnswersApi.delete(token, answerId);
      // Refresh the lead
      if (selectedLead) {
        const fullLead = await leadsApi.getById(token, selectedLead.id);
        setSelectedLead(fullLead);
      }
    } catch (error) {
      console.error("Failed to delete answer:", error);
    }
  }

  function getQuestionLabel(questionType: string): string {
    const labels: Record<string, string> = {
      budget: "Budget",
      credit_score: "Credit Score",
      location: "Location",
      move_in_date: "Move-in Date",
      num_people: "Number of People",
      name: "Name",
      email: "Email",
      phone: "Phone",
      custom: "Custom",
    };
    return labels[questionType] || questionType;
  }

  function getAvailableQuestionTypes(): { type: string; label: string }[] {
    // Get question types from agent questions
    const types = agentQuestions.map((q) => ({
      type: q.question_type,
      label: q.question_type === "custom" ? q.custom_text || "Custom" : getQuestionLabel(q.question_type),
    }));

    // If no questions configured, show default types
    if (types.length === 0) {
      return [
        { type: "budget", label: "Budget" },
        { type: "credit_score", label: "Credit Score" },
        { type: "location", label: "Location" },
        { type: "move_in_date", label: "Move-in Date" },
        { type: "num_people", label: "Number of People" },
        { type: "custom", label: "Custom" },
      ];
    }

    return types;
  }

  const totalPages = Math.ceil(totalLeads / limit);
  const currentPage = Math.floor(offset / limit) + 1;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Leads</h1>
            <p className="text-gray-500">Manage your leads captured by the AI receptionist</p>
          </div>
          <button className="inline-flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors">
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add Lead
          </button>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-xl shadow-sm p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <svg
                  className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
                <input
                  type="text"
                  placeholder="Search by name, phone, or email..."
                  value={search}
                  onChange={(e) => {
                    setSearch(e.target.value);
                    setOffset(0);
                  }}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>
            <select
              value={sourceFilter}
              onChange={(e) => {
                setSourceFilter(e.target.value);
                setOffset(0);
              }}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">All Sources</option>
              <option value="telnyx_ai">AI Calls</option>
              <option value="manual">Manual</option>
              <option value="web">Website</option>
            </select>
          </div>
        </div>

        {/* Leads Table */}
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          {loading ? (
            <div className="p-8 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
            </div>
          ) : leads.length === 0 ? (
            <div className="p-12 text-center">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-1">No leads yet</h3>
              <p className="text-gray-500">
                Leads will appear here after your AI receptionist handles calls
              </p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Lead
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Contact
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Source
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
                    {leads.map((lead) => (
                      <tr key={lead.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <div className="w-10 h-10 bg-indigo-100 rounded-full flex items-center justify-center">
                              <span className="text-sm font-medium text-indigo-600">
                                {lead.name?.charAt(0).toUpperCase() || "?"}
                              </span>
                            </div>
                            <div className="ml-4">
                              <div className="text-sm font-medium text-gray-900">
                                {lead.name || "Unknown"}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">{lead.phone_number}</div>
                          <div className="text-sm text-gray-500">{lead.email || "-"}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {getSourceBadge(lead.source)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDate(lead.created_at)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <button
                            onClick={() => viewLead(lead)}
                            disabled={loadingLead}
                            className="text-indigo-600 hover:text-indigo-900 mr-4 disabled:opacity-50"
                          >
                            {loadingLead ? "..." : "View"}
                          </button>
                          <a
                            href={`tel:${lead.phone_number}`}
                            className="text-green-600 hover:text-green-900"
                          >
                            Call
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
                      <span className="font-medium">{Math.min(offset + limit, totalLeads)}</span> of{" "}
                      <span className="font-medium">{totalLeads}</span> results
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

        {/* Lead Detail Modal */}
        {selectedLead && (
          <div className="fixed inset-0 z-50 overflow-y-auto">
            <div className="flex items-center justify-center min-h-screen px-4">
              <div
                className="fixed inset-0 bg-gray-500 bg-opacity-75"
                onClick={() => setSelectedLead(null)}
              />
              <div className="relative bg-white rounded-xl shadow-xl max-w-lg w-full p-6">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-lg font-semibold text-gray-900">Lead Details</h3>
                  <button
                    onClick={() => setSelectedLead(null)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                <div className="space-y-4">
                  <div className="flex items-center gap-4">
                    <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center">
                      <span className="text-2xl font-medium text-indigo-600">
                        {selectedLead.name?.charAt(0).toUpperCase() || "?"}
                      </span>
                    </div>
                    <div>
                      <h4 className="text-xl font-semibold text-gray-900">
                        {selectedLead.name || "Unknown"}
                      </h4>
                      {getSourceBadge(selectedLead.source)}
                    </div>
                  </div>

                  <div className="border-t pt-4 space-y-3">
                    <div className="flex items-center gap-3">
                      <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                      </svg>
                      <span className="text-gray-900">{selectedLead.phone_number}</span>
                    </div>
                    {selectedLead.email && (
                      <div className="flex items-center gap-3">
                        <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                        </svg>
                        <span className="text-gray-900">{selectedLead.email}</span>
                      </div>
                    )}
                    <div className="flex items-center gap-3">
                      <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                      <span className="text-gray-900">{formatDate(selectedLead.created_at)}</span>
                    </div>
                  </div>

                  {/* Collected Answers */}
                  <div className="border-t pt-4">
                    <div className="flex items-center justify-between mb-3">
                      <h5 className="text-sm font-medium text-gray-500">Collected Information</h5>
                      <button
                        onClick={() => setNewAnswer({ question_type: getAvailableQuestionTypes()[0]?.type || "custom", question_label: "", answer: "" })}
                        className="text-xs text-indigo-600 hover:text-indigo-800 font-medium"
                      >
                        + Add Answer
                      </button>
                    </div>

                    {/* Add New Answer Form */}
                    {newAnswer && (
                      <div className="mb-3 p-3 bg-indigo-50 rounded-lg border border-indigo-200">
                        <div className="space-y-3">
                          <div>
                            <label className="block text-xs font-medium text-gray-700 mb-1">Question Type</label>
                            <select
                              value={newAnswer.question_type}
                              onChange={(e) => {
                                const selectedType = e.target.value;
                                const question = agentQuestions.find(q => q.question_type === selectedType);
                                setNewAnswer({
                                  ...newAnswer,
                                  question_type: selectedType,
                                  question_label: question?.question_type === "custom" ? question.custom_text || "" : "",
                                });
                              }}
                              className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            >
                              {getAvailableQuestionTypes().map((q) => (
                                <option key={q.type} value={q.type}>
                                  {q.label}
                                </option>
                              ))}
                            </select>
                          </div>
                          {newAnswer.question_type === "custom" && (
                            <div>
                              <label className="block text-xs font-medium text-gray-700 mb-1">Custom Label</label>
                              <input
                                type="text"
                                value={newAnswer.question_label}
                                onChange={(e) => setNewAnswer({ ...newAnswer, question_label: e.target.value })}
                                placeholder="Enter custom label..."
                                className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                              />
                            </div>
                          )}
                          <div>
                            <label className="block text-xs font-medium text-gray-700 mb-1">Answer</label>
                            <input
                              type="text"
                              value={newAnswer.answer}
                              onChange={(e) => setNewAnswer({ ...newAnswer, answer: e.target.value })}
                              placeholder="Enter answer..."
                              className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            />
                          </div>
                          <div className="flex gap-2">
                            <button
                              onClick={saveNewAnswer}
                              disabled={savingAnswer || !newAnswer.answer}
                              className="px-3 py-1.5 text-xs bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
                            >
                              {savingAnswer ? "Saving..." : "Save"}
                            </button>
                            <button
                              onClick={() => setNewAnswer(null)}
                              className="px-3 py-1.5 text-xs bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      </div>
                    )}

                    <div className="space-y-2">
                      {selectedLead.answers && selectedLead.answers.length > 0 ? (
                        selectedLead.answers.map((answer) => (
                          <div
                            key={answer.id}
                            className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg group"
                          >
                            <span className="text-lg">{getAnswerIcon(answer.question_type)}</span>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                                  {answer.display_label}
                                </p>
                                {answer.source === "manual" && (
                                  <span className="text-xs bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded">Manual</span>
                                )}
                              </div>
                              {editingAnswer?.id === answer.id ? (
                                <div className="mt-1 flex gap-2">
                                  <input
                                    type="text"
                                    value={editingAnswer.answer}
                                    onChange={(e) => setEditingAnswer({ ...editingAnswer, answer: e.target.value })}
                                    className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                  />
                                  <button
                                    onClick={saveEditedAnswer}
                                    disabled={savingAnswer}
                                    className="px-2 py-1 text-xs bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50"
                                  >
                                    {savingAnswer ? "..." : "Save"}
                                  </button>
                                  <button
                                    onClick={() => setEditingAnswer(null)}
                                    className="px-2 py-1 text-xs bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
                                  >
                                    Cancel
                                  </button>
                                </div>
                              ) : (
                                <p className="text-sm text-gray-900 mt-0.5">{answer.answer}</p>
                              )}
                            </div>
                            {editingAnswer?.id !== answer.id && (
                              <div className="opacity-0 group-hover:opacity-100 flex gap-1 transition-opacity">
                                <button
                                  onClick={() => setEditingAnswer(answer)}
                                  className="p-1 text-gray-400 hover:text-indigo-600"
                                  title="Edit"
                                >
                                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                                  </svg>
                                </button>
                                <button
                                  onClick={() => deleteAnswer(answer.id)}
                                  className="p-1 text-gray-400 hover:text-red-600"
                                  title="Delete"
                                >
                                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                  </svg>
                                </button>
                              </div>
                            )}
                          </div>
                        ))
                      ) : (
                        <p className="text-sm text-gray-500 italic">No information collected yet</p>
                      )}
                    </div>
                  </div>

                  {selectedLead.notes && (
                    <div className="border-t pt-4">
                      <h5 className="text-sm font-medium text-gray-500 mb-2">Notes</h5>
                      <p className="text-gray-700 whitespace-pre-wrap">{selectedLead.notes}</p>
                    </div>
                  )}

                  <div className="border-t pt-4 flex gap-3">
                    <a
                      href={`tel:${selectedLead.phone_number}`}
                      className="flex-1 inline-flex items-center justify-center px-4 py-2 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700"
                    >
                      <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                      </svg>
                      Call
                    </a>
                    {selectedLead.email && (
                      <a
                        href={`mailto:${selectedLead.email}`}
                        className="flex-1 inline-flex items-center justify-center px-4 py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700"
                      >
                        <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                        </svg>
                        Email
                      </a>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}

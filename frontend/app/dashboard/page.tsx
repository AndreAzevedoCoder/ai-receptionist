"use client";

import { useEffect, useState, useCallback } from "react";
import DashboardLayout from "@/components/dashboard-layout";
import { useAuth } from "@/lib/auth-context";
import { agentsApi, Agent, Question } from "@/lib/api";

const QUESTION_OPTIONS = [
  { id: "budget", label: "Budget", icon: "💰" },
  { id: "credit_score", label: "Credit score", icon: "📊" },
  { id: "location", label: "Location", icon: "📍" },
  { id: "move_in_date", label: "Move-in date", icon: "📅" },
  { id: "num_people", label: "Number of people", icon: "👥" },
] as const;

type QuestionType = typeof QUESTION_OPTIONS[number]['id'];

function FlowArrow({ label, color = "gray" }: { label?: string; color?: "gray" | "green" }) {
  const lineColor = color === "green" ? "bg-emerald-300" : "bg-gray-300";
  const textColor = color === "green" ? "text-emerald-600" : "text-gray-500";
  const arrowColor = color === "green" ? "text-emerald-300" : "text-gray-300";

  return (
    <div className="flex flex-col items-center py-1">
      <div className={`w-0.5 h-5 ${lineColor}`} />
      {label && (
        <span className={`text-xs font-medium ${textColor} my-1`}>{label}</span>
      )}
      <div className={`w-0.5 h-5 ${lineColor}`} />
      <svg className={`w-3 h-3 ${arrowColor}`} fill="currentColor" viewBox="0 0 12 12">
        <path d="M6 9L1 4h10L6 9z" />
      </svg>
    </div>
  );
}

function FlowCard({
  icon,
  title,
  subtitle,
  variant = "default",
}: {
  icon: string;
  title: string;
  subtitle?: string;
  variant?: "default" | "primary" | "success";
}) {
  const variants = {
    default: "bg-white border-gray-200 hover:border-gray-300",
    primary: "bg-indigo-50 border-indigo-200 hover:border-indigo-300",
    success: "bg-emerald-50 border-emerald-200 hover:border-emerald-300",
  };

  return (
    <div className={`flex items-center gap-3 px-5 py-4 rounded-2xl border-2 shadow-sm transition-all ${variants[variant]}`}>
      <div className="w-10 h-10 bg-white/50 rounded-full flex items-center justify-center">
        <span className="text-xl">{icon}</span>
      </div>
      <div>
        <p className="font-semibold text-gray-900">{title}</p>
        {subtitle && <p className="text-sm text-gray-600">{subtitle}</p>}
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const { user, token, loading: authLoading } = useAuth();
  const [agent, setAgent] = useState<Agent | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showSetup, setShowSetup] = useState(true);
  const [selectedQuestions, setSelectedQuestions] = useState<string[]>([]);
  const [customQuestions, setCustomQuestions] = useState<string[]>([]);
  const [customInput, setCustomInput] = useState("");
  const [showCustomInput, setShowCustomInput] = useState(false);

  // Track original state to detect changes
  const [originalSelected, setOriginalSelected] = useState<string[]>([]);
  const [originalCustom, setOriginalCustom] = useState<string[]>([]);

  // Check if there are unsaved changes
  const hasChanges =
    JSON.stringify([...selectedQuestions].sort()) !== JSON.stringify([...originalSelected].sort()) ||
    JSON.stringify(customQuestions) !== JSON.stringify(originalCustom);

  useEffect(() => {
    if (authLoading) return;
    if (token) {
      loadAgent();
    } else {
      setLoading(false);
    }
  }, [token, authLoading]);

  async function loadAgent() {
    if (!token) return;
    try {
      const agentData = await agentsApi.getMe(token);
      setAgent(agentData);

      // Parse questions from agent.questions
      const selected: string[] = [];
      const custom: string[] = [];

      if (agentData.questions && agentData.questions.length > 0) {
        for (const q of agentData.questions) {
          if (q.question_type === 'custom') {
            custom.push(q.custom_text || '');
          } else {
            selected.push(q.question_type);
          }
        }
      }

      // Set defaults if no questions
      const finalSelected = selected.length > 0 ? selected : ["budget", "credit_score", "location", "move_in_date"];
      setSelectedQuestions(finalSelected);
      setCustomQuestions(custom);

      // Store original state
      setOriginalSelected(finalSelected);
      setOriginalCustom(custom);
    } catch (error: any) {
      // 404 means no agent yet, set defaults
      if (error.status === 404) {
        const defaults = ["budget", "credit_score", "location", "move_in_date"];
        setSelectedQuestions(defaults);
        setOriginalSelected(defaults);
      } else {
        console.error("Failed to load agent:", error);
      }
    } finally {
      setLoading(false);
    }
  }

  // Save questions to backend
  async function saveQuestions() {
    if (!token || !agent) return;

    setSaving(true);
    try {
      // Build questions array for API
      const questions: Question[] = [
        ...selectedQuestions.map((type, i) => ({
          question_type: type as Question['question_type'],
          order: i,
        })),
        ...customQuestions.map((text, i) => ({
          question_type: 'custom' as const,
          custom_text: text,
          order: selectedQuestions.length + i,
        })),
      ];

      await agentsApi.updateQuestions(token, questions);

      // Refresh agent data to get updated questions
      const updatedAgent = await agentsApi.getMe(token);
      setAgent(updatedAgent);

      // Update original state to match current
      setOriginalSelected([...selectedQuestions]);
      setOriginalCustom([...customQuestions]);
    } catch (error) {
      console.error("Failed to save questions:", error);
    } finally {
      setSaving(false);
    }
  }

  function toggleQuestion(id: string) {
    setSelectedQuestions(prev =>
      prev.includes(id) ? prev.filter((q) => q !== id) : [...prev, id]
    );
  }

  function addCustomQuestion() {
    if (customInput.trim()) {
      setCustomQuestions(prev => [...prev, customInput.trim()]);
      setCustomInput("");
      setShowCustomInput(false);
    }
  }

  function removeCustomQuestion(index: number) {
    setCustomQuestions(prev => prev.filter((_, i) => i !== index));
  }

  // Show loading while auth or agent is loading
  if (loading || authLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
        </div>
      </DashboardLayout>
    );
  }

  // If no token after loading, user is not logged in
  if (!token) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <p className="text-gray-600 mb-4">Please log in to access the dashboard.</p>
            <a href="/login" className="text-indigo-600 hover:underline">Go to Login</a>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto">
        {/* How to Setup Header */}
        {showSetup && (
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5 mb-8">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center">
                  <div className="w-3 h-3 bg-gray-400 rounded-full"></div>
                </div>
                <div>
                  <h2 className="font-semibold text-gray-900">How to Setup</h2>
                  <p className="text-sm text-gray-500">Watch this quick tutorial to get started</p>
                </div>
              </div>
              <button
                onClick={() => setShowSetup(false)}
                className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"
              >
                Hide
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
            </div>
          </div>
        )}

        {/* Flow Diagram */}
        <div className="bg-gradient-to-br from-slate-50 via-gray-50 to-slate-100 rounded-3xl p-8 mb-6">
          <div className="flex flex-col items-center">
            {/* Step 1: Alven's Number */}
            <FlowCard
              icon="📞"
              title="Alven's Number"
              subtitle={agent?.phone_number || "Pending..."}
              variant="primary"
            />

            <FlowArrow label="Transfers to" />

            {/* Step 2: Your Number */}
            <FlowCard
              icon="📱"
              title="Your Number"
              subtitle={agent?.forward_phone_number || "Not configured"}
              variant="default"
            />

            <FlowArrow label="Can't pick up" />

            {/* Step 3: Alven AI - Special styled card */}
            <div className="bg-gradient-to-r from-amber-100 to-orange-100 border-2 border-amber-300 rounded-2xl px-6 py-5 shadow-md">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-gradient-to-br from-amber-200 to-orange-300 rounded-full flex items-center justify-center shadow-inner">
                  <span className="text-2xl">🤖</span>
                </div>
                <div>
                  <p className="font-bold text-gray-900 text-lg">Alven</p>
                  <p className="text-sm text-amber-700">AI Receptionist</p>
                </div>
              </div>
            </div>

            <FlowArrow label="Sends details" color="green" />

            {/* Step 4: Your Email */}
            <FlowCard
              icon="✉️"
              title="Your Email"
              subtitle={user?.email || "your@email.com"}
              variant="success"
            />
          </div>

          {/* Buy Credits Button */}
          <div className="flex justify-center mt-8">
            <a
              href="/dashboard/credits/add"
              className="inline-flex items-center gap-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-full transition-all shadow-lg hover:shadow-xl hover:-translate-y-0.5"
            >
              To start buy credits
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </a>
          </div>
        </div>

        {/* Questions Section */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 text-center">
            What should Alven ask callers?
          </h3>

          <div className="flex flex-wrap justify-center gap-2">
            {QUESTION_OPTIONS.map((option) => (
              <button
                key={option.id}
                onClick={() => toggleQuestion(option.id)}
                className={`flex items-center gap-1.5 px-4 py-2 rounded-full text-sm font-medium transition-all ${
                  selectedQuestions.includes(option.id)
                    ? "bg-gray-900 text-white"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                <span>{option.icon}</span>
                <span>{option.label}</span>
              </button>
            ))}
          </div>

          {/* Custom Questions */}
          <div className="flex flex-wrap justify-center gap-2 mt-3">
            {customQuestions.map((q, i) => (
              <span
                key={i}
                className="flex items-center gap-2 px-4 py-2 bg-gray-100 rounded-full text-sm text-gray-700"
              >
                {q}
                <button
                  onClick={() => removeCustomQuestion(i)}
                  className="text-gray-400 hover:text-gray-600 text-lg leading-none"
                >
                  ×
                </button>
              </span>
            ))}

            {showCustomInput ? (
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={customInput}
                  onChange={(e) => setCustomInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && addCustomQuestion()}
                  placeholder="Enter question..."
                  className="px-4 py-2 rounded-full text-sm border border-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 w-48"
                  autoFocus
                />
                <button
                  onClick={addCustomQuestion}
                  className="px-3 py-2 bg-indigo-600 text-white rounded-full text-sm hover:bg-indigo-700"
                >
                  Add
                </button>
                <button
                  onClick={() => {
                    setShowCustomInput(false);
                    setCustomInput("");
                  }}
                  className="text-gray-400 hover:text-gray-600 text-xl leading-none"
                >
                  ×
                </button>
              </div>
            ) : (
              <button
                onClick={() => setShowCustomInput(true)}
                className="flex items-center gap-1.5 px-4 py-2 rounded-full text-sm text-gray-500 border border-dashed border-gray-300 hover:border-gray-400 hover:text-gray-600 transition-colors"
              >
                Custom question
                <span className="text-lg leading-none">+</span>
              </button>
            )}
          </div>
        </div>

        {/* Quick Stats */}
        {agent && (
          <div className="grid grid-cols-3 gap-4 mt-6">
            <div className="bg-white rounded-xl p-4 border border-gray-100">
              <p className="text-sm text-gray-500">Status</p>
              <p className={`text-lg font-semibold capitalize ${agent.status === 'active' ? 'text-green-600' : 'text-yellow-600'}`}>
                {agent.status}
              </p>
            </div>
            <div className="bg-white rounded-xl p-4 border border-gray-100">
              <p className="text-sm text-gray-500">Alven&apos;s Number</p>
              <p className="text-lg font-semibold text-gray-900">{agent.phone_number || "Pending"}</p>
            </div>
            <div className="bg-white rounded-xl p-4 border border-gray-100">
              <p className="text-sm text-gray-500">Your Number</p>
              <p className="text-lg font-semibold text-gray-900">{agent.forward_phone_number || "Not set"}</p>
            </div>
          </div>
        )}
      </div>

      {/* Floating Save Button */}
      {hasChanges && (
        <div className="fixed bottom-6 right-6 z-50">
          <button
            onClick={saveQuestions}
            disabled={saving}
            className="flex items-center gap-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-medium rounded-full shadow-lg hover:shadow-xl transition-all transform hover:-translate-y-0.5"
          >
            {saving ? (
              <>
                <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Saving...
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Save Changes
              </>
            )}
          </button>
        </div>
      )}
    </DashboardLayout>
  );
}

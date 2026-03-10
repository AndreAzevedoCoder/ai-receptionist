"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

const QUESTION_OPTIONS = [
  { id: "budget", label: "Budget", icon: "💰" },
  { id: "credit_score", label: "Credit Score", icon: "📊" },
  { id: "location", label: "Location", icon: "📍" },
  { id: "move_in_date", label: "Move-in Date", icon: "📅" },
  { id: "num_people", label: "Number of People", icon: "👥" },
];

function formatPhoneNumber(value: string): string {
  const numbers = value.replace(/\D/g, "");
  if (numbers.length <= 3) return numbers;
  if (numbers.length <= 6) return `(${numbers.slice(0, 3)}) ${numbers.slice(3)}`;
  return `(${numbers.slice(0, 3)}) ${numbers.slice(3, 6)}-${numbers.slice(6, 10)}`;
}

function unformatPhoneNumber(value: string): string {
  return value.replace(/\D/g, "");
}

export default function RegisterPage() {
  const [step, setStep] = useState(0);
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    confirmPassword: "",
    phoneNumber: "",
    selectedQuestions: [] as string[],
    customQuestions: [] as string[],
    notificationEmail: "",
    useOriginalEmail: true,
  });
  const [customQuestionInput, setCustomQuestionInput] = useState("");
  const [showCustomInput, setShowCustomInput] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const { register } = useAuth();

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const { name, value } = e.target;
    if (name === "phoneNumber") {
      setFormData({ ...formData, [name]: formatPhoneNumber(value) });
    } else {
      setFormData({ ...formData, [name]: value });
    }
  }

  function toggleQuestion(questionId: string) {
    setFormData((prev) => ({
      ...prev,
      selectedQuestions: prev.selectedQuestions.includes(questionId)
        ? prev.selectedQuestions.filter((q) => q !== questionId)
        : [...prev.selectedQuestions, questionId],
    }));
  }

  function addCustomQuestion() {
    if (customQuestionInput.trim()) {
      setFormData((prev) => ({
        ...prev,
        customQuestions: [...prev.customQuestions, customQuestionInput.trim()],
      }));
      setCustomQuestionInput("");
      setShowCustomInput(false);
    }
  }

  function removeCustomQuestion(index: number) {
    setFormData((prev) => ({
      ...prev,
      customQuestions: prev.customQuestions.filter((_, i) => i !== index),
    }));
  }

  function canProceed(): boolean {
    switch (step) {
      case 0:
        return (
          formData.email.includes("@") &&
          formData.password.length >= 8 &&
          formData.password === formData.confirmPassword
        );
      case 1:
        return unformatPhoneNumber(formData.phoneNumber).length >= 10;
      case 2:
        const hasQuestions = formData.selectedQuestions.length > 0 || formData.customQuestions.length > 0;
        const hasEmail = formData.useOriginalEmail || formData.notificationEmail.includes("@");
        return hasQuestions && hasEmail;
      default:
        return false;
    }
  }

  function nextStep() {
    setError("");
    if (step === 0) {
      if (formData.password !== formData.confirmPassword) {
        setError("Passwords do not match");
        return;
      }
      if (formData.password.length < 8) {
        setError("Password must be at least 8 characters");
        return;
      }
    }
    setStep(step + 1);
  }

  function prevStep() {
    setError("");
    setStep(step - 1);
  }

  async function handleSubmit() {
    setError("");
    setLoading(true);

    try {
      // Build the system prompt from selected questions
      const questions = [
        ...formData.selectedQuestions.map((q) => {
          const option = QUESTION_OPTIONS.find((o) => o.id === q);
          return option?.label || q;
        }),
        ...formData.customQuestions,
      ];

      const notificationEmail = formData.useOriginalEmail
        ? formData.email
        : formData.notificationEmail;

      await register({
        email: formData.email,
        password: formData.password,
        phoneNumber: unformatPhoneNumber(formData.phoneNumber),
        questions,
        notificationEmail,
      });
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <Link href="/" className="flex items-center justify-center gap-2">
          <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold">A</span>
          </div>
          <span className="text-xl font-bold text-gray-900">Alven</span>
        </Link>

        {/* Progress indicator */}
        <div className="mt-8 flex items-center justify-center gap-2">
          {[0, 1, 2].map((s) => (
            <div
              key={s}
              className={`h-2 rounded-full transition-all ${
                s === step
                  ? "w-8 bg-indigo-600"
                  : s < step
                  ? "w-8 bg-indigo-300"
                  : "w-8 bg-gray-200"
              }`}
            />
          ))}
        </div>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow-lg sm:rounded-xl sm:px-10">
          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          {/* Step 0: Email & Password */}
          {step === 0 && (
            <div className="space-y-5">
              <div className="text-center mb-6">
                <h2 className="text-2xl font-bold text-gray-900">Create your account</h2>
                <p className="mt-2 text-sm text-gray-600">
                  Already have an account?{" "}
                  <Link href="/login" className="font-medium text-indigo-600 hover:text-indigo-500">
                    Sign in
                  </Link>
                </p>
              </div>

              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                  Email address
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={formData.email}
                  onChange={handleChange}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                  Password
                </label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="new-password"
                  required
                  value={formData.password}
                  onChange={handleChange}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                />
                <p className="mt-1 text-xs text-gray-500">At least 8 characters</p>
              </div>

              <div>
                <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
                  Confirm Password
                </label>
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type="password"
                  autoComplete="new-password"
                  required
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>

              <button
                onClick={nextStep}
                disabled={!canProceed()}
                className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Continue
              </button>
            </div>
          )}

          {/* Step 1: Phone Number */}
          {step === 1 && (
            <div className="space-y-5">
              <div className="text-center mb-6">
                <h2 className="text-2xl font-bold text-gray-900">Your business number</h2>
                <p className="mt-2 text-sm text-gray-600">
                  What&apos;s the number that clients call you on?
                </p>
              </div>

              <div>
                <label htmlFor="phoneNumber" className="block text-sm font-medium text-gray-700">
                  Phone Number
                </label>
                <input
                  id="phoneNumber"
                  name="phoneNumber"
                  type="tel"
                  autoComplete="tel"
                  required
                  value={formData.phoneNumber}
                  onChange={handleChange}
                  placeholder="(555) 123-4567"
                  className="mt-1 block w-full px-3 py-3 text-lg border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                />
                <p className="mt-2 text-xs text-gray-500">
                  Alven will answer calls and forward them to this number when needed
                </p>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  onClick={prevStep}
                  className="flex-1 py-3 px-4 border border-gray-300 rounded-lg shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  Back
                </button>
                <button
                  onClick={nextStep}
                  disabled={!canProceed()}
                  className="flex-1 py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Continue
                </button>
              </div>
            </div>
          )}

          {/* Step 2: Questions & Delivery */}
          {step === 2 && (
            <div className="space-y-6">
              <div className="text-center mb-4">
                <h2 className="text-2xl font-bold text-gray-900">Customize Alven</h2>
                <p className="mt-2 text-sm text-gray-600">
                  What information do you want Alven to ask callers?
                </p>
              </div>

              {/* Question Buttons */}
              <div className="grid grid-cols-2 gap-2">
                {QUESTION_OPTIONS.map((option) => (
                  <button
                    key={option.id}
                    onClick={() => toggleQuestion(option.id)}
                    className={`flex items-center gap-2 px-4 py-3 rounded-lg border-2 transition-colors text-left ${
                      formData.selectedQuestions.includes(option.id)
                        ? "border-indigo-600 bg-indigo-50 text-indigo-700"
                        : "border-gray-200 hover:border-gray-300 text-gray-700"
                    }`}
                  >
                    <span className="text-lg">{option.icon}</span>
                    <span className="text-sm font-medium">{option.label}</span>
                  </button>
                ))}

                {/* Custom Question Button */}
                <button
                  onClick={() => setShowCustomInput(true)}
                  className="flex items-center gap-2 px-4 py-3 rounded-lg border-2 border-dashed border-gray-300 hover:border-indigo-400 text-gray-600 hover:text-indigo-600 transition-colors text-left"
                >
                  <span className="text-lg">✏️</span>
                  <span className="text-sm font-medium">Custom Question</span>
                </button>
              </div>

              {/* Custom Question Input */}
              {showCustomInput && (
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={customQuestionInput}
                    onChange={(e) => setCustomQuestionInput(e.target.value)}
                    placeholder="Enter your custom question..."
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                    onKeyDown={(e) => e.key === "Enter" && addCustomQuestion()}
                  />
                  <button
                    onClick={addCustomQuestion}
                    disabled={!customQuestionInput.trim()}
                    className="px-4 py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50"
                  >
                    Add
                  </button>
                  <button
                    onClick={() => {
                      setShowCustomInput(false);
                      setCustomQuestionInput("");
                    }}
                    className="px-3 py-2 text-gray-500 hover:text-gray-700"
                  >
                    Cancel
                  </button>
                </div>
              )}

              {/* Custom Questions List */}
              {formData.customQuestions.length > 0 && (
                <div className="space-y-2">
                  {formData.customQuestions.map((q, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between px-3 py-2 bg-indigo-50 rounded-lg border border-indigo-200"
                    >
                      <span className="text-sm text-indigo-700">{q}</span>
                      <button
                        onClick={() => removeCustomQuestion(i)}
                        className="text-indigo-400 hover:text-indigo-600"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Delivery Section */}
              <div className="border-t pt-6">
                <h3 className="text-sm font-medium text-gray-900 mb-3">
                  Where should we send the information we collected?
                </h3>

                <div className="space-y-3">
                  <button
                    onClick={() => setFormData({ ...formData, useOriginalEmail: true })}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg border-2 transition-colors text-left ${
                      formData.useOriginalEmail
                        ? "border-indigo-600 bg-indigo-50"
                        : "border-gray-200 hover:border-gray-300"
                    }`}
                  >
                    <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                      formData.useOriginalEmail ? "border-indigo-600" : "border-gray-300"
                    }`}>
                      {formData.useOriginalEmail && (
                        <div className="w-2.5 h-2.5 rounded-full bg-indigo-600" />
                      )}
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-900">Email to {formData.email}</span>
                    </div>
                  </button>

                  <button
                    onClick={() => setFormData({ ...formData, useOriginalEmail: false })}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg border-2 transition-colors text-left ${
                      !formData.useOriginalEmail
                        ? "border-indigo-600 bg-indigo-50"
                        : "border-gray-200 hover:border-gray-300"
                    }`}
                  >
                    <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                      !formData.useOriginalEmail ? "border-indigo-600" : "border-gray-300"
                    }`}>
                      {!formData.useOriginalEmail && (
                        <div className="w-2.5 h-2.5 rounded-full bg-indigo-600" />
                      )}
                    </div>
                    <span className="text-sm font-medium text-gray-900">Use a different email</span>
                  </button>

                  {!formData.useOriginalEmail && (
                    <input
                      type="email"
                      name="notificationEmail"
                      value={formData.notificationEmail}
                      onChange={handleChange}
                      placeholder="notifications@example.com"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                    />
                  )}
                </div>

                {/* Future PMS integrations hint */}
                <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500">
                    <span className="font-medium">Coming soon:</span> Direct integration with Salesforce, HubSpot, Appfolio, Yardi, PropertyBase, Reapit, and more.
                  </p>
                </div>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  onClick={prevStep}
                  className="flex-1 py-3 px-4 border border-gray-300 rounded-lg shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  Back
                </button>
                <button
                  onClick={handleSubmit}
                  disabled={!canProceed() || loading}
                  className="flex-1 py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? "Creating account..." : "Create account"}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth-context";

const features = [
  {
    icon: "🏠",
    title: "Built for Real Estate",
    description:
      "Trained to handle property inquiries, schedule showings, and qualify leads 24/7.",
  },
  {
    icon: "🤖",
    title: "AI-Powered Conversations",
    description:
      "Natural language processing that understands context and provides intelligent responses.",
  },
  {
    icon: "📞",
    title: "Never Miss a Lead",
    description:
      "Answer every call instantly, even at 2 AM. Convert more prospects into clients.",
  },
  {
    icon: "📊",
    title: "CRM Integration",
    description:
      "All leads automatically captured with full call transcripts and contact details.",
  },
  {
    icon: "📅",
    title: "Smart Scheduling",
    description:
      "AI books showings directly into your calendar based on your availability.",
  },
  {
    icon: "💰",
    title: "Pay Per Minute",
    description:
      "Only $0.24/minute. No monthly fees, no contracts. Scale as you grow.",
  },
];

const testimonials = [
  {
    quote:
      "I was losing leads to voicemail. Now my AI receptionist handles calls while I'm showing properties. Closed 3 extra deals last month!",
    author: "Sarah Chen",
    role: "Real Estate Agent, Keller Williams",
    avatar: "SC",
  },
  {
    quote:
      "The AI qualifies leads better than my previous answering service. It asks the right questions and I get detailed notes for every call.",
    author: "Marcus Johnson",
    role: "Broker, RE/MAX Premier",
    avatar: "MJ",
  },
  {
    quote:
      "Setup took 5 minutes. The AI learned my business and started taking calls immediately. Game changer for my solo practice.",
    author: "Emily Rodriguez",
    role: "Independent Agent",
    avatar: "ER",
  },
];

const pricingFeatures = [
  "Unlimited calls",
  "24/7 availability",
  "Lead capture & CRM",
  "Call transcripts",
  "Custom AI training",
  "Calendar integration",
  "SMS notifications",
  "No contracts",
];

export default function LandingPage() {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link href="/" className="flex items-center gap-2">
              <div className="w-9 h-9 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold">RE</span>
              </div>
              <span className="font-semibold text-xl text-gray-900">ReceptionAI</span>
            </Link>

            <div className="hidden md:flex items-center gap-8">
              <a href="#features" className="text-gray-600 hover:text-gray-900">
                Features
              </a>
              <a href="#pricing" className="text-gray-600 hover:text-gray-900">
                Pricing
              </a>
              <a href="#testimonials" className="text-gray-600 hover:text-gray-900">
                Testimonials
              </a>
            </div>

            <div className="flex items-center gap-4">
              {user ? (
                <Link
                  href="/dashboard"
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors"
                >
                  Dashboard
                </Link>
              ) : (
                <>
                  <Link
                    href="/login"
                    className="text-gray-600 hover:text-gray-900 font-medium"
                  >
                    Sign in
                  </Link>
                  <Link
                    href="/register"
                    className="px-4 py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors"
                  >
                    Get Started
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-4xl mx-auto">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-50 rounded-full mb-6">
              <span className="w-2 h-2 bg-indigo-500 rounded-full animate-pulse" />
              <span className="text-sm font-medium text-indigo-700">
                AI-Powered • Available 24/7
              </span>
            </div>

            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold text-gray-900 leading-tight">
              Your AI Receptionist for{" "}
              <span className="bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                Real Estate
              </span>
            </h1>

            <p className="mt-6 text-xl text-gray-600 max-w-2xl mx-auto">
              Never miss a lead again. Our AI answers calls, qualifies prospects,
              and books showings while you focus on closing deals.
            </p>

            <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                href="/register"
                className="w-full sm:w-auto px-8 py-4 bg-indigo-600 text-white rounded-xl font-semibold text-lg hover:bg-indigo-700 transition-colors shadow-lg shadow-indigo-500/30"
              >
                Start Free Trial
              </Link>
              <a
                href="#demo"
                className="w-full sm:w-auto px-8 py-4 bg-gray-100 text-gray-900 rounded-xl font-semibold text-lg hover:bg-gray-200 transition-colors flex items-center justify-center gap-2"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z"
                    clipRule="evenodd"
                  />
                </svg>
                Watch Demo
              </a>
            </div>

            <p className="mt-4 text-sm text-gray-500">
              No credit card required • Setup in 5 minutes
            </p>
          </div>

          {/* Hero Image/Mockup */}
          <div className="mt-16 relative">
            <div className="absolute inset-0 bg-gradient-to-t from-white via-transparent to-transparent z-10" />
            <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-2xl p-8 shadow-2xl">
              <div className="bg-white rounded-xl shadow-lg overflow-hidden">
                <div className="bg-gray-800 px-4 py-3 flex items-center gap-2">
                  <div className="w-3 h-3 bg-red-500 rounded-full" />
                  <div className="w-3 h-3 bg-yellow-500 rounded-full" />
                  <div className="w-3 h-3 bg-green-500 rounded-full" />
                </div>
                <div className="p-6 space-y-4">
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center text-sm">
                      🤖
                    </div>
                    <div className="bg-gray-100 rounded-2xl rounded-tl-none px-4 py-3 max-w-md">
                      <p className="text-gray-800">
                        Hi! Thanks for calling Premier Realty. I&apos;m your AI assistant.
                        Are you looking to buy, sell, or rent a property today?
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3 justify-end">
                    <div className="bg-indigo-600 rounded-2xl rounded-tr-none px-4 py-3 max-w-md">
                      <p className="text-white">
                        I&apos;m interested in the 3-bedroom house on Oak Street. Is it
                        still available?
                      </p>
                    </div>
                    <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center text-sm">
                      👤
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center text-sm">
                      🤖
                    </div>
                    <div className="bg-gray-100 rounded-2xl rounded-tl-none px-4 py-3 max-w-md">
                      <p className="text-gray-800">
                        Great choice! Yes, 423 Oak Street is still available at
                        $450,000. It has 3 beds, 2 baths, and a beautiful backyard.
                        Would you like to schedule a showing?
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900">
              Everything you need to capture more leads
            </h2>
            <p className="mt-4 text-xl text-gray-600">
              Purpose-built for real estate professionals
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div
                key={index}
                className="bg-white p-6 rounded-2xl shadow-sm hover:shadow-md transition-shadow"
              >
                <div className="text-4xl mb-4">{feature.icon}</div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900">
              Simple, transparent pricing
            </h2>
            <p className="mt-4 text-xl text-gray-600">
              Only pay for what you use. No monthly fees.
            </p>
          </div>

          <div className="max-w-lg mx-auto">
            <div className="bg-white rounded-3xl shadow-xl overflow-hidden border-2 border-indigo-600">
              <div className="bg-indigo-600 px-8 py-6 text-center">
                <p className="text-indigo-200 font-medium">Pay As You Go</p>
                <div className="mt-2 flex items-baseline justify-center gap-1">
                  <span className="text-5xl font-bold text-white">$0.24</span>
                  <span className="text-indigo-200">/minute</span>
                </div>
              </div>

              <div className="px-8 py-8">
                <ul className="space-y-4">
                  {pricingFeatures.map((feature, index) => (
                    <li key={index} className="flex items-center gap-3">
                      <svg
                        className="w-5 h-5 text-green-500 flex-shrink-0"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                      <span className="text-gray-700">{feature}</span>
                    </li>
                  ))}
                </ul>

                <Link
                  href="/register"
                  className="mt-8 block w-full py-4 bg-indigo-600 text-white rounded-xl font-semibold text-center hover:bg-indigo-700 transition-colors"
                >
                  Start Free Trial
                </Link>

                <p className="mt-4 text-center text-sm text-gray-500">
                  $10 free credits to get started
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section id="testimonials" className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900">
              Loved by real estate professionals
            </h2>
            <p className="mt-4 text-xl text-gray-600">
              Join hundreds of agents already using ReceptionAI
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <div key={index} className="bg-white p-8 rounded-2xl shadow-sm">
                <div className="flex items-center gap-1 mb-4">
                  {[...Array(5)].map((_, i) => (
                    <svg
                      key={i}
                      className="w-5 h-5 text-yellow-400"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                  ))}
                </div>
                <p className="text-gray-700 mb-6">&ldquo;{testimonial.quote}&rdquo;</p>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-indigo-100 rounded-full flex items-center justify-center">
                    <span className="text-sm font-semibold text-indigo-600">
                      {testimonial.avatar}
                    </span>
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900">{testimonial.author}</p>
                    <p className="text-sm text-gray-500">{testimonial.role}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-gradient-to-br from-indigo-600 to-purple-700 rounded-3xl p-12 text-center">
            <h2 className="text-4xl font-bold text-white mb-4">
              Ready to never miss a lead again?
            </h2>
            <p className="text-xl text-indigo-100 mb-8 max-w-2xl mx-auto">
              Join hundreds of real estate professionals using AI to grow their
              business. Start your free trial today.
            </p>
            <Link
              href="/register"
              className="inline-flex items-center px-8 py-4 bg-white text-indigo-600 rounded-xl font-semibold text-lg hover:bg-gray-100 transition-colors"
            >
              Get Started Free
              <svg className="ml-2 w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between">
            <div className="flex items-center gap-2 mb-4 md:mb-0">
              <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">RE</span>
              </div>
              <span className="font-semibold text-white">ReceptionAI</span>
            </div>
            <p className="text-sm">
              © {new Date().getFullYear()} ReceptionAI. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

"use client";

import { ArrowRight, BarChart3, FileUp, Layers, MessageSquare, ShieldAlert, Sparkles } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Logo } from "@/components/Logo";
import { ThemeToggle } from "@/components/ThemeToggle";
import { getToken } from "@/lib/session";

const FEATURES = [
  {
    icon: BarChart3,
    title: "Sentiment dashboard",
    body: "Every review scored instantly. Track average sentiment, the positive/negative split, daily trends and top keywords.",
  },
  {
    icon: ShieldAlert,
    title: "Risk alerts",
    body: "A clear low / medium / high risk level based on your negative-review rate, with the issues driving it.",
  },
  {
    icon: Layers,
    title: "Complaint clustering",
    body: "BERTopic groups reviews into business categories like Delivery, Payment or Product Quality — no tagging needed.",
  },
  {
    icon: MessageSquare,
    title: "AI assistant",
    body: "Ask questions in plain English. Answers are grounded only in your reviews, with the source quotes shown.",
  },
];

const STEPS = [
  { icon: FileUp, title: "Upload a CSV", body: "Any export with a review column — up to 10 MB." },
  { icon: Sparkles, title: "We analyze it", body: "Sentiment, keywords, risk and topics in seconds." },
  { icon: MessageSquare, title: "Ask your data", body: "Get summaries and themes backed by real quotes." },
];

export default function LandingPage() {
  const [signedIn, setSignedIn] = useState(false);

  useEffect(() => {
    // Google OAuth redirects back to the site root; hand the response to the login page.
    if (/(id_token|error)=/.test(window.location.hash)) {
      window.location.replace(`/login${window.location.hash}`);
      return;
    }
    setSignedIn(Boolean(getToken()));
  }, []);

  const primaryHref = signedIn ? "/dashboard" : "/login?mode=register";
  const primaryLabel = signedIn ? "Open dashboard" : "Get started free";

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-40 border-b border-zinc-200 bg-white/80 backdrop-blur dark:border-zinc-800 dark:bg-zinc-950/80">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
          <Logo />
          <nav className="flex items-center gap-1 sm:gap-2">
            <Link href="/chat" className="btn hidden text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-white sm:inline-flex">
              Try the demo
            </Link>
            {!signedIn && (
              <Link href="/login" className="btn text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-white">
                Log in
              </Link>
            )}
            <Link href={primaryHref} className="btn-primary">
              {signedIn ? "Dashboard" : "Sign up"}
            </Link>
            <ThemeToggle />
          </nav>
        </div>
      </header>

      <main>
        {/* Hero */}
        <section className="mx-auto grid max-w-6xl gap-12 px-4 pb-16 pt-16 sm:px-6 lg:grid-cols-2 lg:items-center lg:pt-24">
          <div>
            <span className="inline-flex items-center gap-1.5 rounded-full border border-zinc-200 px-3 py-1 text-xs text-zinc-600 dark:border-zinc-800 dark:text-zinc-400">
              <Sparkles size={12} /> Customer feedback analytics
            </span>
            <h1 className="mt-5 text-4xl font-semibold tracking-tight sm:text-5xl lg:text-6xl">
              Understand your customers without reading every review.
            </h1>
            <p className="muted mt-5 max-w-lg text-base sm:text-lg">
              Upload a CSV of reviews and get sentiment scoring, risk alerts, complaint clustering, and an AI
              assistant that answers only from your own data.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href={primaryHref} className="btn-primary px-5 py-2.5">
                {primaryLabel} <ArrowRight size={16} />
              </Link>
              <Link href="/chat" className="btn-secondary px-5 py-2.5">
                Try the AI demo
              </Link>
            </div>
            <p className="muted mt-4 text-xs">No credit card required · CSV in, insight out</p>
          </div>

          <DashboardPreview />
        </section>

        {/* Features */}
        <section className="border-t border-zinc-200 bg-zinc-50 py-20 dark:border-zinc-800 dark:bg-zinc-900/40">
          <div className="mx-auto max-w-6xl px-4 sm:px-6">
            <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">Everything you need to act on feedback</h2>
            <p className="muted mt-2 max-w-2xl">From raw review text to prioritized issues in one workflow.</p>
            <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {FEATURES.map(({ icon: Icon, title, body }) => (
                <div key={title} className="card p-5">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-zinc-100 dark:bg-zinc-800">
                    <Icon size={18} />
                  </div>
                  <h3 className="mt-4 text-sm font-semibold">{title}</h3>
                  <p className="muted mt-1.5 text-sm leading-relaxed">{body}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* How it works */}
        <section className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
          <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">How it works</h2>
          <ol className="mt-10 grid gap-6 sm:grid-cols-3">
            {STEPS.map(({ icon: Icon, title, body }, i) => (
              <li key={title} className="flex gap-4">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-zinc-200 text-sm font-semibold dark:border-zinc-700">
                  {i + 1}
                </div>
                <div>
                  <h3 className="flex items-center gap-2 text-sm font-semibold">
                    <Icon size={15} className="text-zinc-400" /> {title}
                  </h3>
                  <p className="muted mt-1 text-sm">{body}</p>
                </div>
              </li>
            ))}
          </ol>

          <div className="card mt-16 flex flex-col items-start justify-between gap-6 p-8 sm:flex-row sm:items-center">
            <div>
              <h2 className="text-xl font-semibold tracking-tight">Ready to see what your customers are saying?</h2>
              <p className="muted mt-1 text-sm">Create a free account and upload your first CSV in under a minute.</p>
            </div>
            <Link href={primaryHref} className="btn-primary shrink-0 px-5 py-2.5">
              {primaryLabel} <ArrowRight size={16} />
            </Link>
          </div>
        </section>
      </main>

      <footer className="border-t border-zinc-200 dark:border-zinc-800">
        <div className="muted mx-auto flex max-w-6xl flex-col items-center justify-between gap-2 px-4 py-6 text-xs sm:flex-row sm:px-6">
          <span>© {new Date().getFullYear()} BizInsight AI</span>
          <span>Sentiment analysis · Topic clustering · RAG assistant</span>
        </div>
      </footer>
    </div>
  );
}

function DashboardPreview() {
  const line =
    "0,85 28,88 56,75 84,72 112,67 140,63 168,58 196,50 224,52 252,48 280,42 308,55 336,38 364,42 400,34";
  return (
    <div
      className="rounded-2xl border border-zinc-200 bg-gradient-to-br from-zinc-50 to-zinc-100 p-5 shadow-sm dark:border-zinc-800 dark:from-zinc-900 dark:to-zinc-950"
      aria-hidden="true"
    >
      <div className="grid grid-cols-3 gap-3">
        {[
          ["Avg. sentiment", "+0.42", "text-emerald-600 dark:text-emerald-400"],
          ["Reviews", "2,340", ""],
          ["Risk level", "Low", "text-emerald-600 dark:text-emerald-400"],
        ].map(([label, value, color]) => (
          <div key={label} className="rounded-lg bg-white p-3 shadow-sm dark:bg-zinc-800">
            <div className="text-[10px] text-zinc-400">{label}</div>
            <div className={`text-lg font-semibold ${color}`}>{value}</div>
          </div>
        ))}
      </div>
      <div className="mt-3 rounded-lg bg-white p-4 shadow-sm dark:bg-zinc-800">
        <div className="mb-3 text-[10px] text-zinc-400">Sentiment trend · last 30 days</div>
        <svg viewBox="0 0 400 120" className="h-auto w-full" fill="none">
          <defs>
            <linearGradient id="heroFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#10b981" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#10b981" stopOpacity="0" />
            </linearGradient>
          </defs>
          {[30, 60, 90].map((y) => (
            <line key={y} x1="0" y1={y} x2="400" y2={y} stroke="currentColor" strokeOpacity="0.08" />
          ))}
          <polygon points={`${line} 400,120 0,120`} fill="url(#heroFill)" />
          <polyline points={line} stroke="#10b981" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
      <div className="mt-3 rounded-lg bg-white p-4 shadow-sm dark:bg-zinc-800">
        <div className="mb-2 text-[10px] text-zinc-400">Top complaint clusters</div>
        {[
          ["Delivery Issues", 38],
          ["Product Quality Issues", 24],
          ["Customer Service Issues", 15],
        ].map(([name, pct]) => (
          <div key={name} className="mb-2 last:mb-0">
            <div className="flex justify-between text-[11px]">
              <span>{name}</span>
              <span className="text-zinc-400">{pct}%</span>
            </div>
            <div className="mt-1 h-1.5 rounded-full bg-zinc-100 dark:bg-zinc-700">
              <div className="h-full rounded-full bg-zinc-900 dark:bg-white" style={{ width: `${pct}%` }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api-client";
import { Upload, LogOut, RefreshCw } from "lucide-react";

export default function UnifiedApp() {
  const router = useRouter();
  const [currentView, setCurrentView] = useState<"landing" | "login">("landing");
  const [darkMode, setDarkMode] = useState(false);

  // Auth
  const [isLoginTab, setIsLoginTab] = useState(true);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authError, setAuthError] = useState("");
  const [authLoading, setAuthLoading] = useState(false);
  const [user, setUser] = useState<any>(null);



  useEffect(() => {
    const token = localStorage.getItem("bizinsight_token");
    const storedUser = localStorage.getItem("bizinsight_user");
    if (token && storedUser) {
      setUser(JSON.parse(storedUser));
      router.push("/dashboard");
      return;
    }

    // Handle Google OAuth redirect response from URL hash
    const hash = typeof window !== "undefined" ? window.location.hash : "";
    if (hash && hash.includes("id_token=")) {
      const params = new URLSearchParams(hash.replace("#", "?"));
      const idToken = params.get("id_token");
      if (idToken) {
        window.history.replaceState(null, "", window.location.pathname);
        setAuthLoading(true);
        api.googleLogin({ id_token: idToken })
          .then((res) => {
            localStorage.setItem("bizinsight_token", res.token);
            localStorage.setItem("bizinsight_user", JSON.stringify(res.user));
            setUser(res.user);
            router.push("/dashboard");
          })
          .catch((err) => {
            setAuthError(err.message || "Google authentication failed.");
          })
          .finally(() => {
            setAuthLoading(false);
          });
      }
    }
  }, [router]);

  useEffect(() => {
    if (darkMode) document.documentElement.classList.add("dark");
    else document.documentElement.classList.remove("dark");
  }, [darkMode]);



  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError("");
    setAuthLoading(true);
    try {
      if (isLoginTab) {
        const res = await api.login({ username, password });
        localStorage.setItem("bizinsight_token", res.token);
        localStorage.setItem("bizinsight_user", JSON.stringify(res.user));
        setUser(res.user);
        router.push("/dashboard");
      } else {
        const res = await api.register({ username, email, password, confirm_password: password });
        localStorage.setItem("bizinsight_token", res.token);
        localStorage.setItem("bizinsight_user", JSON.stringify(res.user));
        setUser(res.user);
        router.push("/dashboard");
      }
    } catch (err: any) {
      setAuthError(err.message || "Failed to authenticate.");
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("bizinsight_token");
    localStorage.removeItem("bizinsight_user");
    setUser(null);
    setCurrentView("landing");
  };

  const handleGoogleAuth = () => {
    setAuthError("");
    setAuthLoading(true);

    const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "";

    if (!GOOGLE_CLIENT_ID) {
      setAuthError("Google OAuth is not configured. Please set NEXT_PUBLIC_GOOGLE_CLIENT_ID.");
      setAuthLoading(false);
      return;
    }

    // Perform direct Google OAuth 2.0 redirect (bypasses COOP postMessage blocks entirely)
    const redirectUri = window.location.origin;
    const nonce = Math.random().toString(36).substring(2);
    const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?client_id=${encodeURIComponent(GOOGLE_CLIENT_ID)}&redirect_uri=${encodeURIComponent(redirectUri)}&response_type=id_token&scope=openid%20email%20profile&nonce=${nonce}`;

    window.location.href = authUrl;
  };

  return (
    <div className="min-h-screen bg-white text-black dark:bg-zinc-900 dark:text-white transition-colors">
      {/* TOP BAR */}
      <div className="sticky top-0 z-40 border-b border-zinc-200 dark:border-zinc-800 bg-white/90 dark:bg-zinc-900/90 backdrop-blur">
        <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">
          <button onClick={() => setCurrentView("landing")} className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-zinc-900 dark:bg-white" />
            <span className="text-base font-semibold tracking-tight">BizInsight AI</span>
          </button>
          <div className="hidden sm:flex items-center gap-6 text-sm">
            <button onClick={() => setCurrentView("landing")} className="text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition-colors">Product</button>
            <button onClick={() => { if (user) router.push("/dashboard"); else { setIsLoginTab(true); setCurrentView("login"); } }} className="text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition-colors">Dashboard</button>
            <Link href="/chat" className="text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition-colors">AI Chat</Link>
            {!user ? (
              <button onClick={() => { setIsLoginTab(true); setCurrentView("login"); }} className="text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition-colors">Log in</button>
            ) : (
              <button onClick={handleLogout} className="text-zinc-500 dark:text-zinc-400 hover:text-red-500 transition-colors flex items-center gap-1"><LogOut size={13} /> Logout</button>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => { if (user) router.push("/dashboard"); else { setIsLoginTab(false); setCurrentView("login"); } }} className="text-sm font-medium px-3 py-1.5 rounded-lg bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:opacity-90 transition-opacity">Try the demo</button>
            <button onClick={() => setDarkMode(!darkMode)} className="text-xs px-3 py-1.5 rounded-full border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 shadow">Theme</button>
          </div>
        </div>
      </div>

      {/* LANDING */}
      {currentView === "landing" && (
        <section className="max-w-7xl mx-auto px-6">
          <header className="text-left py-12">
            <h1 className="text-5xl sm:text-6xl font-semibold tracking-tight">Understand your customers <br />without reading every review.</h1>
            <p className="mt-5 text-zinc-500 dark:text-zinc-400 max-w-lg">Upload a CSV of reviews and get sentiment scoring, risk alerts, complaint clustering, and an AI assistant that only answers from your own data.</p>
            <button onClick={() => { if (user) router.push("/dashboard"); else { setIsLoginTab(false); setCurrentView("login"); } }} className="mt-7 inline-block bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 rounded-lg px-6 py-2.5 text-sm font-medium hover:opacity-90 transition-opacity">Get started free</button>
          </header>

          <section className="grid grid-cols-1 lg:grid-cols-3 gap-2 h-full">
            {/* Hero: Dashboard Preview */}
            <div className="lg:col-span-2 bg-gradient-to-br from-zinc-100 to-zinc-200 dark:from-zinc-800 dark:to-zinc-900 rounded-xl p-6 overflow-hidden relative mb-4 lg:mb-0 flex flex-col min-h-[420px]">
              <div className="flex-grow flex flex-col justify-between">
                {/* Mini metric cards */}
                <div className="grid grid-cols-3 gap-3 mb-4">
                  <div className="bg-white dark:bg-zinc-700 rounded-lg p-3 shadow-sm"><div className="text-[9px] text-zinc-400 mb-1">Sentiment</div><div className="text-lg font-semibold text-emerald-600">+0.42</div></div>
                  <div className="bg-white dark:bg-zinc-700 rounded-lg p-3 shadow-sm"><div className="text-[9px] text-zinc-400 mb-1">Reviews</div><div className="text-lg font-semibold">2,340</div></div>
                  <div className="bg-white dark:bg-zinc-700 rounded-lg p-3 shadow-sm"><div className="text-[9px] text-zinc-400 mb-1">Risk</div><div className="text-lg font-semibold text-emerald-600">LOW</div></div>
                </div>
                {/* Chart visualization */}
                <div className="bg-white dark:bg-zinc-700 rounded-lg p-4 shadow-sm flex-grow flex flex-col justify-center">
                  <div className="text-[10px] text-zinc-400 mb-3">Satisfaction trend · last 30 days</div>
                  <svg viewBox="0 0 400 120" className="w-full h-auto" fill="none">
                    <line x1="0" y1="30" x2="400" y2="30" stroke="currentColor" strokeOpacity="0.06" />
                    <line x1="0" y1="60" x2="400" y2="60" stroke="currentColor" strokeOpacity="0.06" />
                    <line x1="0" y1="90" x2="400" y2="90" stroke="currentColor" strokeOpacity="0.06" />
                    <polyline points="0,85 14,80 28,88 42,92 56,75 70,68 84,72 98,60 112,67 126,74 140,63 154,55 168,58 182,68 196,50 210,45 224,52 238,60 252,48 266,40 280,42 294,50 308,55 322,45 336,38 350,35 364,42 378,48 392,40 400,55" stroke="#18181b" className="dark:stroke-white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                    <linearGradient id="heroGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#18181b" stopOpacity="0.1" className="dark:[stop-color:white]" />
                      <stop offset="100%" stopColor="#18181b" stopOpacity="0" className="dark:[stop-color:white]" />
                    </linearGradient>
                    <polygon points="0,85 14,80 28,88 42,92 56,75 70,68 84,72 98,60 112,67 126,74 140,63 154,55 168,58 182,68 196,50 210,45 224,52 238,60 252,48 266,40 280,42 294,50 308,55 322,45 336,38 350,35 364,42 378,48 392,40 400,55 400,120 0,120" fill="url(#heroGrad)" />
                  </svg>
                </div>
                {/* Keywords */}
                <div className="flex gap-2 mt-3 flex-wrap">
                  <span className="text-[10px] px-2.5 py-1 rounded-full bg-red-100 text-red-600 dark:bg-red-500/20 dark:text-red-400">shipping delay</span>
                  <span className="text-[10px] px-2.5 py-1 rounded-full bg-red-100 text-red-600 dark:bg-red-500/20 dark:text-red-400">late delivery</span>
                  <span className="text-[10px] px-2.5 py-1 rounded-full bg-zinc-100 text-zinc-500 dark:bg-zinc-600 dark:text-zinc-300">app crash</span>
                  <span className="text-[10px] px-2.5 py-1 rounded-full bg-zinc-100 text-zinc-500 dark:bg-zinc-600 dark:text-zinc-300">refund</span>
                </div>
              </div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 gap-2 h-full">
              {/* Sentiment Dashboard Card */}
              <div className="flex flex-col border border-zinc-200 dark:border-zinc-800 rounded-xl p-3 hover:shadow-lg cursor-pointer transition-shadow">
                <div className="bg-zinc-50 dark:bg-zinc-800 flex-grow rounded-lg p-3 flex flex-col justify-center items-center gap-2">
                  <svg viewBox="0 0 120 80" className="w-full h-auto max-h-[80px]" fill="none">
                    <rect x="5" y="50" width="12" height="25" rx="2" fill="#34D399" opacity="0.7" />
                    <rect x="22" y="35" width="12" height="40" rx="2" fill="#34D399" opacity="0.8" />
                    <rect x="39" y="45" width="12" height="30" rx="2" fill="#FBBF24" opacity="0.7" />
                    <rect x="56" y="20" width="12" height="55" rx="2" fill="#34D399" />
                    <rect x="73" y="55" width="12" height="20" rx="2" fill="#F87171" opacity="0.7" />
                    <rect x="90" y="30" width="12" height="45" rx="2" fill="#34D399" opacity="0.9" />
                    <circle cx="90" cy="12" r="8" fill="#34D399" opacity="0.15" stroke="#34D399" strokeWidth="1.5" />
                    <polyline points="8,48 25,33 42,43 59,18 76,53 93,28" stroke="#18181b" className="dark:stroke-white" strokeWidth="1.5" strokeLinecap="round" strokeDasharray="3 2" opacity="0.3" />
                  </svg>
                </div>
                <div className="mt-2"><h3 className="text-sm font-medium mb-1">Sentiment Dashboard</h3><p className="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">Trends, distribution, and top keywords in one view.</p></div>
              </div>
              {/* Risk Alerts Card */}
              <div className="flex flex-col border border-zinc-200 dark:border-zinc-800 rounded-xl p-3 hover:shadow-lg cursor-pointer transition-shadow">
                <div className="bg-zinc-50 dark:bg-zinc-800 flex-grow rounded-lg p-3 flex flex-col justify-center items-center gap-1">
                  <svg viewBox="0 0 100 80" className="w-full h-auto max-h-[80px]" fill="none">
                    <polygon points="50,8 90,68 10,68" fill="#FBBF24" opacity="0.15" stroke="#FBBF24" strokeWidth="2" strokeLinejoin="round" />
                    <text x="50" y="55" textAnchor="middle" fontSize="22" fill="#FBBF24" fontWeight="bold">!</text>
                    <rect x="5" y="72" width="90" height="5" rx="2.5" fill="#e4e4e7" className="dark:fill-zinc-700" />
                    <rect x="5" y="72" width="25" height="5" rx="2.5" fill="#34D399" />
                    <circle cx="20" cy="15" r="4" fill="#F87171" opacity="0.3" />
                    <circle cx="80" cy="20" r="3" fill="#34D399" opacity="0.3" />
                  </svg>
                </div>
                <div className="mt-2"><h3 className="text-sm font-medium mb-1">Risk Alerts</h3><p className="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">Automatic spike detection with a risk score.</p></div>
              </div>
              {/* Complaint Clustering Card */}
              <div className="flex flex-col border border-zinc-200 dark:border-zinc-800 rounded-xl p-3 hover:shadow-lg cursor-pointer transition-shadow">
                <div className="bg-zinc-50 dark:bg-zinc-800 flex-grow rounded-lg p-3 flex flex-col justify-center items-center">
                  <svg viewBox="0 0 100 80" className="w-full h-auto max-h-[80px]" fill="none">
                    {/* Blue cluster */}
                    <circle cx="25" cy="30" r="6" fill="#60A5FA" opacity="0.7" /><circle cx="18" cy="38" r="4" fill="#60A5FA" opacity="0.5" /><circle cx="32" cy="36" r="5" fill="#60A5FA" opacity="0.6" /><circle cx="22" cy="24" r="3" fill="#60A5FA" opacity="0.4" />
                    {/* Green cluster */}
                    <circle cx="70" cy="25" r="7" fill="#34D399" opacity="0.7" /><circle cx="78" cy="32" r="4" fill="#34D399" opacity="0.5" /><circle cx="63" cy="20" r="5" fill="#34D399" opacity="0.6" /><circle cx="75" cy="18" r="3" fill="#34D399" opacity="0.4" />
                    {/* Red cluster */}
                    <circle cx="45" cy="58" r="6" fill="#F87171" opacity="0.7" /><circle cx="38" cy="65" r="4" fill="#F87171" opacity="0.5" /><circle cx="52" cy="62" r="5" fill="#F87171" opacity="0.6" /><circle cx="42" cy="52" r="3" fill="#F87171" opacity="0.4" />
                    {/* Purple cluster */}
                    <circle cx="80" cy="60" r="5" fill="#A78BFA" opacity="0.6" /><circle cx="86" cy="55" r="3" fill="#A78BFA" opacity="0.4" /><circle cx="75" cy="66" r="4" fill="#A78BFA" opacity="0.5" />
                  </svg>
                </div>
                <div className="mt-2"><h3 className="text-sm font-medium mb-1">Complaint Clustering</h3><p className="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">Negative reviews grouped into real categories.</p></div>
              </div>
              {/* AI Assistant Card */}
              <Link href="/chat" className="flex flex-col border border-zinc-200 dark:border-zinc-800 rounded-xl p-3 hover:shadow-lg cursor-pointer transition-shadow">
                <div className="bg-zinc-50 dark:bg-zinc-800 flex-grow rounded-lg p-3 flex flex-col justify-center gap-1.5">
                  <div className="flex justify-end"><div className="bg-zinc-900 dark:bg-white rounded-2xl rounded-br-sm px-3 py-1.5 max-w-[75%]"><span className="text-[9px] text-white dark:text-zinc-900">What drives negative reviews?</span></div></div>
                  <div className="flex justify-start"><div className="bg-zinc-200 dark:bg-zinc-700 rounded-2xl rounded-bl-sm px-3 py-1.5 max-w-[80%]"><span className="text-[9px] text-zinc-700 dark:text-zinc-200">Shipping delays, with 184 mentions this week.</span></div></div>
                  <div className="flex justify-end"><div className="bg-zinc-900 dark:bg-white rounded-2xl rounded-br-sm px-3 py-1.5 max-w-[70%]"><span className="text-[9px] text-white dark:text-zinc-900">Show top keywords</span></div></div>
                  <div className="flex gap-1 mt-0.5"><div className="flex-1 h-5 rounded bg-zinc-200 dark:bg-zinc-600 px-2 flex items-center"><span className="text-[7px] text-zinc-400">Ask your data...</span></div><div className="h-5 w-8 rounded bg-zinc-900 dark:bg-white flex items-center justify-center"><span className="text-[7px] text-white dark:text-zinc-900 font-medium">→</span></div></div>
                </div>
                <div className="mt-2"><h3 className="text-sm font-medium mb-1">AI Assistant</h3><p className="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">Ask questions grounded only in your reviews.</p></div>
              </Link>
            </div>
          </section>

          <section className="mt-12 grid grid-cols-2 md:grid-cols-4 gap-1 text-sm">
            {[
              { name: "Shopify", desc: "Storefront reviews" },
              { name: "Zendesk", desc: "Support tickets" },
              { name: "Trustpilot", desc: "Public reviews" },
              { name: "Slack", desc: "Risk alert delivery" },
            ].map((item, i) => (
              <div key={i} className="p-3 flex items-center gap-3 hover:bg-zinc-50 dark:hover:bg-zinc-800 rounded-xl transition">
                <div className="w-10 h-10 rounded-xl bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center text-xs font-semibold text-zinc-500">{item.name[0]}</div>
                <div><div className="font-normal">{item.name}</div><div className="text-xs text-gray-500 dark:text-gray-400">{item.desc}</div></div>
              </div>
            ))}
          </section>

          <footer className="text-center py-12 text-zinc-500 dark:text-zinc-400 text-sm">No credit card &bull; CSV in, insight out</footer>
        </section>
      )}

      {/* LOGIN / REGISTER */}
      {currentView === "login" && (
        <section className="min-h-[calc(100vh-57px)] flex flex-col items-center justify-center px-6 py-16">
          <div className="w-full max-w-sm border border-zinc-200 dark:border-zinc-800 rounded-xl p-8 bg-white dark:bg-zinc-900 shadow-sm">
            <div className="grid grid-cols-2 mb-7 rounded-lg bg-zinc-100 dark:bg-zinc-800 p-1 text-sm font-medium">
              <button onClick={() => setIsLoginTab(true)} className={`py-1.5 rounded-md transition-colors ${isLoginTab ? "bg-white dark:bg-zinc-700 shadow text-zinc-900 dark:text-white" : "text-zinc-500 dark:text-zinc-400"}`}>Log in</button>
              <button onClick={() => setIsLoginTab(false)} className={`py-1.5 rounded-md transition-colors ${!isLoginTab ? "bg-white dark:bg-zinc-700 shadow text-zinc-900 dark:text-white" : "text-zinc-500 dark:text-zinc-400"}`}>Create account</button>
            </div>
            <h1 className="text-xl font-semibold tracking-tight mb-1">{isLoginTab ? "Welcome back" : "Create your account"}</h1>
            <p className="text-sm text-zinc-500 dark:text-zinc-400 mb-6">{isLoginTab ? "Log in to see your sentiment dashboard." : "Start catching risk before your customers escalate."}</p>
            <div className="w-full mb-3 flex flex-col items-center justify-center min-h-[44px]">
              <button
                type="button"
                onClick={handleGoogleAuth}
                disabled={authLoading}
                className="w-full flex items-center justify-center gap-3 border border-zinc-200 dark:border-zinc-700 rounded-lg py-2.5 text-sm font-medium hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors disabled:opacity-50"
              >
                <svg width="18" height="18" viewBox="0 0 48 48">
                  <path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.7 32.9 29.3 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34.5 6.1 29.5 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.7-.4-3.5z"/>
                  <path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.6 15.9 18.9 13 24 13c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34.5 6.1 29.5 4 24 4c-7.7 0-14.4 4.3-17.7 10.7z"/>
                  <path fill="#4CAF50" d="M24 44c5.3 0 10.2-2 13.9-5.4l-6.4-5.4C29.4 34.7 26.8 36 24 36c-5.3 0-9.7-3.1-11.3-7.6l-6.6 5.1C9.5 39.6 16.2 44 24 44z"/>
                  <path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.3-2.2 4.2-4 5.6l6.4 5.4C41.5 35.7 44 30.3 44 24c0-1.3-.1-2.7-.4-3.5z"/>
                </svg>
                {authLoading ? "Signing in..." : "Continue with Google"}
              </button>
            </div>
            <div className="flex items-center gap-3 mb-5"><div className="flex-1 h-px bg-zinc-200 dark:bg-zinc-800" /><span className="text-xs text-zinc-400 dark:text-zinc-500">or</span><div className="flex-1 h-px bg-zinc-200 dark:bg-zinc-800" /></div>
            <form onSubmit={handleAuthSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-zinc-600 dark:text-zinc-400 mb-1.5">Username</label>
                <input type="text" value={username} onChange={e => setUsername(e.target.value)} placeholder="your_username" className="w-full border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-white" />
              </div>
              {!isLoginTab && (
                <div>
                  <label className="block text-xs font-medium text-zinc-600 dark:text-zinc-400 mb-1.5">Email</label>
                  <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@company.com" className="w-full border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-white" />
                </div>
              )}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block text-xs font-medium text-zinc-600 dark:text-zinc-400">Password</label>
                  {isLoginTab && <a href="#" className="text-xs text-zinc-500 dark:text-zinc-400 hover:underline">Forgot?</a>}
                </div>
                <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" className="w-full border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-white" />
              </div>
              {authError && <p className="text-xs text-red-500">{authError}</p>}
              <button type="submit" disabled={authLoading} className="w-full bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 rounded-lg py-2.5 text-sm font-medium hover:opacity-90 transition-opacity mt-2 disabled:opacity-50">
                {authLoading ? "Please wait..." : isLoginTab ? "Log in" : "Create account"}
              </button>
            </form>
            <p className="text-center text-sm text-zinc-500 dark:text-zinc-400 mt-6">
              {isLoginTab ? "Don't have an account? " : "Already have an account? "}
              <button onClick={() => setIsLoginTab(!isLoginTab)} className="font-medium text-zinc-900 dark:text-white hover:underline">{isLoginTab ? "Create one" : "Log in"}</button>
            </p>
          </div>
          <p className="text-xs text-zinc-400 dark:text-zinc-600 mt-8 max-w-sm text-center">By continuing, you agree to BizInsight AI&apos;s Terms of Service and Privacy Policy.</p>
        </section>
      )}
    </div>
  );
}

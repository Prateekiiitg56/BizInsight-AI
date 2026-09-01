"use client";

import React, { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api-client";
import { Upload, RefreshCw, AlertCircle, BarChart2, ArrowUpRight } from "lucide-react";

export default function DashboardHome() {
  const router = useRouter();
  const [data, setData] = useState<any>(null);
  const [alerts, setAlerts] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(false);
  const [reviewCountAnimated, setReviewCountAnimated] = useState(0);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const countRef = useRef(false);

  const [chatMessages, setChatMessages] = useState<{ role: string; content: string }[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const chatLogEndRef = useRef<HTMLDivElement>(null);

  const fetchData = async () => {
    const token = localStorage.getItem("bizinsight_token");
    if (!token) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setFetchError(false);
    try {
      const [summary, risk] = await Promise.all([api.getSummary(token), api.getAlerts(token)]);
      setData(summary);
      setAlerts(risk);
      setLastUpdated(new Date());
    } catch (err: any) {
      if (err?.message?.toLowerCase().includes("token") || err?.message?.toLowerCase().includes("log in") || err?.message?.toLowerCase().includes("invalid")) {
        localStorage.removeItem("bizinsight_token");
        localStorage.removeItem("bizinsight_user");
        router.push("/");
        return;
      }
      setFetchError(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  // Animate review count
  useEffect(() => {
    if (loading || countRef.current || !data) return;
    countRef.current = true;
    const target = data.total_reviews;
    if (target === 0) { setReviewCountAnimated(0); return; }
    const dur = 1000, start = performance.now();
    function tick(now: number) {
      const t = Math.min(1, (now - start) / dur);
      setReviewCountAnimated(Math.floor(t * target));
      if (t < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }, [loading, data]);

  const handleChatSend = async (text: string) => {
    if (!text.trim() || chatLoading) return;
    setChatMessages(prev => [...prev, { role: "user", content: text }]);
    setChatInput("");
    setChatLoading(true);
    const token = localStorage.getItem("bizinsight_token") || "";
    try {
      const res = await api.chat(token, { question: text, use_memory: false });
      setChatMessages(prev => [...prev, { role: "assistant", content: res.answer }]);
    } catch {
      const fallbackMsg = "⚠️ The backend service might not be loaded properly or is spinning up due to the Render free-tier setup (takes ~30-50 seconds to wake from sleep).\n\nPlease wait a moment and try again!";
      setChatMessages(prev => [...prev, { role: "assistant", content: fallbackMsg }]);
    } finally {
      setChatLoading(false);
      setTimeout(() => chatLogEndRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
    }
  };

  const [exportError, setExportError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);

  const handleExport = async () => {
    const token = localStorage.getItem("bizinsight_token");
    if (!token) return;
    setExportError(null);
    setExporting(true);
    try {
      const res = await fetch(api.getExportUrl(token));
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setExportError(err.detail || "Export failed. Please try again.");
        setTimeout(() => setExportError(null), 5000);
        return;
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "bizinsight_feedback.csv";
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch {
      setExportError("Network error. Could not reach the server.");
      setTimeout(() => setExportError(null), 5000);
    } finally {
      setExporting(false);
    }
  };

  // Format "last updated" relative time
  const getRelativeTime = () => {
    if (!lastUpdated) return "";
    const diff = Math.floor((Date.now() - lastUpdated.getTime()) / 1000);
    if (diff < 60) return "just now";
    if (diff < 3600) return `${Math.floor(diff / 60)} minutes ago`;
    return `${Math.floor(diff / 3600)} hours ago`;
  };

  if (loading) {
    return (<div className="min-h-[60vh] flex flex-col items-center justify-center gap-3"><RefreshCw className="animate-spin text-zinc-400" size={24} /><p className="text-sm text-zinc-500">Loading dashboard...</p></div>);
  }

  // Check if user has no data (either API returned 0 reviews, or API failed)
  const hasNoData = !data || data.total_reviews === 0;

  // Empty state — user hasn't uploaded anything yet
  if (hasNoData && !fetchError) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center gap-6 text-center">
        <div className="w-16 h-16 rounded-2xl bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center">
          <BarChart2 size={28} className="text-zinc-400" />
        </div>
        <div>
          <h2 className="text-xl font-semibold tracking-tight mb-2">No data yet</h2>
          <p className="text-sm text-zinc-500 dark:text-zinc-400 max-w-sm">Upload a CSV file with your customer reviews to see sentiment analysis, trends, and insights here.</p>
        </div>
        <Link href="/dashboard/upload" className="text-sm font-medium px-6 py-2.5 rounded-lg bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:opacity-90 transition-opacity flex items-center gap-2">
          <Upload size={16} /> Upload your first CSV
        </Link>
      </div>
    );
  }

  // Error state — backend unreachable
  if (fetchError && hasNoData) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center gap-6 text-center">
        <div className="w-16 h-16 rounded-2xl bg-red-50 dark:bg-red-950/30 flex items-center justify-center">
          <AlertCircle size={28} className="text-red-500" />
        </div>
        <div>
          <h2 className="text-xl font-semibold tracking-tight mb-2">Couldn&apos;t load dashboard</h2>
          <p className="text-sm text-zinc-500 dark:text-zinc-400 max-w-sm">The backend service may be starting up (free-tier cold starts take ~30-50s). Please wait a moment and try again.</p>
        </div>
        <button onClick={() => { countRef.current = false; fetchData(); }} className="text-sm font-medium px-6 py-2.5 rounded-lg bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:opacity-90 transition-opacity flex items-center gap-2">
          <RefreshCw size={16} /> Retry
        </button>
      </div>
    );
  }

  // We have real data — render the dashboard
  const d = data;
  const a = alerts || { risk_level: "low", negative_percent: 0, threshold: 40, total_reviews: 0, top_issues: [] };
  const riskColor = a.risk_level === "high" ? "text-red-500" : a.risk_level === "medium" ? "text-amber-500" : "text-emerald-600 dark:text-emerald-400";

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">Dashboard</h2>
          {lastUpdated && <p className="text-sm text-zinc-500 dark:text-zinc-400">Last updated {getRelativeTime()}</p>}
        </div>
        <div className="flex items-center gap-2">
          <Link href="/dashboard/upload" className="text-sm font-medium px-4 py-2 rounded-lg bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:opacity-90 transition-opacity flex items-center gap-1.5">
            <Upload size={14} /> Import CSV
          </Link>
          <button onClick={handleExport} disabled={exporting} className="text-sm font-medium px-4 py-2 rounded-lg border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors flex items-center gap-1.5 disabled:opacity-50">
            {exporting && <RefreshCw className="animate-spin text-zinc-400" size={14} />}
            {exporting ? "Exporting..." : "Export report"}
          </button>
        </div>
      </div>

      {exportError && (
        <div className="mb-6 p-4 rounded-xl border border-red-200 dark:border-red-900/50 bg-red-50 dark:bg-red-950/30 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-red-100 dark:bg-red-900/40 text-red-600 dark:text-red-400 flex items-center justify-center shrink-0">
              <AlertCircle size={18} />
            </div>
            <div>
              <p className="text-sm font-medium text-red-900 dark:text-red-200">{exportError}</p>
              <p className="text-xs text-red-600/80 dark:text-red-400/80 mt-0.5">You need to upload at least one CSV dataset before generating reports.</p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Link href="/dashboard/upload" className="text-xs font-medium px-3 py-1.5 rounded-lg bg-red-600 dark:bg-red-500 text-white hover:opacity-90 transition-opacity">
              Upload Reviews
            </Link>
            <button onClick={() => setExportError(null)} className="text-xs text-red-500 hover:text-red-700 dark:hover:text-red-300 px-2 py-1">
              Dismiss
            </button>
          </div>
        </div>
      )}

      {/* Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
        <div className="border border-zinc-200 dark:border-zinc-800 rounded-xl p-5">
          <div className="text-xs text-zinc-500 dark:text-zinc-400 mb-2">Avg. sentiment</div>
          <div className="text-2xl font-semibold">{d.avg_sentiment > 0 ? "+" : ""}{d.avg_sentiment.toFixed(2)}</div>
          <div className="text-xs text-zinc-500 dark:text-zinc-400 mt-1">{d.positive_percent.toFixed(0)}% positive</div>
        </div>
        <div className="border border-zinc-200 dark:border-zinc-800 rounded-xl p-5">
          <div className="text-xs text-zinc-500 dark:text-zinc-400 mb-2">Reviews analyzed</div>
          <div className="text-2xl font-semibold">{reviewCountAnimated.toLocaleString()}</div>
          <div className="text-xs text-zinc-500 dark:text-zinc-400 mt-1">{d.negative_count} negative · {d.neutral_count} neutral</div>
        </div>
        <div className="border border-zinc-200 dark:border-zinc-800 rounded-xl p-5">
          <div className="text-xs text-zinc-500 dark:text-zinc-400 mb-2">Risk level</div>
          <div className={`text-2xl font-semibold uppercase ${riskColor}`}>{a.risk_level}</div>
          <div className="text-xs text-zinc-500 dark:text-zinc-400 mt-1">{a.negative_percent.toFixed(1)}% negative rate</div>
        </div>
        <div className="border border-zinc-200 dark:border-zinc-800 rounded-xl p-5">
          <div className="text-xs text-zinc-500 dark:text-zinc-400 mb-2">Negative spike</div>
          <div className="text-2xl font-semibold">{a.risk_level === "high" ? "Detected" : "None"}</div>
          <div className="text-xs text-zinc-500 dark:text-zinc-400 mt-1">threshold: ≥{a.threshold || 40}% negative</div>
        </div>
      </div>

      {/* Chart area + Keywords */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3 mb-6">
        <div className="lg:col-span-2 border border-zinc-200 dark:border-zinc-800 rounded-xl p-5">
          <h3 className="text-sm font-medium mb-4">Satisfaction trend <span className="text-zinc-400 dark:text-zinc-500 font-normal">· from your data</span></h3>
          <SatisfactionChart trendData={d.trend} />
        </div>
        <div className="border border-zinc-200 dark:border-zinc-800 rounded-xl p-5">
          <h3 className="text-sm font-medium mb-4">Top complaint keywords</h3>
          <div className="flex flex-wrap gap-2">
            {d.top_keywords && d.top_keywords.length > 0 ? (
              d.top_keywords.map((kw: any, idx: number) => (
                <span key={idx} className={`text-xs px-3 py-1.5 rounded-full ${idx < 2 ? "bg-red-50 text-red-600 dark:bg-red-500/10 dark:text-red-400" : "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400"}`}>
                  {kw.keyword} <span className="opacity-60">({kw.frequency})</span>
                </span>
              ))
            ) : (
              <p className="text-xs text-zinc-400">No keywords extracted yet.</p>
            )}
          </div>
        </div>
      </div>

      {/* Top issues from alerts */}
      {a.top_issues && a.top_issues.length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-medium mb-3">Top negative issues</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {a.top_issues.map((issue: string, i: number) => (
              <div key={i} className="border border-zinc-200 dark:border-zinc-800 rounded-xl p-4 hover:shadow-lg transition-shadow">
                <div className="text-xs text-zinc-400 dark:text-zinc-500 mb-1">ISSUE #{i + 1}</div>
                <h4 className="font-medium text-sm">{issue}</h4>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Chat */}
      <div className="border border-zinc-200 dark:border-zinc-800 rounded-xl p-5">
        <h3 className="text-sm font-medium mb-4">Ask your data <span className="text-zinc-400 dark:text-zinc-500 font-normal">· grounded only in your reviews</span></h3>
        <div className="flex flex-col gap-3 mb-4 max-h-48 overflow-y-auto pr-2 no-scrollbar">
          {chatMessages.length === 0 && (
            <p className="text-xs text-zinc-400 dark:text-zinc-500 text-center py-4">Ask a question about your uploaded reviews to get started.</p>
          )}
          {chatMessages.map((m, idx) => (
            <div key={idx} className={`max-w-[80%] text-sm px-4 py-2 rounded-2xl ${m.role === "user" ? "self-end bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 rounded-br-sm" : "self-start bg-zinc-100 dark:bg-zinc-800 rounded-bl-sm"}`}>
              {m.content}
            </div>
          ))}
          {chatLoading && (<div className="self-start max-w-[80%] bg-zinc-100 dark:bg-zinc-800 text-xs px-4 py-2 rounded-2xl rounded-bl-sm text-zinc-500 flex items-center gap-2"><RefreshCw className="animate-spin" size={12} /> Evaluating context...</div>)}
          <div ref={chatLogEndRef} />
        </div>
        <form onSubmit={e => { e.preventDefault(); handleChatSend(chatInput); }} className="flex gap-2">
          <input type="text" value={chatInput} onChange={e => setChatInput(e.target.value)} placeholder="Ask a question about your reviews…" className="flex-1 border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-white" disabled={chatLoading} />
          <button type="submit" disabled={chatLoading || !chatInput.trim()} className="px-4 py-2 rounded-lg bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50">Ask</button>
        </form>
      </div>
    </div>
  );
}

/** Canvas-based satisfaction chart using real trend data from API */
function SatisfactionChart({ trendData }: { trendData?: { date: string; avg_sentiment: number }[] }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const draw = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const parent = canvas.parentElement;
    if (!parent) return;
    const w = canvas.width = parent.clientWidth - 40;
    const h = canvas.height = 200;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.clearRect(0, 0, w, h);

    const isDark = document.documentElement.classList.contains("dark");

    // Use real trend data if available
    const pts = trendData && trendData.length > 0
      ? trendData.map(t => t.avg_sentiment)
      : [];

    if (pts.length === 0) {
      // No data — show empty state
      ctx.fillStyle = isDark ? "rgba(255,255,255,0.3)" : "rgba(0,0,0,0.3)";
      ctx.font = "13px system-ui, sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("No trend data yet — upload reviews to see the chart", w / 2, h / 2);
      return;
    }

    const dataMin = Math.min(...pts);
    const dataMax = Math.max(...pts);
    const range = dataMax - dataMin || 0.1;
    const min = dataMin - range * 0.15;
    const max = dataMax + range * 0.15;
    const pad = 10;
    const stepX = pts.length > 1 ? (w - pad * 2) / (pts.length - 1) : 0;

    // Grid lines
    ctx.strokeStyle = isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.06)";
    for (let i = 0; i <= 3; i++) {
      const y = pad + ((h - pad * 2) / 3) * i;
      ctx.beginPath(); ctx.moveTo(pad, y); ctx.lineTo(w - pad, y); ctx.stroke();
    }

    // Data line
    ctx.beginPath();
    pts.forEach((v, i) => {
      const x = pad + i * stepX;
      const y = h - pad - ((v - min) / (max - min)) * (h - pad * 2);
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.strokeStyle = isDark ? "#ffffff" : "#18181b";
    ctx.lineWidth = 2;
    ctx.stroke();
  };

  useEffect(() => {
    draw();
    window.addEventListener("resize", draw);
    const observer = new MutationObserver(draw);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
    return () => { window.removeEventListener("resize", draw); observer.disconnect(); };
  }, [trendData]);

  return <canvas ref={canvasRef} className="w-full" style={{ height: 200 }} />;
}

"use client";

import React, { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { api } from "@/lib/api-client";
import { Upload, RefreshCw, AlertCircle } from "lucide-react";

const fallbackData = {
  total_reviews: 2340, positive_count: 1420, negative_count: 610, neutral_count: 310,
  avg_sentiment: 0.42, positive_percent: 60.7, neutral_percent: 13.2, negative_percent: 26.1,
  top_keywords: [
    { keyword: "shipping delay", frequency: 184 }, { keyword: "late delivery", frequency: 140 },
    { keyword: "app crash", frequency: 96 }, { keyword: "refund", frequency: 61 }, { keyword: "support wait", frequency: 44 },
  ],
};
const fallbackAlerts = { risk_level: "low", negative_percent: 26.1, threshold: 40, total_reviews: 2340, top_issues: [] };

export default function DashboardHome() {
  const [data, setData] = useState<any>(null);
  const [alerts, setAlerts] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [reviewCountAnimated, setReviewCountAnimated] = useState(0);
  const countRef = useRef(false);

  const [chatMessages, setChatMessages] = useState<{ role: string; content: string }[]>([
    { role: "user", content: "What's driving the negative reviews this week?" },
    { role: "assistant", content: "Delivery delays are the top driver, with 184 reviews mentioning late shipping, up from 140 last week." },
  ]);
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
    try {
      const [summary, risk] = await Promise.all([api.getSummary(token), api.getAlerts(token)]);
      setData(summary);
      setAlerts(risk);
    } catch {
      // Use fallback data on error
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  // Use real data if available, else fallback (like the reference HTML)
  const d = data || fallbackData;
  const a = alerts || fallbackAlerts;

  useEffect(() => {
    if (loading || countRef.current) return;
    countRef.current = true;
    const target = d.total_reviews;
    const dur = 1000, start = performance.now();
    function tick(now: number) {
      const t = Math.min(1, (now - start) / dur);
      setReviewCountAnimated(Math.floor(t * target));
      if (t < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }, [loading, d.total_reviews]);

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
      setChatMessages(prev => [...prev, { role: "assistant", content: "This is a UI demo; please check your backend RAG configuration." }]);
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

  if (loading) {
    return (<div className="min-h-[60vh] flex flex-col items-center justify-center gap-3"><RefreshCw className="animate-spin text-zinc-400" size={24} /><p className="text-sm text-zinc-500">Loading dashboard...</p></div>);
  }

  const riskColor = a.risk_level === "high" ? "text-red-500" : a.risk_level === "medium" ? "text-amber-500" : "text-emerald-600 dark:text-emerald-400";

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">Dashboard</h2>
          <p className="text-sm text-zinc-500 dark:text-zinc-400">Last updated 4 minutes ago</p>
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
        <div className="mb-6 p-4 rounded-xl border border-red-200 dark:border-red-900/50 bg-red-50 dark:bg-red-950/30 flex items-center justify-between gap-4 animate-in fade-in slide-in-from-top-2 duration-200">
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

      {/* Metrics: matches reference exactly */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
        <div className="border border-zinc-200 dark:border-zinc-800 rounded-xl p-5">
          <div className="text-xs text-zinc-500 dark:text-zinc-400 mb-2">Avg. sentiment</div>
          <div className="text-2xl font-semibold">{d.avg_sentiment > 0 ? "+" : ""}{d.avg_sentiment.toFixed(2)}</div>
          <div className="text-xs text-emerald-600 dark:text-emerald-400 mt-1">▲ 0.06 vs last week</div>
        </div>
        <div className="border border-zinc-200 dark:border-zinc-800 rounded-xl p-5">
          <div className="text-xs text-zinc-500 dark:text-zinc-400 mb-2">Reviews analyzed</div>
          <div className="text-2xl font-semibold">{reviewCountAnimated.toLocaleString()}</div>
          <div className="text-xs text-emerald-600 dark:text-emerald-400 mt-1">▲ 312 this week</div>
        </div>
        <div className="border border-zinc-200 dark:border-zinc-800 rounded-xl p-5">
          <div className="text-xs text-zinc-500 dark:text-zinc-400 mb-2">Risk level</div>
          <div className={`text-2xl font-semibold uppercase ${riskColor}`}>{a.risk_level}</div>
          <div className="text-xs text-zinc-500 dark:text-zinc-400 mt-1">stable for 9 days</div>
        </div>
        <div className="border border-zinc-200 dark:border-zinc-800 rounded-xl p-5">
          <div className="text-xs text-zinc-500 dark:text-zinc-400 mb-2">Negative spike</div>
          <div className="text-2xl font-semibold">{a.risk_level === "high" ? "Detected" : "None"}</div>
          <div className="text-xs text-zinc-500 dark:text-zinc-400 mt-1">threshold: ≥15pt jump</div>
        </div>
      </div>

      {/* Chart area + Keywords: matches reference */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3 mb-6">
        <div className="lg:col-span-2 border border-zinc-200 dark:border-zinc-800 rounded-xl p-5">
          <h3 className="text-sm font-medium mb-4">Satisfaction trend <span className="text-zinc-400 dark:text-zinc-500 font-normal">· last 30 days</span></h3>
          <SatisfactionChart />
        </div>
        <div className="border border-zinc-200 dark:border-zinc-800 rounded-xl p-5">
          <h3 className="text-sm font-medium mb-4">Top complaint keywords</h3>
          <div className="flex flex-wrap gap-2">
            {(d.top_keywords || fallbackData.top_keywords).map((kw: any, idx: number) => (
              <span key={idx} className={`text-xs px-3 py-1.5 rounded-full ${idx < 2 ? "bg-red-50 text-red-600 dark:bg-red-500/10 dark:text-red-400" : "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400"}`}>
                {kw.keyword}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Clusters: matches reference */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-6">
        {[
          { cat: "DELIVERY", count: 184, title: "Shipping & delivery delays", desc: "Recurring theme across the last 2 weeks." },
          { cat: "TECHNICAL", count: 96, title: "App reliability", desc: "Mostly mobile users, Android." },
          { cat: "PAYMENT", count: 61, title: "Refund processing time", desc: "Growing slowly, watch next week." },
        ].map((c, i) => (
          <div key={i} className="border border-zinc-200 dark:border-zinc-800 rounded-xl p-4 hover:shadow-lg transition-shadow cursor-pointer">
            <div className="text-xs text-zinc-400 dark:text-zinc-500 mb-1">CATEGORY · {c.cat} <span className="float-right">{c.count}</span></div>
            <h4 className="font-medium text-sm mb-1">{c.title}</h4>
            <p className="text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed">{c.desc}</p>
          </div>
        ))}
      </div>

      {/* Chat: matches reference */}
      <div className="border border-zinc-200 dark:border-zinc-800 rounded-xl p-5">
        <h3 className="text-sm font-medium mb-4">Ask your data <span className="text-zinc-400 dark:text-zinc-500 font-normal">· grounded only in your reviews</span></h3>
        <div className="flex flex-col gap-3 mb-4 max-h-48 overflow-y-auto pr-2 no-scrollbar">
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

/** Canvas-based satisfaction chart matching the reference HTML exactly */
function SatisfactionChart() {
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

    const pts = [0.31,0.33,0.30,0.28,0.35,0.38,0.36,0.40,0.37,0.34,0.39,0.42,0.41,0.38,0.44,0.46,0.43,0.40,0.45,0.48,0.47,0.44,0.42,0.46,0.49,0.50,0.47,0.45,0.48,0.42];
    const max = 0.6, min = 0.1, pad = 10;
    const stepX = (w - pad * 2) / (pts.length - 1);
    const isDark = document.documentElement.classList.contains("dark");

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
    // Redraw on theme change
    const observer = new MutationObserver(draw);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
    return () => { window.removeEventListener("resize", draw); observer.disconnect(); };
  }, []);

  return <canvas ref={canvasRef} className="w-full" style={{ height: 200 }} />;
}

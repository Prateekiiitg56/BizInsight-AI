"use client";

import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import { api } from "@/lib/api-client";
import { Send, Bot, User, Layers, ChevronDown, ChevronUp, RefreshCw, ArrowLeft, MessageSquare, Sparkles } from "lucide-react";

interface Message { role: "user" | "assistant"; content: string; sources?: string[]; }

export default function PublicChatPage() {
  const [messages, setMessages] = useState<Message[]>([{ role: "assistant", content: "Hello! I'm the BizInsight RAG Bot. Ask me anything about customer reviews loaded into the database. I answer strictly from matching feedback rows." }]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [useMemory, setUseMemory] = useState(true);
  const [sessionId, setSessionId] = useState("");
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);
  const [darkMode, setDarkMode] = useState(false);
  const [dbStatus, setDbStatus] = useState<{ status: string; count: number | null }>({ status: "checking", count: null });
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setSessionId(`s_${Math.random().toString(36).substr(2, 9)}`);
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
    fetch(`${baseUrl}/api/rag/health`).then(r => r.json()).then(d => setDbStatus({ status: "ok", count: d.vector_count ?? 0 })).catch(() => setDbStatus({ status: "error", count: null }));
  }, []);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, loading]);
  useEffect(() => { if (darkMode) document.documentElement.classList.add("dark"); else document.documentElement.classList.remove("dark"); }, [darkMode]);

  const send = async (text: string) => {
    if (!text.trim() || loading) return;
    setMessages(p => [...p, { role: "user", content: text }]);
    setInput(""); setLoading(true);
    const token = localStorage.getItem("bizinsight_token") || "";
    try {
      const res = await api.chat(token, { question: text, session_id: sessionId, use_memory: useMemory });
      setMessages(p => [...p, { role: "assistant", content: res.answer, sources: res.sources }]);
    } catch (err: any) {
      const fallbackMsg = "⚠️ The backend service might not be loaded properly or is spinning up due to the Render free-tier setup (takes ~30-50 seconds to wake from sleep).\n\nPlease wait a moment and try again! (Or consider donating something so I can upgrade to a paid tier, hehe ☕😉)";
      setMessages(p => [...p, { role: "assistant", content: fallbackMsg }]);
    } finally { setLoading(false); }
  };

  const presets = ["What are the top customer complaints?", "What features do customers love most?", "Summarize feedback regarding pricing.", "Are there any recurring product bugs?"];

  return (
    <div className="min-h-screen bg-white text-black dark:bg-zinc-900 dark:text-white transition-colors flex flex-col">
      {/* Top Bar */}
      <div className="sticky top-0 z-40 border-b border-zinc-200 dark:border-zinc-800 bg-white/90 dark:bg-zinc-900/90 backdrop-blur">
        <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="flex items-center gap-2 text-zinc-500 hover:text-zinc-900 dark:hover:text-white transition-colors text-sm"><ArrowLeft size={14} /> Back</Link>
            <span className="hidden sm:inline h-4 w-px bg-zinc-200 dark:bg-zinc-700" />
            <span className="hidden sm:flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-zinc-900 dark:bg-white" /><span className="text-base font-semibold tracking-tight">BizInsight AI</span></span>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-[10px] text-zinc-500">
              <span className={`w-2 h-2 rounded-full ${dbStatus.status === "ok" ? "bg-emerald-500" : dbStatus.status === "checking" ? "bg-amber-500 animate-pulse" : "bg-red-500"}`} />
              {dbStatus.status === "ok" ? `ChromaDB: ${dbStatus.count} vectors` : dbStatus.status === "checking" ? "Connecting..." : "Offline"}
            </div>
            <Link href="/dashboard" className="text-sm font-medium px-3 py-1.5 rounded-lg bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:opacity-90 transition-opacity">Dashboard</Link>
            <button onClick={() => setDarkMode(!darkMode)} className="text-xs px-3 py-1.5 rounded-full border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 shadow">Theme</button>
          </div>
        </div>
      </div>

      {/* Content */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-6 py-8 flex flex-col">
        <div className="mb-6">
          <h1 className="text-3xl font-semibold tracking-tight flex items-center gap-3"><MessageSquare size={28} /> RAG Chatbot</h1>
          <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-2">Interact with customer reviews using AI-powered context-grounded retrieval. No login required.</p>
        </div>

        <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-6 min-h-0">
          {/* Chat Pane */}
          <div className="lg:col-span-2 flex flex-col border border-zinc-200 dark:border-zinc-800 rounded-xl overflow-hidden min-h-[500px]">
            <div className="flex-1 overflow-y-auto p-4 space-y-3 no-scrollbar">
              {messages.map((m, i) => (
                <div key={i} className={`flex gap-2.5 max-w-[85%] ${m.role === "user" ? "ml-auto flex-row-reverse" : "mr-auto"}`}>
                  <div className="w-7 h-7 rounded-lg shrink-0 flex items-center justify-center bg-zinc-100 dark:bg-zinc-800">
                    {m.role === "user" ? <User size={14} /> : <Bot size={14} />}
                  </div>
                  <div className="space-y-2">
                    <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${m.role === "user" ? "bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 rounded-tr-sm" : "bg-zinc-100 dark:bg-zinc-800 rounded-tl-sm text-zinc-900 dark:text-zinc-100"}`}>
                      {m.role === "user" ? (
                        m.content
                      ) : (
                        <div className="prose dark:prose-invert max-w-none text-sm space-y-2 [&_h2]:text-base [&_h2]:font-bold [&_h2]:mt-3 [&_h2]:mb-1 [&_h2]:tracking-tight [&_ul]:list-disc [&_ul]:pl-4 [&_li]:mt-1.5 [&_p]:mb-2 leading-relaxed">
                          <ReactMarkdown>{m.content}</ReactMarkdown>
                        </div>
                      )}
                    </div>
                    {m.sources && m.sources.length > 0 && (
                      <div>
                        <button onClick={() => setExpandedIdx(expandedIdx === i ? null : i)} className="flex items-center gap-1 text-[10px] text-zinc-400 hover:text-zinc-600">
                          <Layers size={10} /> Sources ({m.sources.length}) {expandedIdx === i ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
                        </button>
                        {expandedIdx === i && (
                          <div className="mt-1.5 space-y-1 pl-2 border-l-2 border-zinc-200 dark:border-zinc-700">
                            {m.sources.map((s, j) => <div key={j} className="p-2 rounded-lg bg-zinc-50 dark:bg-zinc-800/50 text-[10px] text-zinc-500 italic">&ldquo;{s}&rdquo;</div>)}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {loading && (<div className="flex gap-2.5 mr-auto items-center"><div className="w-7 h-7 rounded-lg bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center"><Bot size={14} /></div><div className="px-4 py-2.5 rounded-2xl rounded-tl-sm bg-zinc-100 dark:bg-zinc-800 text-xs text-zinc-500 flex items-center gap-2"><RefreshCw className="animate-spin" size={12} /> Querying ChromaDB...</div></div>)}
              <div ref={endRef} />
            </div>
            <form onSubmit={e => { e.preventDefault(); send(input); }} className="flex gap-2 p-3 border-t border-zinc-200 dark:border-zinc-800">
              <input type="text" value={input} onChange={e => setInput(e.target.value)} placeholder="Ask about customer reviews... (e.g. 'What do users complain about?')" className="flex-1 border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-white" disabled={loading} />
              <button type="submit" disabled={loading || !input.trim()} className="px-4 py-2 rounded-lg bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 text-sm font-medium hover:opacity-90 disabled:opacity-50">Ask</button>
            </form>
          </div>

          {/* Sidebar */}
          <div className="space-y-4">
            <div className="border border-zinc-200 dark:border-zinc-800 rounded-xl p-5">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-medium">Suggested Prompts</h3>
                <label className="flex items-center gap-1.5 text-[10px] text-zinc-500 cursor-pointer"><span>Memory</span><input type="checkbox" checked={useMemory} onChange={() => setUseMemory(!useMemory)} className="accent-zinc-900 dark:accent-white" /></label>
              </div>
              <div className="space-y-2">
                {presets.map((q, i) => (<button key={i} onClick={() => send(q)} disabled={loading} className="w-full text-left text-xs p-3 rounded-lg border border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition disabled:opacity-50">{q}</button>))}
              </div>
            </div>
            <div className="border border-zinc-200 dark:border-zinc-800 rounded-xl p-5">
              <h3 className="text-sm font-medium mb-3 flex items-center gap-2"><Sparkles size={14} className="text-zinc-400" /> How it works</h3>
              <ol className="text-xs text-zinc-500 space-y-1.5 list-decimal list-inside leading-relaxed">
                <li>Your question is vectorized by SentenceTransformers.</li>
                <li>Top semantic matches retrieved from ChromaDB.</li>
                <li>LLM answers strictly from retrieved context.</li>
                <li>Source documents shown for transparency.</li>
              </ol>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

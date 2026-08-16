"use client";

import React, { useState, useRef, useEffect } from "react";
import { api } from "@/lib/api-client";
import { Send, Bot, User, Layers, ChevronDown, ChevronUp, RefreshCw, HelpCircle, Sparkles } from "lucide-react";

interface Message { role: "user" | "assistant"; content: string; sources?: string[]; }

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([{ role: "assistant", content: "Hello! I'm your BizInsight AI assistant. Ask me anything about your loaded customer reviews." }]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [useMemory, setUseMemory] = useState(true);
  const [sessionId, setSessionId] = useState("");
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => { setSessionId(`s_${Math.random().toString(36).substr(2, 9)}`); }, []);
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, loading]);

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
    <div className="h-[calc(100vh-8rem)] flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div><h2 className="text-2xl font-semibold tracking-tight">AI Assistant</h2><p className="text-sm text-zinc-500 dark:text-zinc-400 mt-1">Chat with your review data using RAG retrieval.</p></div>
        <label className="flex items-center gap-2 text-xs text-zinc-500 cursor-pointer select-none">
          <span>Memory</span>
          <input type="checkbox" checked={useMemory} onChange={() => setUseMemory(!useMemory)} className="accent-zinc-900 dark:accent-white" />
        </label>
      </div>

      <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-6 min-h-0">
        {/* Chat */}
        <div className="lg:col-span-2 flex flex-col border border-zinc-200 dark:border-zinc-800 rounded-xl overflow-hidden">
          <div className="flex-1 overflow-y-auto p-4 space-y-3 no-scrollbar">
            {messages.map((m, i) => (
              <div key={i} className={`flex gap-2.5 max-w-[85%] ${m.role === "user" ? "ml-auto flex-row-reverse" : "mr-auto"}`}>
                <div className={`w-7 h-7 rounded-lg shrink-0 flex items-center justify-center text-xs ${m.role === "user" ? "bg-zinc-100 dark:bg-zinc-800" : "bg-zinc-100 dark:bg-zinc-800"}`}>
                  {m.role === "user" ? <User size={14} /> : <Bot size={14} />}
                </div>
                <div className="space-y-2">
                  <div className={`px-4 py-2.5 rounded-2xl text-sm ${m.role === "user" ? "bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 rounded-tr-sm" : "bg-zinc-100 dark:bg-zinc-800 rounded-tl-sm"}`}>{m.content}</div>
                  {m.sources && m.sources.length > 0 && (
                    <div>
                      <button onClick={() => setExpandedIdx(expandedIdx === i ? null : i)} className="flex items-center gap-1 text-[10px] text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300">
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
            {loading && (<div className="flex gap-2.5 mr-auto items-center"><div className="w-7 h-7 rounded-lg bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center"><Bot size={14} /></div><div className="px-4 py-2.5 rounded-2xl rounded-tl-sm bg-zinc-100 dark:bg-zinc-800 text-xs text-zinc-500 flex items-center gap-2"><RefreshCw className="animate-spin" size={12} /> Thinking...</div></div>)}
            <div ref={endRef} />
          </div>
          <form onSubmit={e => { e.preventDefault(); send(input); }} className="flex gap-2 p-3 border-t border-zinc-200 dark:border-zinc-800">
            <input type="text" value={input} onChange={e => setInput(e.target.value)} placeholder="Ask about your reviews..." className="flex-1 border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-white" disabled={loading} />
            <button type="submit" disabled={loading || !input.trim()} className="px-4 py-2 rounded-lg bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 text-sm font-medium hover:opacity-90 disabled:opacity-50"><Send size={15} /></button>
          </form>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          <div className="border border-zinc-200 dark:border-zinc-800 rounded-xl p-5">
            <h3 className="text-sm font-medium mb-3 flex items-center gap-2"><HelpCircle size={14} className="text-zinc-400" /> Suggested Prompts</h3>
            <div className="space-y-2">
              {presets.map((q, i) => (<button key={i} onClick={() => send(q)} disabled={loading} className="w-full text-left text-xs p-3 rounded-lg border border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition disabled:opacity-50">{q}</button>))}
            </div>
          </div>
          <div className="border border-zinc-200 dark:border-zinc-800 rounded-xl p-5">
            <h3 className="text-sm font-medium mb-3 flex items-center gap-2"><Sparkles size={14} className="text-zinc-400" /> RAG Guardrails</h3>
            <ol className="text-xs text-zinc-500 space-y-1.5 list-decimal list-inside leading-relaxed">
              <li>Retrieves top matches from ChromaDB vectors.</li>
              <li>Filters by metadata query expansion.</li>
              <li>Answers strictly from retrieved quotes.</li>
              <li>Reports &ldquo;not found&rdquo; if no matches.</li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  );
}

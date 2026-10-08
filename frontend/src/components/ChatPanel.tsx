"use client";

import { Bot, ChevronDown, ChevronUp, Quote, RotateCcw, Send, User } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { api } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import { Spinner } from "./ui";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: string[];
  error?: boolean;
}

const DEFAULT_SUGGESTIONS = [
  "What are the top customer complaints?",
  "What do customers love most?",
  "Summarize feedback about delivery.",
  "Are there recurring product defects?",
];

function newSessionId() {
  return typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `s_${Date.now().toString(36)}_${Math.random().toString(36).slice(2)}`;
}

export function ChatPanel({
  intro,
  suggestions = DEFAULT_SUGGESTIONS,
  className,
}: {
  intro: string;
  suggestions?: string[];
  className?: string;
}) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [useMemory, setUseMemory] = useState(true);
  const [sessionId, setSessionId] = useState(newSessionId);
  const [openSources, setOpenSources] = useState<number | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  const send = async (text: string) => {
    const question = text.trim();
    if (!question || loading) return;
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setInput("");
    setLoading(true);
    try {
      const res = await api.chat({ question, session_id: sessionId, use_memory: useMemory });
      setMessages((prev) => [...prev, { role: "assistant", content: res.answer, sources: res.sources }]);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Something went wrong. Please try again.";
      setMessages((prev) => [...prev, { role: "assistant", content: message, error: true }]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const reset = () => {
    setMessages([]);
    setOpenSources(null);
    setSessionId(newSessionId());
  };

  return (
    <div className={cn("card flex min-h-0 flex-col overflow-hidden", className)}>
      <div className="flex items-center justify-between gap-3 border-b border-zinc-200 px-4 py-2.5 dark:border-zinc-800">
        <label className="muted flex cursor-pointer select-none items-center gap-2 text-xs">
          <input
            type="checkbox"
            checked={useMemory}
            onChange={(e) => setUseMemory(e.target.checked)}
            className="accent-zinc-900 dark:accent-white"
          />
          Remember conversation
        </label>
        <button
          type="button"
          onClick={reset}
          disabled={messages.length === 0 || loading}
          className="muted inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs hover:bg-zinc-100 hover:text-zinc-900 disabled:opacity-40 dark:hover:bg-zinc-800 dark:hover:text-white"
        >
          <RotateCcw size={12} /> New chat
        </button>
      </div>

      <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto p-4" aria-live="polite">
        <AssistantBubble>
          <p>{intro}</p>
        </AssistantBubble>

        {messages.length === 0 && (
          <div className="grid gap-2 pl-10 sm:grid-cols-2">
            {suggestions.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => send(s)}
                className="rounded-lg border border-zinc-200 px-3 py-2 text-left text-xs text-zinc-700 transition hover:bg-zinc-50 dark:border-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-800"
              >
                {s}
              </button>
            ))}
          </div>
        )}

        {messages.map((m, i) =>
          m.role === "user" ? (
            <div key={i} className="flex justify-end gap-2.5">
              <div className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-tr-sm bg-zinc-900 px-4 py-2.5 text-sm text-white dark:bg-white dark:text-zinc-900">
                {m.content}
              </div>
              <Avatar>
                <User size={14} />
              </Avatar>
            </div>
          ) : (
            <AssistantBubble key={i} error={m.error}>
              {m.error ? <p>{m.content}</p> : <ReactMarkdown>{m.content}</ReactMarkdown>}
              {m.sources && m.sources.length > 0 && (
                <div className="mt-3 border-t border-zinc-200 pt-2 dark:border-zinc-700">
                  <button
                    type="button"
                    onClick={() => setOpenSources(openSources === i ? null : i)}
                    className="muted inline-flex items-center gap-1 text-xs hover:text-zinc-900 dark:hover:text-white"
                    aria-expanded={openSources === i}
                  >
                    <Quote size={11} /> {m.sources.length} source review{m.sources.length > 1 ? "s" : ""}
                    {openSources === i ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                  </button>
                  {openSources === i && (
                    <ul className="mt-2 space-y-1.5 !pl-0">
                      {m.sources.map((s, j) => (
                        <li
                          key={j}
                          className="list-none rounded-md bg-white px-2.5 py-1.5 text-xs italic text-zinc-600 dark:bg-zinc-900 dark:text-zinc-400"
                        >
                          &ldquo;{s}&rdquo;
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </AssistantBubble>
          )
        )}

        {loading && (
          <AssistantBubble>
            <span className="muted inline-flex items-center gap-2 text-xs">
              <Spinner size={12} /> Analyzing reviews…
            </span>
          </AssistantBubble>
        )}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          send(input);
        }}
        className="flex items-end gap-2 border-t border-zinc-200 p-3 dark:border-zinc-800"
      >
        <label htmlFor="chat-input" className="sr-only">
          Ask a question about your reviews
        </label>
        <textarea
          id="chat-input"
          ref={inputRef}
          rows={1}
          value={input}
          maxLength={1000}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send(input);
            }
          }}
          placeholder="Ask about your reviews…"
          className="input max-h-32 min-h-[40px] resize-none"
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()} className="btn-primary h-10 px-3" aria-label="Send">
          <Send size={16} />
        </button>
      </form>
    </div>
  );
}

function Avatar({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300">
      {children}
    </div>
  );
}

function AssistantBubble({ children, error }: { children: React.ReactNode; error?: boolean }) {
  return (
    <div className="flex gap-2.5">
      <Avatar>
        <Bot size={14} />
      </Avatar>
      <div
        className={cn(
          "chat-markdown max-w-[85%] rounded-2xl rounded-tl-sm px-4 py-2.5 text-sm leading-relaxed",
          error
            ? "bg-red-50 text-red-700 dark:bg-red-500/10 dark:text-red-300"
            : "bg-zinc-100 text-zinc-900 dark:bg-zinc-800 dark:text-zinc-100"
        )}
      >
        {children}
      </div>
    </div>
  );
}

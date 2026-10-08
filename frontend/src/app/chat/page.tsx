"use client";

import { ArrowLeft, Info } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { ChatPanel } from "@/components/ChatPanel";
import { Logo } from "@/components/Logo";
import { ThemeToggle } from "@/components/ThemeToggle";
import { getToken } from "@/lib/session";

export default function DemoChatPage() {
  const [signedIn, setSignedIn] = useState(false);

  useEffect(() => setSignedIn(Boolean(getToken())), []);

  return (
    <div className="flex min-h-[100dvh] flex-col">
      <header className="border-b border-zinc-200 dark:border-zinc-800">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3 sm:px-6">
          <div className="flex items-center gap-4">
            <Link href="/" className="muted inline-flex items-center gap-1 text-sm hover:text-zinc-900 dark:hover:text-white">
              <ArrowLeft size={14} /> <span className="hidden sm:inline">Back</span>
            </Link>
            <Logo />
          </div>
          <div className="flex items-center gap-2">
            <Link href={signedIn ? "/dashboard" : "/login?mode=register"} className="btn-primary">
              {signedIn ? "Dashboard" : "Sign up free"}
            </Link>
            <ThemeToggle />
          </div>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col px-4 py-6 sm:px-6">
        <h1 className="text-2xl font-semibold tracking-tight">AI review assistant</h1>
        {signedIn ? (
          <p className="muted mt-1 text-sm">You&apos;re signed in, so answers come from your own uploaded reviews.</p>
        ) : (
          <p className="mt-2 flex items-start gap-2 rounded-lg bg-zinc-100 px-3 py-2 text-sm text-zinc-700 dark:bg-zinc-900 dark:text-zinc-300">
            <Info size={15} className="mt-0.5 shrink-0" />
            <span>
              Demo mode: answers come from a sample set of product reviews.{" "}
              <Link href="/login?mode=register" className="font-medium underline underline-offset-2">
                Create an account
              </Link>{" "}
              to chat with your own data.
            </span>
          </p>
        )}
        <ChatPanel
          className="mt-5 h-[calc(100dvh-14rem)] min-h-[480px]"
          intro={
            signedIn
              ? "Hi! Ask me anything about your customer reviews."
              : "Hi! I'm loaded with sample e-commerce product reviews. Ask what customers think."
          }
        />
      </main>
    </div>
  );
}

"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Logo } from "@/components/Logo";
import { ThemeToggle } from "@/components/ThemeToggle";
import { ErrorBanner, Spinner } from "@/components/ui";
import { api } from "@/lib/api-client";
import { consumeGoogleRedirect, GOOGLE_CLIENT_ID, startGoogleSignIn } from "@/lib/google";
import { getToken, saveSession } from "@/lib/session";
import type { AuthResponse } from "@/lib/types";
import { cn } from "@/lib/utils";

type Mode = "login" | "register";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);

  useEffect(() => {
    const google = consumeGoogleRedirect();
    if (google && "error" in google) {
      setError(google.error);
    } else if (google) {
      setGoogleLoading(true);
      api
        .googleLogin(google.idToken)
        .then(finish)
        .catch((err: Error) => setError(err.message))
        .finally(() => setGoogleLoading(false));
      return;
    }

    if (getToken()) {
      router.replace("/dashboard");
      return;
    }
    if (new URLSearchParams(window.location.search).get("mode") === "register") setMode("register");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function finish(res: AuthResponse) {
    saveSession(res);
    router.replace("/dashboard");
  }

  const switchMode = (next: Mode) => {
    setMode(next);
    setError("");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (mode === "register") {
      if (password.length < 8) return setError("Password must be at least 8 characters.");
      if (password !== confirm) return setError("Passwords do not match.");
    }

    setLoading(true);
    try {
      const res =
        mode === "login"
          ? await api.login({ username: username.trim(), password })
          : await api.register({ username: username.trim(), email: email.trim(), password, confirm_password: confirm });
      finish(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong. Please try again.");
      setLoading(false);
    }
  };

  const busy = loading || googleLoading;

  return (
    <div className="flex min-h-screen flex-col">
      <header className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
        <Logo />
        <ThemeToggle />
      </header>

      <main className="flex flex-1 items-center justify-center px-4 py-10">
        <div className="w-full max-w-sm">
          <div className="card p-6 shadow-sm sm:p-8">
            <div className="mb-6 grid grid-cols-2 rounded-lg bg-zinc-100 p-1 text-sm font-medium dark:bg-zinc-800" role="tablist">
              {(["login", "register"] as const).map((m) => (
                <button
                  key={m}
                  type="button"
                  role="tab"
                  aria-selected={mode === m}
                  onClick={() => switchMode(m)}
                  className={cn(
                    "rounded-md py-1.5 transition",
                    mode === m ? "bg-white shadow-sm dark:bg-zinc-700" : "muted hover:text-zinc-900 dark:hover:text-white"
                  )}
                >
                  {m === "login" ? "Log in" : "Create account"}
                </button>
              ))}
            </div>

            <h1 className="text-xl font-semibold tracking-tight">
              {mode === "login" ? "Welcome back" : "Create your account"}
            </h1>
            <p className="muted mb-6 mt-1 text-sm">
              {mode === "login"
                ? "Log in to see your sentiment dashboard."
                : "Start catching risk before your customers escalate."}
            </p>

            {GOOGLE_CLIENT_ID && (
              <>
                <button
                  type="button"
                  onClick={() => {
                    setError("");
                    setGoogleLoading(true);
                    startGoogleSignIn();
                  }}
                  disabled={busy}
                  className="btn-secondary w-full py-2.5"
                >
                  {googleLoading ? <Spinner /> : <GoogleIcon />}
                  {googleLoading ? "Signing in with Google…" : "Continue with Google"}
                </button>
                <div className="my-5 flex items-center gap-3">
                  <div className="h-px flex-1 bg-zinc-200 dark:bg-zinc-800" />
                  <span className="text-xs text-zinc-400">or</span>
                  <div className="h-px flex-1 bg-zinc-200 dark:bg-zinc-800" />
                </div>
              </>
            )}

            <form onSubmit={handleSubmit} className="space-y-4" noValidate>
              <div>
                <label htmlFor="username" className="label">Username</label>
                <input
                  id="username"
                  type="text"
                  autoComplete="username"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="jane_doe"
                  className="input"
                />
              </div>
              {mode === "register" && (
                <div>
                  <label htmlFor="email" className="label">Work email</label>
                  <input
                    id="email"
                    type="email"
                    autoComplete="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@company.com"
                    className="input"
                  />
                </div>
              )}
              <div>
                <label htmlFor="password" className="label">Password</label>
                <input
                  id="password"
                  type="password"
                  autoComplete={mode === "login" ? "current-password" : "new-password"}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={mode === "register" ? "At least 8 characters" : "••••••••"}
                  className="input"
                />
              </div>
              {mode === "register" && (
                <div>
                  <label htmlFor="confirm" className="label">Confirm password</label>
                  <input
                    id="confirm"
                    type="password"
                    autoComplete="new-password"
                    required
                    value={confirm}
                    onChange={(e) => setConfirm(e.target.value)}
                    className="input"
                  />
                </div>
              )}

              {error && <ErrorBanner message={error} />}

              <button
                type="submit"
                disabled={busy || !username.trim() || !password || (mode === "register" && (!email.trim() || !confirm))}
                className="btn-primary w-full py-2.5"
              >
                {loading && <Spinner />}
                {mode === "login" ? "Log in" : "Create account"}
              </button>
            </form>
          </div>

          <p className="muted mt-6 text-center text-sm">
            Just exploring?{" "}
            <Link href="/chat" className="font-medium text-zinc-900 underline-offset-4 hover:underline dark:text-white">
              Try the AI demo
            </Link>{" "}
            — no account needed.
          </p>
        </div>
      </main>
    </div>
  );
}

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 48 48" aria-hidden="true">
      <path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.7 32.9 29.3 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34.5 6.1 29.5 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.7-.4-3.5z" />
      <path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.6 15.9 18.9 13 24 13c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34.5 6.1 29.5 4 24 4c-7.7 0-14.4 4.3-17.7 10.7z" />
      <path fill="#4CAF50" d="M24 44c5.3 0 10.2-2 13.9-5.4l-6.4-5.4C29.4 34.7 26.8 36 24 36c-5.3 0-9.7-3.1-11.3-7.6l-6.6 5.1C9.5 39.6 16.2 44 24 44z" />
      <path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.3-2.2 4.2-4 5.6l6.4 5.4C41.5 35.7 44 30.3 44 24c0-1.3-.1-2.7-.4-3.5z" />
    </svg>
  );
}

"use client";

import { BarChart3, Layers, LogOut, Menu, MessageSquare, ShieldAlert, Upload, Users, X } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Logo } from "@/components/Logo";
import { ThemeToggle } from "@/components/ThemeToggle";
import { LoadingState } from "@/components/ui";
import { UserContext } from "@/components/UserContext";
import { api } from "@/lib/api-client";
import { clearSession, getStoredUser, getToken, saveUser, UNAUTHORIZED_EVENT } from "@/lib/session";
import type { User } from "@/lib/types";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/dashboard", icon: BarChart3, label: "Overview" },
  { href: "/dashboard/upload", icon: Upload, label: "Data upload" },
  { href: "/dashboard/alerts", icon: ShieldAlert, label: "Risk alerts" },
  { href: "/dashboard/clusters", icon: Layers, label: "Clustering" },
  { href: "/dashboard/chat", icon: MessageSquare, label: "AI assistant" },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<User | null>(null);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    setUser(getStoredUser());

    // Re-validate the session in the background; a 401 fires UNAUTHORIZED_EVENT below.
    api.me().then((u) => {
      setUser(u);
      saveUser(u);
    }).catch(() => {});

    const onUnauthorized = () => router.replace("/login");
    window.addEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
  }, [router]);

  useEffect(() => setMobileOpen(false), [pathname]);

  const logout = () => {
    clearSession();
    router.replace("/");
  };

  if (!user) return <LoadingState label="Loading your workspace…" />;

  const links = user.role === "admin" ? [...NAV, { href: "/dashboard/admin", icon: Users, label: "Users" }] : NAV;

  return (
    <UserContext.Provider value={user}>
      <div className="min-h-screen md:flex">
        {/* Mobile top bar */}
        <div className="sticky top-0 z-30 flex items-center justify-between border-b border-zinc-200 bg-white px-4 py-3 dark:border-zinc-800 dark:bg-zinc-950 md:hidden">
          <Logo href="/dashboard" />
          <button
            type="button"
            onClick={() => setMobileOpen(true)}
            className="rounded-lg border border-zinc-200 p-2 dark:border-zinc-700"
            aria-label="Open navigation"
          >
            <Menu size={18} />
          </button>
        </div>

        {mobileOpen && (
          <div className="fixed inset-0 z-40 bg-black/40 md:hidden" onClick={() => setMobileOpen(false)} aria-hidden="true" />
        )}

        <aside
          className={cn(
            "fixed inset-y-0 left-0 z-50 flex w-64 flex-col justify-between border-r border-zinc-200 bg-white p-4 transition-transform dark:border-zinc-800 dark:bg-zinc-950 md:sticky md:top-0 md:h-screen md:w-60 md:translate-x-0",
            mobileOpen ? "translate-x-0" : "-translate-x-full"
          )}
        >
          <div className="flex flex-col gap-6">
            <div className="flex items-center justify-between px-2 pt-1">
              <Logo href="/dashboard" />
              <button
                type="button"
                onClick={() => setMobileOpen(false)}
                className="rounded-md p-1 text-zinc-500 md:hidden"
                aria-label="Close navigation"
              >
                <X size={18} />
              </button>
            </div>
            <nav className="flex flex-col gap-0.5" aria-label="Dashboard">
              {links.map(({ href, icon: Icon, label }) => {
                const active = pathname === href;
                return (
                  <Link
                    key={href}
                    href={href}
                    aria-current={active ? "page" : undefined}
                    className={cn(
                      "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition",
                      active
                        ? "bg-zinc-100 text-zinc-900 dark:bg-zinc-800 dark:text-white"
                        : "text-zinc-500 hover:bg-zinc-50 hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-900 dark:hover:text-white"
                    )}
                  >
                    <Icon size={17} />
                    {label}
                  </Link>
                );
              })}
            </nav>
          </div>

          <div className="flex flex-col gap-3 border-t border-zinc-200 pt-4 dark:border-zinc-800">
            <div className="flex items-center gap-3 px-2">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-zinc-900 text-xs font-semibold uppercase text-white dark:bg-white dark:text-zinc-900">
                {user.username.slice(0, 1)}
              </div>
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-medium">{user.username}</div>
                <div className="muted truncate text-xs">{user.email}</div>
              </div>
            </div>
            <div className="flex gap-2">
              <button type="button" onClick={logout} className="btn-secondary flex-1 py-1.5 text-xs">
                <LogOut size={13} /> Log out
              </button>
              <ThemeToggle />
            </div>
          </div>
        </aside>

        <main className="mx-auto w-full min-w-0 max-w-6xl flex-1 px-4 py-6 sm:px-6 md:px-10 md:py-8">{children}</main>
      </div>
    </UserContext.Provider>
  );
}

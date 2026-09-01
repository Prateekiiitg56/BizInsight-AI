"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { BarChart2, Upload, ShieldAlert, Layers, MessageSquare, LogOut, User, Menu, X } from "lucide-react";
import { api } from "@/lib/api-client";

interface SidebarLinkProps {
  href: string;
  icon: React.ReactNode;
  label: string;
  active: boolean;
  onClick?: () => void;
}

const SidebarLink: React.FC<SidebarLinkProps> = ({ href, icon, label, active, onClick }) => (
  <Link href={href} onClick={onClick} className={`flex items-center gap-3 px-4 py-2.5 rounded-lg transition-all text-sm font-medium ${active ? "bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-white" : "text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white hover:bg-zinc-50 dark:hover:bg-zinc-800/50"}`}>
    <span className={active ? "text-zinc-900 dark:text-white" : "text-zinc-400 dark:text-zinc-500"}>{icon}</span>
    <span>{label}</span>
  </Link>
);

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [darkMode, setDarkMode] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("bizinsight_token");
    const storedUser = localStorage.getItem("bizinsight_user");

    if (!token) {
      router.push("/");
      return;
    }

    // Load stored user immediately for fast UI render
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (e) {
        console.error("Failed to parse stored user", e);
      }
    }

    // Verify token with backend
    api.me(token)
      .then((userData) => {
        setUser(userData);
        localStorage.setItem("bizinsight_user", JSON.stringify(userData));
      })
      .catch((err) => {
        console.error("Token verification failed:", err);
        localStorage.removeItem("bizinsight_token");
        localStorage.removeItem("bizinsight_user");
        router.push("/");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [router]);

  useEffect(() => {
    if (darkMode) document.documentElement.classList.add("dark");
    else document.documentElement.classList.remove("dark");
  }, [darkMode]);

  const handleLogout = () => { localStorage.removeItem("bizinsight_token"); localStorage.removeItem("bizinsight_user"); router.push("/"); };

  if (loading) {
    return (<div className="min-h-screen flex items-center justify-center"><div className="flex flex-col items-center gap-3"><span className="text-lg font-semibold tracking-tight">BizInsight AI</span><div className="w-8 h-0.5 bg-zinc-900 dark:bg-white rounded-full animate-pulse" /></div></div>);
  }

  const links = [
    { href: "/dashboard", icon: <BarChart2 size={18} />, label: "Dashboard" },
    { href: "/dashboard/upload", icon: <Upload size={18} />, label: "Data Upload" },
    { href: "/dashboard/alerts", icon: <ShieldAlert size={18} />, label: "Trend Alerts" },
    { href: "/dashboard/clusters", icon: <Layers size={18} />, label: "Clustering" },
    { href: "/dashboard/chat", icon: <MessageSquare size={18} />, label: "AI Assistant" },
  ];

  return (
    <div className="min-h-screen flex flex-col md:flex-row">
      {/* Mobile Top Bar */}
      <div className="md:hidden flex items-center justify-between px-6 py-3 border-b border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 sticky top-0 z-30">
        <span className="font-semibold text-base">BizInsight AI</span>
        <button onClick={() => setMobileOpen(!mobileOpen)} className="p-2 rounded-lg border border-zinc-200 dark:border-zinc-700">
          {mobileOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {/* Sidebar */}
      <aside className={`w-full md:w-60 border-r border-zinc-200 dark:border-zinc-800 flex flex-col justify-between p-5 fixed md:sticky top-0 md:h-screen z-20 transition-transform bg-white dark:bg-zinc-900 ${mobileOpen ? "translate-x-0 h-screen" : "-translate-x-full md:translate-x-0"}`}>
        <div className="flex flex-col gap-6">
          <div className="hidden md:flex items-center gap-2 px-2">
            <span className="w-2.5 h-2.5 rounded-full bg-zinc-900 dark:bg-white" />
            <span className="text-base font-semibold tracking-tight">BizInsight AI</span>
          </div>
          <nav className="flex flex-col gap-1">
            {links.map((link) => (<SidebarLink key={link.href} href={link.href} icon={link.icon} label={link.label} active={pathname === link.href} onClick={() => setMobileOpen(false)} />))}
          </nav>
        </div>
        <div className="flex flex-col gap-3 border-t border-zinc-200 dark:border-zinc-800 pt-4">
          <div className="flex items-center gap-3 px-2">
            <div className="w-8 h-8 rounded-lg bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center"><User size={16} className="text-zinc-500" /></div>
            <div className="flex-1 min-w-0">
              <div className="text-xs font-semibold truncate">{user?.name || user?.username || "Prateek Singh"}</div>
              <div className="text-[10px] text-zinc-500 truncate">{user?.email || user?.role || "Google User"}</div>
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={handleLogout} className="flex-1 flex items-center justify-center gap-1.5 text-xs font-medium px-3 py-2 rounded-lg border border-zinc-200 dark:border-zinc-700 text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors">
              <LogOut size={13} /> Log out
            </button>
            <button onClick={() => setDarkMode(!darkMode)} className="text-[10px] px-3 py-2 rounded-lg border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors">Theme</button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 px-6 py-8 md:px-10 md:py-8 max-w-7xl mx-auto w-full overflow-y-auto no-scrollbar">
        {children}
      </main>
    </div>
  );
}

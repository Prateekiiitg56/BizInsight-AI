import { AlertCircle, Loader2 } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export function PageHeader({
  title,
  description,
  actions,
}: {
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
        {description && <p className="muted mt-1 text-sm">{description}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}

export function Spinner({ size = 16, className }: { size?: number; className?: string }) {
  return <Loader2 size={size} className={cn("animate-spin", className)} aria-hidden="true" />;
}

export function LoadingState({ label }: { label: string }) {
  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center gap-3" role="status">
      <Spinner size={24} className="text-zinc-400" />
      <p className="muted text-sm">{label}</p>
    </div>
  );
}

export function ErrorBanner({ message, action }: { message: string; action?: ReactNode }) {
  return (
    <div
      role="alert"
      className="flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-300"
    >
      <AlertCircle size={16} className="mt-0.5 shrink-0" aria-hidden="true" />
      <div className="flex-1">{message}</div>
      {action}
    </div>
  );
}

export function EmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon: ReactNode;
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center gap-5 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-zinc-100 text-zinc-400 dark:bg-zinc-800">
        {icon}
      </div>
      <div>
        <h2 className="text-lg font-semibold tracking-tight">{title}</h2>
        <p className="muted mt-1 max-w-sm text-sm">{description}</p>
      </div>
      {action}
    </div>
  );
}

export function StatCard({
  label,
  value,
  hint,
  valueClassName,
}: {
  label: string;
  value: ReactNode;
  hint?: ReactNode;
  valueClassName?: string;
}) {
  return (
    <div className="card p-5">
      <div className="muted mb-2 text-xs font-medium">{label}</div>
      <div className={cn("text-2xl font-semibold tabular-nums", valueClassName)}>{value}</div>
      {hint && <div className="muted mt-1 text-xs">{hint}</div>}
    </div>
  );
}

export const RISK_STYLES: Record<string, { text: string; badge: string; label: string }> = {
  low: {
    text: "text-emerald-600 dark:text-emerald-400",
    badge: "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400",
    label: "Low",
  },
  medium: {
    text: "text-amber-600 dark:text-amber-400",
    badge: "bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400",
    label: "Medium",
  },
  high: {
    text: "text-red-600 dark:text-red-400",
    badge: "bg-red-50 text-red-700 dark:bg-red-500/10 dark:text-red-400",
    label: "High",
  },
};

export function sentimentColor(score: number): string {
  if (score > 0) return "text-emerald-600 dark:text-emerald-400";
  if (score < 0) return "text-red-600 dark:text-red-400";
  return "text-zinc-500";
}

export function formatScore(score: number): string {
  return `${score > 0 ? "+" : ""}${score.toFixed(2)}`;
}

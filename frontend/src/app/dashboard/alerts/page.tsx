"use client";

import { AlertTriangle, CheckCircle2, RefreshCw, ShieldAlert, Upload } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { EmptyState, ErrorBanner, LoadingState, PageHeader, RISK_STYLES, Spinner } from "@/components/ui";
import { api } from "@/lib/api-client";
import type { AlertStatus } from "@/lib/types";
import { cn } from "@/lib/utils";

const MEDIUM_THRESHOLD = 25;

const GUIDANCE: Record<string, string> = {
  low: "Customer sentiment is healthy. Keep monitoring as new reviews arrive.",
  medium: "Negative feedback is building. Review the top issues below before they escalate.",
  high: "Negative reviews have crossed the alert threshold. Prioritize the top issues and run complaint clustering to find root causes.",
};

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<AlertStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async (initial = false) => {
    if (initial) setLoading(true);
    else setRefreshing(true);
    setError("");
    try {
      setAlerts(await api.getAlerts());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load alerts.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    load(true);
  }, [load]);

  if (loading) return <LoadingState label="Loading alerts…" />;

  const header = (
    <PageHeader
      title="Risk alerts"
      description="Risk is based on the share of negative reviews in your data."
      actions={
        <button type="button" onClick={() => load()} disabled={refreshing} className="btn-secondary">
          {refreshing ? <Spinner size={14} /> : <RefreshCw size={14} />} Re-scan
        </button>
      }
    />
  );

  if (error || !alerts) {
    return (
      <div>
        {header}
        <ErrorBanner message={error || "Could not load alerts."} />
      </div>
    );
  }

  if (alerts.total_reviews === 0) {
    return (
      <div>
        {header}
        <EmptyState
          icon={<ShieldAlert size={26} />}
          title="Nothing to monitor yet"
          description="Upload reviews to calculate your risk level."
          action={
            <Link href="/dashboard/upload" className="btn-primary">
              <Upload size={16} /> Upload reviews
            </Link>
          }
        />
      </div>
    );
  }

  const style = RISK_STYLES[alerts.risk_level] ?? RISK_STYLES.low;
  const RiskIcon = alerts.risk_level === "low" ? CheckCircle2 : AlertTriangle;
  const gaugePct = Math.min(100, alerts.negative_percent);

  return (
    <div>
      {header}

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-2">
          <section className="card p-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="muted text-xs font-medium">Current risk level</div>
                <div className={cn("mt-1 flex items-center gap-2 text-3xl font-semibold", style.text)}>
                  <RiskIcon size={26} /> {style.label}
                </div>
                <p className="muted mt-2 max-w-md text-sm">{GUIDANCE[alerts.risk_level]}</p>
              </div>
              <span className={cn("rounded-full px-3 py-1 text-xs font-medium", style.badge)}>
                {alerts.negative_percent.toFixed(1)}% negative
              </span>
            </div>

            {/* Gauge: 0–100% negative, with medium & high thresholds marked */}
            <div className="mt-8">
              <div className="relative h-2.5 rounded-full bg-zinc-100 dark:bg-zinc-800">
                <div
                  className={cn(
                    "h-full rounded-full",
                    alerts.risk_level === "high" ? "bg-red-500" : alerts.risk_level === "medium" ? "bg-amber-500" : "bg-emerald-500"
                  )}
                  style={{ width: `${gaugePct}%` }}
                />
                {[MEDIUM_THRESHOLD, alerts.threshold].map((t) => (
                  <div key={t} className="absolute -top-1 w-px bg-zinc-400" style={{ left: `${t}%`, height: 18 }} />
                ))}
              </div>
              <div className="muted relative mt-2 h-4 text-[11px]">
                <span className="absolute left-0">0%</span>
                <span className="absolute -translate-x-1/2" style={{ left: `${MEDIUM_THRESHOLD}%` }}>
                  {MEDIUM_THRESHOLD}%
                </span>
                <span className="absolute -translate-x-1/2" style={{ left: `${alerts.threshold}%` }}>
                  {alerts.threshold}%
                </span>
                <span className="absolute right-0">100%</span>
              </div>
            </div>

            <dl className="mt-6 grid grid-cols-3 gap-4 border-t border-zinc-200 pt-5 dark:border-zinc-800">
              <div>
                <dt className="muted text-xs">Negative share</dt>
                <dd className="mt-0.5 text-xl font-semibold tabular-nums">{alerts.negative_percent.toFixed(1)}%</dd>
              </div>
              <div>
                <dt className="muted text-xs">Alert threshold</dt>
                <dd className="mt-0.5 text-xl font-semibold tabular-nums">{alerts.threshold}%</dd>
              </div>
              <div>
                <dt className="muted text-xs">Reviews scanned</dt>
                <dd className="mt-0.5 text-xl font-semibold tabular-nums">{alerts.total_reviews.toLocaleString()}</dd>
              </div>
            </dl>
          </section>

          <section className="card p-5">
            <h2 className="text-sm font-semibold">Top issue keywords</h2>
            <p className="muted mb-4 text-xs">Most frequent terms in negative reviews</p>
            {alerts.top_issues.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {alerts.top_issues.map((w) => (
                  <span
                    key={w}
                    className="rounded-full border border-red-200 bg-red-50 px-3 py-1 text-xs capitalize text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-300"
                  >
                    {w}
                  </span>
                ))}
              </div>
            ) : (
              <p className="muted text-sm">No negative issues found.</p>
            )}
            <Link href="/dashboard/clusters" className="btn-secondary mt-5">
              Find root causes with clustering
            </Link>
          </section>
        </div>

        <section className="card h-fit p-5">
          <h2 className="text-sm font-semibold">How risk is scored</h2>
          <dl className="mt-4 space-y-3 text-sm">
            {[
              ["low", `Below ${MEDIUM_THRESHOLD}%`],
              ["medium", `${MEDIUM_THRESHOLD}% – ${alerts.threshold}%`],
              ["high", `${alerts.threshold}% or more`],
            ].map(([level, range]) => (
              <div key={level} className="flex items-center justify-between">
                <dt className={cn("rounded-full px-2.5 py-0.5 text-xs font-medium", RISK_STYLES[level].badge)}>
                  {RISK_STYLES[level].label}
                </dt>
                <dd className="muted tabular-nums">{range} negative</dd>
              </div>
            ))}
          </dl>
          <p className="muted mt-5 border-t border-zinc-200 pt-4 text-xs leading-relaxed dark:border-zinc-800">
            A review counts as negative when its VADER sentiment score is below zero.
          </p>
        </section>
      </div>
    </div>
  );
}

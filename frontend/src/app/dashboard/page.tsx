"use client";

import { ArrowRight, BarChart3, Download, MessageSquare, RefreshCw, Upload } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { SentimentTrendChart } from "@/components/SentimentTrendChart";
import {
  EmptyState,
  ErrorBanner,
  formatScore,
  LoadingState,
  PageHeader,
  RISK_STYLES,
  sentimentColor,
  Spinner,
  StatCard,
} from "@/components/ui";
import { api } from "@/lib/api-client";
import type { AlertStatus, DashboardSummary } from "@/lib/types";

export default function DashboardOverview() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [alerts, setAlerts] = useState<AlertStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [s, a] = await Promise.all([api.getSummary(), api.getAlerts()]);
      setSummary(s);
      setAlerts(a);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load the dashboard.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleExport = async () => {
    setExporting(true);
    setExportError("");
    try {
      const blob = await api.exportReviews();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `bizinsight-reviews-${new Date().toISOString().slice(0, 10)}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setExportError(err instanceof Error ? err.message : "Export failed.");
    } finally {
      setExporting(false);
    }
  };

  if (loading) return <LoadingState label="Loading dashboard…" />;

  if (error || !summary || !alerts) {
    return (
      <div className="mx-auto max-w-lg pt-16">
        <ErrorBanner
          message={error || "Could not load the dashboard."}
          action={
            <button type="button" onClick={load} className="font-medium underline underline-offset-2">
              Retry
            </button>
          }
        />
      </div>
    );
  }

  if (summary.total_reviews === 0) {
    return (
      <EmptyState
        icon={<BarChart3 size={26} />}
        title="No data yet"
        description="Upload a CSV of customer reviews to see sentiment, trends, risk and keywords here."
        action={
          <Link href="/dashboard/upload" className="btn-primary">
            <Upload size={16} /> Upload your first CSV
          </Link>
        }
      />
    );
  }

  const risk = RISK_STYLES[alerts.risk_level] ?? RISK_STYLES.low;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Overview"
        description={`${summary.total_reviews.toLocaleString()} reviews analyzed`}
        actions={
          <>
            <button type="button" onClick={load} className="btn-secondary" aria-label="Refresh">
              <RefreshCw size={14} />
            </button>
            <button type="button" onClick={handleExport} disabled={exporting} className="btn-secondary">
              {exporting ? <Spinner size={14} /> : <Download size={14} />} Export CSV
            </button>
            <Link href="/dashboard/upload" className="btn-primary">
              <Upload size={14} /> Import CSV
            </Link>
          </>
        }
      />

      {exportError && <ErrorBanner message={exportError} />}

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCard
          label="Avg. sentiment"
          value={formatScore(summary.avg_sentiment)}
          valueClassName={sentimentColor(summary.avg_sentiment)}
          hint="Scale −1 (negative) to +1 (positive)"
        />
        <StatCard
          label="Reviews analyzed"
          value={summary.total_reviews.toLocaleString()}
          hint={`${summary.positive_count.toLocaleString()} positive · ${summary.negative_count.toLocaleString()} negative`}
        />
        <StatCard
          label="Risk level"
          value={risk.label}
          valueClassName={risk.text}
          hint={`${alerts.negative_percent.toFixed(1)}% negative reviews`}
        />
        <StatCard
          label="Negative spike"
          value={alerts.risk_level === "high" ? "Detected" : "None"}
          valueClassName={alerts.risk_level === "high" ? risk.text : undefined}
          hint={`Alert at ≥ ${alerts.threshold}% negative`}
        />
      </div>

      <div className="grid gap-3 lg:grid-cols-3">
        <section className="card p-5 lg:col-span-2">
          <h2 className="text-sm font-semibold">Sentiment trend</h2>
          <p className="muted mb-4 text-xs">Average sentiment per day</p>
          <SentimentTrendChart data={summary.trend} />
        </section>

        <section className="card p-5">
          <h2 className="text-sm font-semibold">Sentiment split</h2>
          <p className="muted mb-4 text-xs">Share of all reviews</p>
          <SentimentSplit summary={summary} />
        </section>
      </div>

      <div className="grid gap-3 lg:grid-cols-3">
        <section className="card p-5">
          <h2 className="text-sm font-semibold">Top keywords</h2>
          <p className="muted mb-4 text-xs">Most frequent terms across all reviews</p>
          {summary.top_keywords.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {summary.top_keywords.map((kw) => (
                <span key={kw.keyword} className="rounded-full bg-zinc-100 px-3 py-1 text-xs dark:bg-zinc-800">
                  {kw.keyword} <span className="muted">· {kw.frequency}</span>
                </span>
              ))}
            </div>
          ) : (
            <p className="muted text-sm">No keywords extracted.</p>
          )}
        </section>

        <section className="card p-5">
          <h2 className="text-sm font-semibold">Top negative issues</h2>
          <p className="muted mb-4 text-xs">Most frequent terms in negative reviews</p>
          {alerts.top_issues.length > 0 ? (
            <ol className="space-y-2">
              {alerts.top_issues.map((issue, i) => (
                <li key={issue} className="flex items-center gap-3 text-sm">
                  <span className="muted w-4 text-xs tabular-nums">{i + 1}</span>
                  <span className="capitalize">{issue}</span>
                </li>
              ))}
            </ol>
          ) : (
            <p className="muted text-sm">No negative issues found.</p>
          )}
        </section>

        <section className="card flex flex-col justify-between p-5">
          <div>
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-zinc-100 dark:bg-zinc-800">
              <MessageSquare size={17} />
            </div>
            <h2 className="mt-4 text-sm font-semibold">Ask your data</h2>
            <p className="muted mt-1 text-sm">
              Get AI summaries of what customers are saying, grounded only in your reviews.
            </p>
          </div>
          <Link href="/dashboard/chat" className="btn-secondary mt-4 self-start">
            Open AI assistant <ArrowRight size={14} />
          </Link>
        </section>
      </div>
    </div>
  );
}

function SentimentSplit({ summary }: { summary: DashboardSummary }) {
  const segments = [
    { label: "Positive", pct: summary.positive_percent, count: summary.positive_count, color: "bg-emerald-500" },
    { label: "Neutral", pct: summary.neutral_percent, count: summary.neutral_count, color: "bg-zinc-300 dark:bg-zinc-600" },
    { label: "Negative", pct: summary.negative_percent, count: summary.negative_count, color: "bg-red-500" },
  ];
  return (
    <div>
      <div className="flex h-3 gap-0.5 overflow-hidden rounded-full" role="img" aria-label="Sentiment distribution">
        {segments
          .filter((s) => s.pct > 0)
          .map((s) => (
            <div key={s.label} className={s.color} style={{ width: `${s.pct}%` }} title={`${s.label}: ${s.pct.toFixed(1)}%`} />
          ))}
      </div>
      <dl className="mt-5 space-y-3">
        {segments.map((s) => (
          <div key={s.label} className="flex items-center justify-between text-sm">
            <dt className="flex items-center gap-2">
              <span className={`h-2.5 w-2.5 rounded-sm ${s.color}`} aria-hidden="true" />
              {s.label}
            </dt>
            <dd className="tabular-nums">
              {s.pct.toFixed(1)}% <span className="muted text-xs">({s.count.toLocaleString()})</span>
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

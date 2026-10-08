"use client";

import { ChevronDown, Layers } from "lucide-react";
import { useEffect, useState } from "react";
import { ErrorBanner, PageHeader, Spinner } from "@/components/ui";
import { api } from "@/lib/api-client";
import type { ClusterItem, ClusteringJobStatus, ClusteringMode, ClusteringResult } from "@/lib/types";
import { cn } from "@/lib/utils";

const POLL_MS = 2000;

export default function ClustersPage() {
  const [mode, setMode] = useState<ClusteringMode>("negative");
  const [job, setJob] = useState<ClusteringJobStatus | null>(null);
  const [result, setResult] = useState<ClusteringResult | null>(null);
  const [resultMode, setResultMode] = useState<ClusteringMode>("negative");
  const [error, setError] = useState("");

  const running = job?.status === "pending" || job?.status === "running";

  useEffect(() => {
    if (!job || !running) return;
    let cancelled = false;
    const timer = setTimeout(async () => {
      try {
        const status = await api.getClusteringStatus(job.job_id);
        if (cancelled) return;
        if (status.status === "completed") {
          const res = await api.getClusteringResults(job.job_id);
          if (cancelled) return;
          setResult(res);
        } else if (status.status === "failed") {
          setError(status.message || "Clustering failed.");
        }
        setJob(status);
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Lost track of the clustering job.");
        setJob(null);
      }
    }, POLL_MS);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [job, running]);

  const start = async () => {
    setError("");
    setResult(null);
    setResultMode(mode);
    try {
      setJob(await api.startClustering(mode));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start clustering.");
    }
  };

  const maxCount = Math.max(1, ...(result?.clusters.map((c) => c.count) ?? []));

  return (
    <div>
      <PageHeader
        title="Topic clustering"
        description="Group reviews into themes with BERTopic (sentence embeddings → UMAP → HDBSCAN)."
      />

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-4">
          <section className="card space-y-4 p-5">
            <div>
              <h2 className="text-sm font-semibold">Run clustering</h2>
              <p className="muted mt-1 text-xs leading-relaxed">
                Needs at least 10 reviews of the chosen sentiment. Large datasets can take a minute or two.
              </p>
            </div>
            <fieldset>
              <legend className="label">Reviews to cluster</legend>
              <div className="grid grid-cols-2 gap-1 rounded-lg bg-zinc-100 p-1 dark:bg-zinc-800">
                {(["negative", "positive"] as const).map((m) => (
                  <button
                    key={m}
                    type="button"
                    onClick={() => setMode(m)}
                    disabled={running}
                    aria-pressed={mode === m}
                    className={cn(
                      "rounded-md py-1.5 text-xs font-medium capitalize transition",
                      mode === m ? "bg-white shadow-sm dark:bg-zinc-700" : "muted"
                    )}
                  >
                    {m === "negative" ? "Complaints" : "Praise"}
                  </button>
                ))}
              </div>
            </fieldset>
            <button type="button" onClick={start} disabled={running} className="btn-primary w-full py-2.5">
              {running ? <Spinner /> : <Layers size={15} />}
              {running ? "Clustering…" : mode === "negative" ? "Find complaint themes" : "Find praise themes"}
            </button>
          </section>

          {job && (
            <section className="card space-y-2 p-4 text-xs">
              <div className="flex items-center justify-between">
                <span className="muted">Status</span>
                <span
                  className={cn(
                    "rounded-full px-2 py-0.5 font-medium capitalize",
                    job.status === "completed"
                      ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400"
                      : job.status === "failed"
                        ? "bg-red-50 text-red-700 dark:bg-red-500/10 dark:text-red-400"
                        : "bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400"
                  )}
                >
                  {job.status}
                </span>
              </div>
              {job.message && <p className="muted">{job.message}</p>}
            </section>
          )}

          {error && <ErrorBanner message={error} />}
        </div>

        <div className="lg:col-span-2">
          {running ? (
            <div className="card flex min-h-[320px] flex-col items-center justify-center gap-3 p-8 text-center">
              <Spinner size={26} className="text-zinc-400" />
              <div>
                <h3 className="text-sm font-medium">Running the clustering pipeline</h3>
                <p className="muted mt-1 text-xs">The first run also downloads the embedding model.</p>
              </div>
            </div>
          ) : result ? (
            <div className="space-y-3">
              <section className="card grid grid-cols-3 gap-4 p-5">
                <div>
                  <div className="muted text-xs">Themes found</div>
                  <div className="text-xl font-semibold tabular-nums">{result.n_clusters}</div>
                </div>
                <div>
                  <div className="muted text-xs">Reviews clustered</div>
                  <div className="text-xl font-semibold tabular-nums">{result.total_reviews.toLocaleString()}</div>
                </div>
                <div>
                  <div className="muted text-xs" title="Reviews that didn't fit any theme">Unclustered</div>
                  <div className="text-xl font-semibold tabular-nums">{result.noise_percentage}%</div>
                </div>
              </section>
              {result.clusters.length > 0 ? (
                result.clusters.map((c) => (
                  <ClusterRow key={c.id} cluster={c} maxCount={maxCount} positive={resultMode === "positive"} />
                ))
              ) : (
                <div className="card muted p-10 text-center text-sm">
                  No distinct themes found. Try again with more reviews.
                </div>
              )}
            </div>
          ) : (
            <div className="flex min-h-[320px] flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-zinc-200 p-8 text-center dark:border-zinc-800">
              <Layers size={26} className="text-zinc-400" />
              <h3 className="text-sm font-medium">No results yet</h3>
              <p className="muted max-w-xs text-xs">Run clustering to see the main themes in your reviews.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ClusterRow({ cluster, maxCount, positive }: { cluster: ClusterItem; maxCount: number; positive: boolean }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="card">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        className="flex w-full items-center gap-4 p-4 text-left"
      >
        <div className="min-w-0 flex-1">
          <h3 className="truncate text-sm font-medium">{cluster.name}</h3>
          <div className="mt-2 h-1.5 rounded-full bg-zinc-100 dark:bg-zinc-800">
            <div
              className={cn("h-full rounded-full", positive ? "bg-emerald-500" : "bg-red-500")}
              style={{ width: `${(cluster.count / maxCount) * 100}%` }}
            />
          </div>
        </div>
        <div className="shrink-0 text-right">
          <div className="text-sm font-semibold tabular-nums">{cluster.percentage}%</div>
          <div className="muted text-xs tabular-nums">{cluster.count.toLocaleString()} reviews</div>
        </div>
        <ChevronDown size={16} className={cn("shrink-0 text-zinc-400 transition", open && "rotate-180")} />
      </button>
      {open && cluster.example_reviews.length > 0 && (
        <ul className="space-y-2 border-t border-zinc-100 p-4 dark:border-zinc-800">
          {cluster.example_reviews.map((q, i) => (
            <li key={i} className="rounded-lg bg-zinc-50 px-3 py-2 text-xs italic leading-relaxed dark:bg-zinc-800/60">
              &ldquo;{q}&rdquo;
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

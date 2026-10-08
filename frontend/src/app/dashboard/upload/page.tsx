"use client";

import { AlertTriangle, CheckCircle2, ChevronLeft, ChevronRight, FileText, Trash2, Upload, X } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { ErrorBanner, formatScore, PageHeader, sentimentColor, Spinner } from "@/components/ui";
import { api } from "@/lib/api-client";
import type { ReviewItem, UploadSummary } from "@/lib/types";
import { cn } from "@/lib/utils";

const PAGE_SIZE = 10;
const MAX_MB = 10;

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<UploadSummary | null>(null);
  const [error, setError] = useState("");

  const [reviews, setReviews] = useState<ReviewItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loadingReviews, setLoadingReviews] = useState(true);
  const [reviewsError, setReviewsError] = useState("");
  const [clearing, setClearing] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const fetchReviews = useCallback(async (p: number) => {
    setLoadingReviews(true);
    setReviewsError("");
    try {
      const res = await api.getReviews(p, PAGE_SIZE);
      setReviews(res.reviews);
      setTotal(res.total);
    } catch (err) {
      setReviewsError(err instanceof Error ? err.message : "Could not load reviews.");
    } finally {
      setLoadingReviews(false);
    }
  }, []);

  useEffect(() => {
    fetchReviews(page);
  }, [page, fetchReviews]);

  const selectFile = (f: File | undefined) => {
    setResult(null);
    setError("");
    if (!f) return;
    if (!f.name.toLowerCase().endsWith(".csv")) return setError("Please choose a .csv file.");
    if (f.size > MAX_MB * 1024 * 1024) return setError(`File is too large. The limit is ${MAX_MB} MB.`);
    setFile(f);
  };

  const clearFile = () => {
    setFile(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError("");
    try {
      setResult(await api.uploadReviews(file));
      clearFile();
      if (page === 1) fetchReviews(1);
      else setPage(1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setUploading(false);
    }
  };

  const handleClear = async () => {
    if (!window.confirm(`Delete all ${total.toLocaleString()} reviews? This cannot be undone.`)) return;
    setClearing(true);
    try {
      await api.clearReviews();
      setReviews([]);
      setTotal(0);
      setPage(1);
      setResult(null);
    } catch (err) {
      setReviewsError(err instanceof Error ? err.message : "Could not clear reviews.");
    } finally {
      setClearing(false);
    }
  };

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div>
      <PageHeader
        title="Data upload"
        description="Upload customer reviews as a CSV file with a column named “review”."
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-4">
          <section className="card p-5">
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setDragging(true);
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={(e) => {
                e.preventDefault();
                setDragging(false);
                selectFile(e.dataTransfer.files?.[0]);
              }}
              className={cn(
                "flex flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-10 text-center transition",
                dragging
                  ? "border-zinc-900 bg-zinc-50 dark:border-white dark:bg-zinc-800/50"
                  : "border-zinc-200 dark:border-zinc-700"
              )}
            >
              <input
                ref={inputRef}
                id="csv-input"
                type="file"
                accept=".csv,text/csv"
                className="sr-only"
                onChange={(e) => selectFile(e.target.files?.[0])}
              />
              {file ? (
                <div className="flex items-center gap-3 rounded-lg bg-zinc-100 px-4 py-3 text-left dark:bg-zinc-800">
                  <FileText size={20} className="shrink-0 text-zinc-500" />
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">{file.name}</p>
                    <p className="muted text-xs">{(file.size / 1024).toFixed(1)} KB</p>
                  </div>
                  <button
                    type="button"
                    onClick={clearFile}
                    disabled={uploading}
                    className="ml-2 rounded p-1 text-zinc-400 hover:text-zinc-900 dark:hover:text-white"
                    aria-label="Remove file"
                  >
                    <X size={16} />
                  </button>
                </div>
              ) : (
                <>
                  <Upload size={22} className="mb-3 text-zinc-400" />
                  <p className="text-sm font-medium">
                    Drag & drop a CSV, or{" "}
                    <label htmlFor="csv-input" className="cursor-pointer underline underline-offset-4">
                      browse
                    </label>
                  </p>
                  <p className="muted mt-1 text-xs">CSV only · up to {MAX_MB} MB</p>
                </>
              )}
            </div>

            {error && (
              <div className="mt-4">
                <ErrorBanner message={error} />
              </div>
            )}

            <button type="button" onClick={handleUpload} disabled={!file || uploading} className="btn-primary mt-4 w-full py-2.5">
              {uploading ? <Spinner /> : <Upload size={16} />}
              {uploading ? "Analyzing reviews…" : "Upload & analyze"}
            </button>
          </section>

          {result && (
            <section className="card border-emerald-200 p-5 dark:border-emerald-500/30">
              <div className="mb-4 flex items-center gap-2 text-emerald-700 dark:text-emerald-400">
                <CheckCircle2 size={16} />
                <h2 className="text-sm font-semibold">
                  {result.total_processed.toLocaleString()} reviews analyzed
                </h2>
              </div>
              <dl className="grid grid-cols-4 gap-3 text-center">
                {[
                  ["Positive", result.positive, "text-emerald-600 dark:text-emerald-400"],
                  ["Neutral", result.neutral, ""],
                  ["Negative", result.negative, "text-red-600 dark:text-red-400"],
                  ["Negative %", `${result.negative_percent}%`, result.alert_triggered ? "text-red-600 dark:text-red-400" : ""],
                ].map(([label, value, color]) => (
                  <div key={label as string}>
                    <dt className="muted text-xs">{label}</dt>
                    <dd className={cn("mt-0.5 text-lg font-semibold tabular-nums", color as string)}>{value}</dd>
                  </div>
                ))}
              </dl>
              {result.alert_triggered && (
                <p className="mt-4 flex items-center gap-2 rounded-lg bg-red-50 p-3 text-xs text-red-700 dark:bg-red-500/10 dark:text-red-300">
                  <AlertTriangle size={14} className="shrink-0" />
                  High risk: negative reviews in this file exceed the alert threshold.
                </p>
              )}
              <Link href="/dashboard" className="btn-primary mt-4 w-full">
                View dashboard
              </Link>
            </section>
          )}

          <section className="card p-5 text-sm">
            <h2 className="font-semibold">CSV format</h2>
            <p className="muted mt-1 text-xs">One review per row. Other columns are ignored.</p>
            <pre className="mt-3 overflow-x-auto rounded-lg bg-zinc-100 p-3 text-xs dark:bg-zinc-800">
{`review
"Delivery was two days late."
"Great quality, would buy again!"`}
            </pre>
          </section>
        </div>

        <section className="card flex flex-col p-5">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold">Your reviews</h2>
            <span className="muted text-xs">{total.toLocaleString()} total</span>
          </div>

          {reviewsError && <ErrorBanner message={reviewsError} />}

          {loadingReviews ? (
            <div className="flex h-64 items-center justify-center">
              <Spinner size={20} className="text-zinc-400" />
            </div>
          ) : reviews.length > 0 ? (
            <ul className="flex-1 divide-y divide-zinc-100 dark:divide-zinc-800">
              {reviews.map((r, i) => (
                <li key={`${page}-${i}`} className="py-3">
                  <p className="line-clamp-2 text-sm">{r.review}</p>
                  <div className="mt-1 flex justify-between text-xs">
                    <span className={cn("font-medium tabular-nums", sentimentColor(r.sentiment))}>
                      {formatScore(r.sentiment)}
                    </span>
                    <span className="muted">{r.date.split(/[ T]/)[0]}</span>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            !reviewsError && (
              <div className="muted flex h-64 flex-col items-center justify-center gap-2 text-sm">
                <FileText size={22} />
                No reviews yet. Upload a CSV to get started.
              </div>
            )
          )}

          {total > 0 && (
            <div className="mt-3 flex items-center justify-between border-t border-zinc-100 pt-3 dark:border-zinc-800">
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setPage((p) => p - 1)}
                  disabled={page === 1 || loadingReviews}
                  className="btn-secondary p-1.5"
                  aria-label="Previous page"
                >
                  <ChevronLeft size={14} />
                </button>
                <span className="muted text-xs tabular-nums">
                  Page {page} of {totalPages}
                </span>
                <button
                  type="button"
                  onClick={() => setPage((p) => p + 1)}
                  disabled={page >= totalPages || loadingReviews}
                  className="btn-secondary p-1.5"
                  aria-label="Next page"
                >
                  <ChevronRight size={14} />
                </button>
              </div>
              <button type="button" onClick={handleClear} disabled={clearing} className="btn-danger px-3 py-1.5 text-xs">
                {clearing ? <Spinner size={13} /> : <Trash2 size={13} />} Delete all
              </button>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TrendPoint } from "@/lib/types";

const formatDate = (d: string) =>
  new Date(`${d}T00:00:00`).toLocaleDateString(undefined, { month: "short", day: "numeric" });

export function SentimentTrendChart({ data }: { data: TrendPoint[] }) {
  if (data.length === 0) {
    return <p className="muted flex h-56 items-center justify-center text-sm">No trend data yet.</p>;
  }

  return (
    <div className="h-56 w-full text-zinc-400" role="img" aria-label="Average sentiment per day">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: -12 }}>
          <CartesianGrid vertical={false} stroke="currentColor" strokeOpacity={0.15} />
          <XAxis
            dataKey="date"
            tickFormatter={formatDate}
            tick={{ fontSize: 11, fill: "currentColor" }}
            tickLine={false}
            axisLine={false}
            minTickGap={24}
          />
          <YAxis
            domain={[-1, 1]}
            ticks={[-1, -0.5, 0, 0.5, 1]}
            tick={{ fontSize: 11, fill: "currentColor" }}
            tickLine={false}
            axisLine={false}
          />
          <ReferenceLine y={0} stroke="currentColor" strokeOpacity={0.4} />
          <Tooltip
            cursor={{ stroke: "currentColor", strokeOpacity: 0.3 }}
            content={({ active, payload }) => {
              if (!active || !payload?.length) return null;
              const point = payload[0].payload as TrendPoint;
              return (
                <div className="rounded-lg border border-zinc-200 bg-white px-3 py-2 text-xs shadow-md dark:border-zinc-700 dark:bg-zinc-900">
                  <div className="muted">{formatDate(point.date)}</div>
                  <div className="mt-0.5 font-semibold text-zinc-900 dark:text-zinc-100">
                    Avg. sentiment {point.avg_sentiment > 0 ? "+" : ""}
                    {point.avg_sentiment.toFixed(2)}
                  </div>
                </div>
              );
            }}
          />
          <Line
            type="monotone"
            dataKey="avg_sentiment"
            stroke="#10b981"
            strokeWidth={2}
            dot={data.length === 1 ? { r: 4, fill: "#10b981", strokeWidth: 0 } : false}
            activeDot={{ r: 5, strokeWidth: 0, fill: "#10b981" }}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card } from "@/components/ui/Card";
import { formatDateTime, formatCurrency } from "@/lib/format";
import type { SeriesPoint } from "@/lib/clientAnalytics";

export function PriceHistoryChart({ series }: { series: SeriesPoint[] }) {
  return (
    <Card className="glow-blue">
      <h3 className="mb-4 text-sm font-bold uppercase tracking-wider text-foreground">Price History</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={series} margin={{ top: 4, right: 12, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="priceLineGradient" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#9b85c4" />
              <stop offset="55%" stopColor="#7fc8d9" />
              <stop offset="100%" stopColor="#5fd0ac" />
            </linearGradient>
            <filter id="neonGlow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur in="SourceGraphic" stdDeviation="1.5" result="blur1" />
              <feMerge>
                <feMergeNode in="blur1" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <filter id="neonGlowSoft" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur in="SourceGraphic" stdDeviation="0.8" result="blur1" />
              <feMerge>
                <feMergeNode in="blur1" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          <CartesianGrid strokeDasharray="2 6" stroke="var(--border)" vertical={false} />
          <XAxis
            dataKey="timestamp"
            tickFormatter={(v) => formatDateTime(v)}
            stroke="var(--muted)"
            fontSize={11}
            fontFamily="var(--font-mono)"
            minTickGap={40}
          />
          <YAxis
            stroke="var(--muted)"
            fontSize={11}
            fontFamily="var(--font-mono)"
            tickFormatter={(v) => `$${v}`}
            domain={["auto", "auto"]}
            width={56}
          />
          <Tooltip
            contentStyle={{
              background: "rgba(12,13,19,0.92)",
              border: "1px solid rgba(106,227,255,0.3)",
              borderRadius: 12,
              fontSize: 12,
              fontFamily: "var(--font-mono)",
              boxShadow: "0 0 16px -6px rgba(106,227,255,0.35)",
            }}
            labelFormatter={(v) => formatDateTime(v as string)}
            formatter={(value, name) => [formatCurrency(value as number), name as string]}
          />
          <Legend wrapperStyle={{ fontSize: 12, fontFamily: "var(--font-mono)" }} />
          <Line
            type="monotone"
            dataKey="ewma"
            name="EWMA"
            stroke="#d9b06b"
            strokeWidth={1.25}
            dot={false}
            strokeDasharray="2 3"
            filter="url(#neonGlowSoft)"
          />
          <Line
            type="monotone"
            dataKey="sma"
            name="SMA (5)"
            stroke="#5fd0ac"
            strokeWidth={1.25}
            dot={false}
            strokeDasharray="4 3"
            filter="url(#neonGlowSoft)"
          />
          <Line
            type="monotone"
            dataKey="price"
            name="Price"
            stroke="url(#priceLineGradient)"
            strokeWidth={2}
            dot={false}
            filter="url(#neonGlow)"
          />
        </LineChart>
      </ResponsiveContainer>
    </Card>
  );
}

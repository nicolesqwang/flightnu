"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Card } from "@/components/ui/Card";

export function PriceHistogram({ buckets }: { buckets: { bucket: string; count: number }[] }) {
  return (
    <Card className="glow-green">
      <h3 className="mb-4 text-sm font-bold uppercase tracking-wider text-foreground">
        Histogram of Historical Prices
      </h3>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={buckets} margin={{ top: 4, right: 12, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="histogramFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#5fd0ac" />
              <stop offset="100%" stopColor="#7fc8d9" stopOpacity={0.4} />
            </linearGradient>
            <filter id="barGlow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur in="SourceGraphic" stdDeviation="1.2" result="blur1" />
              <feMerge>
                <feMergeNode in="blur1" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          <CartesianGrid strokeDasharray="2 6" stroke="var(--border)" vertical={false} />
          <XAxis dataKey="bucket" stroke="var(--muted)" fontSize={11} fontFamily="var(--font-mono)" />
          <YAxis stroke="var(--muted)" fontSize={11} fontFamily="var(--font-mono)" allowDecimals={false} width={32} />
          <Tooltip
            contentStyle={{
              background: "rgba(12,13,19,0.92)",
              border: "1px solid rgba(44,255,184,0.3)",
              borderRadius: 12,
              fontSize: 12,
              fontFamily: "var(--font-mono)",
              boxShadow: "0 0 16px -6px rgba(44,255,184,0.35)",
            }}
            formatter={(value) => [value as number, "Observations"]}
          />
          <Bar dataKey="count" fill="url(#histogramFill)" radius={[6, 6, 0, 0]} filter="url(#barGlow)" />
        </BarChart>
      </ResponsiveContainer>
    </Card>
  );
}

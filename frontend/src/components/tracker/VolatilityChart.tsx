"use client";

import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis, ReferenceLine } from "recharts";
import { Card } from "@/components/ui/Card";
import { formatDateTime, formatCurrency } from "@/lib/format";
import type { SeriesPoint } from "@/lib/clientAnalytics";

export function VolatilityChart({ series }: { series: SeriesPoint[] }) {
  return (
    <Card className="glow-purple">
      <h3 className="mb-4 text-sm font-bold uppercase tracking-wider text-foreground">
        Price Volatility (Deviation from Mean)
      </h3>
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={series} margin={{ top: 4, right: 12, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="volatilityFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#d97fa3" stopOpacity={0.35} />
              <stop offset="100%" stopColor="#9b85c4" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="volatilityStroke" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#9b85c4" />
              <stop offset="100%" stopColor="#d97fa3" />
            </linearGradient>
            <filter id="volatilityGlow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur in="SourceGraphic" stdDeviation="1.5" result="blur1" />
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
            width={56}
          />
          <ReferenceLine y={0} stroke="rgba(255,255,255,0.25)" />
          <Tooltip
            contentStyle={{
              background: "rgba(12,13,19,0.92)",
              border: "1px solid rgba(180,109,255,0.3)",
              borderRadius: 12,
              fontSize: 12,
              fontFamily: "var(--font-mono)",
              boxShadow: "0 0 16px -6px rgba(180,109,255,0.35)",
            }}
            labelFormatter={(v) => formatDateTime(v as string)}
            formatter={(value) => [formatCurrency(value as number, { showSign: true }), "Deviation"]}
          />
          <Area
            type="monotone"
            dataKey="deviation"
            stroke="url(#volatilityStroke)"
            fill="url(#volatilityFill)"
            strokeWidth={1.5}
            filter="url(#volatilityGlow)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </Card>
  );
}

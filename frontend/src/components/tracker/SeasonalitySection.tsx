import { Card } from "@/components/ui/Card";
import { formatHour } from "@/lib/format";
import type { Prediction } from "@/lib/types";

export function SeasonalitySection({ prediction }: { prediction: Prediction }) {
  const rows = [
    {
      label: "Cheapest Day of Week",
      value: prediction.cheapest_day_of_week ?? "—",
      accent: "text-accent-green neon-text-green",
      glow: "rgba(44,255,184,0.4)",
    },
    {
      label: "Most Expensive Day of Week",
      value: prediction.most_expensive_day_of_week ?? "—",
      accent: "text-accent-red neon-text-red",
      glow: "rgba(255,93,143,0.4)",
    },
    {
      label: "Cheapest Hour of Day",
      value: formatHour(prediction.cheapest_hour_of_day),
      accent: "text-accent-green neon-text-green",
      glow: "rgba(44,255,184,0.4)",
    },
    {
      label: "Most Expensive Hour of Day",
      value: formatHour(prediction.most_expensive_hour_of_day),
      accent: "text-accent-red neon-text-red",
      glow: "rgba(255,93,143,0.4)",
    },
  ];

  return (
    <Card className="glow-purple">
      <h3 className="mb-4 text-sm font-bold uppercase tracking-wider text-foreground">Seasonality</h3>
      <div className="grid grid-cols-2 gap-4">
        {rows.map((row) => (
          <div
            key={row.label}
            className="rounded-xl border border-border bg-surface-2 p-4"
            style={{ boxShadow: `0 0 24px -10px ${row.glow}` }}
          >
            <p className="text-xs uppercase tracking-wider text-muted">{row.label}</p>
            <p className={`font-numeric mt-1 text-lg font-bold ${row.accent}`}>{row.value}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}

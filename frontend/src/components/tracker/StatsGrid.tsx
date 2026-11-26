import { clsx } from "clsx";
import { Card, CardLabel, CardValue } from "@/components/ui/Card";
import { formatCurrency, formatPercent } from "@/lib/format";
import type { Prediction } from "@/lib/types";

export function StatsGrid({ prediction }: { prediction: Prediction }) {
  const cheaperThan = prediction.percentile === null ? null : 100 - prediction.percentile;
  const items = [
    { label: "Current Price", value: formatCurrency(prediction.current_price), glow: "glow-blue" },
    { label: "Average Seen", value: formatCurrency(prediction.historical_average), glow: "glow-purple" },
    {
      label: "Lowest Seen",
      value: formatCurrency(prediction.historical_low),
      accent: "text-accent-green neon-text-green",
      glow: "glow-green",
    },
    {
      label: "Highest Seen",
      value: formatCurrency(prediction.historical_high),
      accent: "text-accent-red neon-text-red",
      glow: "glow-red",
    },
    {
      label: "Cheaper Than",
      value: cheaperThan === null ? "—" : `${cheaperThan.toFixed(0)}% seen`,
      accent: "text-accent-green neon-text-green",
      glow: "glow-green",
    },
    {
      label: "Forecast Confidence",
      value: prediction.has_forecast === false ? "Collecting" : formatPercent(prediction.confidence_score),
      glow: "glow-yellow",
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
      {items.map((item) => (
        <Card key={item.label} className={clsx(item.glow)}>
          <CardLabel>{item.label}</CardLabel>
          <CardValue className={item.accent}>{item.value}</CardValue>
        </Card>
      ))}
    </div>
  );
}

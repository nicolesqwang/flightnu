import { clsx } from "clsx";
import { Card, CardLabel, CardValue } from "@/components/ui/Card";
import { formatCurrency, formatPercent } from "@/lib/format";
import type { Prediction } from "@/lib/types";

export function StatsGrid({ prediction }: { prediction: Prediction }) {
  const items = [
    { label: "Current Price", value: formatCurrency(prediction.current_price), glow: "glow-blue" },
    { label: "Historical Average", value: formatCurrency(prediction.historical_average), glow: "glow-purple" },
    {
      label: "Historical Low",
      value: formatCurrency(prediction.historical_low),
      accent: "text-accent-green neon-text-green",
      glow: "glow-green",
    },
    {
      label: "Historical High",
      value: formatCurrency(prediction.historical_high),
      accent: "text-accent-red neon-text-red",
      glow: "glow-red",
    },
    {
      label: "Potential Savings",
      value: formatCurrency(Math.max(0, prediction.historical_average - prediction.current_price)),
      accent: "text-accent-green neon-text-green",
      glow: "glow-green",
    },
    { label: "Prediction Confidence", value: formatPercent(prediction.confidence_score), glow: "glow-yellow" },
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

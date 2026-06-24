import { Card } from "@/components/ui/Card";
import { formatCurrency } from "@/lib/format";
import type { Prediction } from "@/lib/types";

export function AnalyticsSection({ prediction }: { prediction: Prediction }) {
  const volatilityScore = prediction.historical_average
    ? (prediction.std_dev / prediction.historical_average) * 100
    : 0;

  const rows = [
    { label: "Lowest Observed Price", value: formatCurrency(prediction.historical_low) },
    { label: "Highest Observed Price", value: formatCurrency(prediction.historical_high) },
    { label: "Average Price", value: formatCurrency(prediction.historical_average) },
    { label: "Standard Deviation", value: formatCurrency(prediction.std_dev) },
    { label: "Volatility Score", value: `${volatilityScore.toFixed(1)}%` },
    { label: "Z-Score (current price)", value: prediction.z_score.toFixed(2) },
  ];

  return (
    <Card className="glow-blue">
      <h3 className="mb-4 text-sm font-bold uppercase tracking-wider text-foreground">Analytics</h3>
      <dl className="grid grid-cols-2 gap-y-4 sm:grid-cols-3">
        {rows.map((row) => (
          <div key={row.label}>
            <dt className="text-xs uppercase tracking-wider text-muted">{row.label}</dt>
            <dd className="font-numeric mt-1 text-base font-bold text-foreground">{row.value}</dd>
          </div>
        ))}
      </dl>
    </Card>
  );
}

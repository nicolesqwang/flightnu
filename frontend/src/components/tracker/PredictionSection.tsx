import { Card } from "@/components/ui/Card";
import { formatCurrency, formatPercent } from "@/lib/format";
import type { Prediction } from "@/lib/types";

export function PredictionSection({ prediction }: { prediction: Prediction }) {
  return (
    <Card className="glow-yellow">
      <h3 className="mb-4 text-sm font-bold uppercase tracking-wider text-foreground">Prediction</h3>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Stat label="Prob. Increase (24h)" value={formatPercent(prediction.prob_increase_24h * 100)} />
        <Stat label="Prob. Increase (48h)" value={formatPercent(prediction.prob_increase_48h * 100)} />
        <Stat
          label="Expected Increase"
          value={formatCurrency(prediction.expected_increase, { showSign: true })}
          accent="text-accent-red neon-text-red"
        />
        <Stat
          label="Expected Decrease"
          value={`-${formatCurrency(prediction.expected_decrease)}`}
          accent="text-accent-green neon-text-green"
        />
      </div>

      <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div
          className="rounded-xl border border-border bg-surface-2 p-4"
          style={{ boxShadow: "0 0 24px -10px rgba(106,227,255,0.4)" }}
        >
          <p className="text-xs uppercase tracking-wider text-muted">Predicted Price (24h)</p>
          <p className="font-numeric mt-1 text-lg font-bold text-foreground">
            {formatCurrency(prediction.predicted_price_24h)}
          </p>
        </div>
        <div
          className="rounded-xl border border-border bg-surface-2 p-4"
          style={{ boxShadow: "0 0 24px -10px rgba(180,109,255,0.4)" }}
        >
          <p className="text-xs uppercase tracking-wider text-muted">Predicted Price (48h)</p>
          <p className="font-numeric mt-1 text-lg font-bold text-foreground">
            {formatCurrency(prediction.predicted_price_48h)}
          </p>
        </div>
      </div>

      <div
        className="mt-4 rounded-xl border border-border bg-surface-2 p-4"
        style={{ boxShadow: "0 0 24px -10px rgba(255,200,87,0.4)" }}
      >
        <p className="text-xs uppercase tracking-wider text-muted">95% Confidence Interval (48h forecast)</p>
        <p className="font-numeric mt-1 text-lg font-bold text-foreground">
          {formatCurrency(prediction.confidence_interval_low)} – {formatCurrency(prediction.confidence_interval_high)}
        </p>
      </div>
    </Card>
  );
}

function Stat({ label, value, accent }: { label: string; value: string; accent?: string }) {
  return (
    <div>
      <p className="text-xs uppercase tracking-wider text-muted">{label}</p>
      <p className={`font-numeric mt-1 text-xl font-bold ${accent ?? "text-foreground"}`}>{value}</p>
    </div>
  );
}

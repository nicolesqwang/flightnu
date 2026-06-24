import { clsx } from "clsx";
import { Card } from "@/components/ui/Card";
import { RecommendationBadge } from "@/components/ui/RecommendationBadge";
import type { Prediction } from "@/lib/types";

const GLOW_BY_RECOMMENDATION: Record<string, string> = {
  BUY_NOW: "glow-green border-l-accent-green/70",
  WAIT: "glow-red border-l-accent-red/70",
  MONITOR: "glow-yellow border-l-accent-yellow/70",
};

export function RecommendationSection({ prediction }: { prediction: Prediction }) {
  return (
    <Card className={clsx("border-l-4", GLOW_BY_RECOMMENDATION[prediction.recommendation])}>
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold uppercase tracking-wider text-foreground">Recommendation</h3>
        <RecommendationBadge recommendation={prediction.recommendation} size="lg" />
      </div>
      <p className="mt-4 leading-relaxed text-muted">{prediction.explanation}</p>
    </Card>
  );
}

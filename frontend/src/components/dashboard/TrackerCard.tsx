"use client";

import { useRouter } from "next/navigation";
import { clsx } from "clsx";
import { Card } from "@/components/ui/Card";
import { RecommendationBadge } from "@/components/ui/RecommendationBadge";
import { formatCurrency, formatDate, formatPercent } from "@/lib/format";
import type { TrackerCard as TrackerCardType } from "@/lib/types";

const GLOW_BY_RECOMMENDATION: Record<string, string> = {
  BUY_NOW: "glow-green",
  WAIT: "glow-red",
  MONITOR: "glow-yellow",
};

export function TrackerCard({ card }: { card: TrackerCardType }) {
  const router = useRouter();
  const { tracker } = card;
  const glowClass = card.recommendation ? GLOW_BY_RECOMMENDATION[card.recommendation] : "glow-blue";

  return (
    <Card
      className={clsx("animate-fade-in-up cursor-pointer hover:-translate-y-0.5", glowClass)}
      as="section"
    >
      <div onClick={() => router.push(`/trackers/${tracker.id}`)}>
        <div className="flex items-start justify-between">
          <div>
            <p className="flex items-center gap-2 text-lg font-bold text-foreground">
              <span>{tracker.origin_airport}</span>
              <span className="text-muted">→</span>
              <span>{tracker.destination_airport}</span>
            </p>
            <p className="mt-1 text-xs text-muted">
              Departs {formatDate(tracker.departure_date)}
              {tracker.return_date ? ` · Returns ${formatDate(tracker.return_date)}` : ""}
            </p>
          </div>
          <RecommendationBadge recommendation={card.recommendation} />
        </div>

        <div className="mt-5 grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs uppercase tracking-wider text-muted">Current Price</p>
            <p className="font-numeric mt-1 text-xl font-bold text-foreground">{formatCurrency(card.current_price)}</p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-wider text-muted">Historical Average</p>
            <p className="font-numeric mt-1 text-xl font-bold text-foreground">
              {formatCurrency(card.historical_average)}
            </p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-wider text-muted">Savings Opportunity</p>
            <p className="font-numeric neon-text-green mt-1 text-xl font-bold text-accent-green">
              {formatCurrency(card.savings_opportunity)}
            </p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-wider text-muted">Confidence</p>
            <p className="font-numeric mt-1 text-xl font-bold text-foreground">{formatPercent(card.confidence_score)}</p>
          </div>
        </div>

        <p className="mt-4 text-xs text-muted">{card.observation_count} price observations collected</p>
      </div>
    </Card>
  );
}

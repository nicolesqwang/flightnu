import { Card } from "@/components/ui/Card";
import { formatCurrency, formatDateTime, sourceLabel } from "@/lib/format";
import type { PriceObservation } from "@/lib/types";

export function LatestFareCard({ observation }: { observation: PriceObservation }) {
  const stops =
    observation.transfers === null || observation.transfers === undefined
      ? null
      : observation.transfers === 0
        ? "Nonstop"
        : `${observation.transfers} stop${observation.transfers > 1 ? "s" : ""}`;
  const simulated = observation.source === "simulator";

  return (
    <Card className="glow-blue">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h3 className="text-sm font-bold uppercase tracking-wider text-foreground">Latest Fare</h3>
          <p className="font-numeric mt-2 text-2xl font-bold text-foreground">{formatCurrency(observation.price)}</p>
          <p className="mt-1 text-sm text-muted">
            {[observation.airline, observation.flight_number, stops].filter(Boolean).join(" · ")}
          </p>
          <p className="mt-1 text-xs text-muted">
            Source: {sourceLabel(observation.source)} · seen {formatDateTime(observation.timestamp)}
            {simulated && " · simulated demo data, not a real fare"}
          </p>
        </div>
        {observation.booking_link && !simulated && (
          <a
            href={observation.booking_link}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-xl border border-accent-blue/40 px-4 py-2.5 text-sm font-medium text-accent-blue hover:bg-accent-blue/10"
          >
            View this fare ↗
          </a>
        )}
      </div>
    </Card>
  );
}

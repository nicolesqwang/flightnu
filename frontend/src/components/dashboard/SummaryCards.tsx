import { Card, CardLabel, CardValue } from "@/components/ui/Card";
import { CardSkeleton } from "@/components/ui/Skeleton";
import { formatCurrency, formatPercent } from "@/lib/format";
import type { DashboardSummary } from "@/lib/types";

export function SummaryCards({ summary }: { summary: DashboardSummary | null }) {
  if (!summary) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <CardSkeleton key={i} />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <Card className="glow-blue animate-fade-in-up">
        <CardLabel>Total Active Trackers</CardLabel>
        <CardValue className="neon-text-blue">{summary.total_active_trackers}</CardValue>
      </Card>
      <Card className="glow-purple animate-fade-in-up">
        <CardLabel>Total Observations Collected</CardLabel>
        <CardValue>{summary.total_observations.toLocaleString()}</CardValue>
      </Card>
      <Card className="glow-green animate-fade-in-up">
        <CardLabel>Average Savings Opportunity</CardLabel>
        <CardValue className="text-accent-green neon-text-green">
          {formatCurrency(summary.average_savings_opportunity)}
        </CardValue>
      </Card>
      <Card className="glow-yellow animate-fade-in-up">
        <CardLabel>Average Prediction Confidence</CardLabel>
        <CardValue>{formatPercent(summary.average_prediction_confidence)}</CardValue>
      </Card>
    </div>
  );
}

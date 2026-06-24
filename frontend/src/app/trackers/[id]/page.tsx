"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { TopNav } from "@/components/TopNav";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { RecommendationBadge } from "@/components/ui/RecommendationBadge";
import { Skeleton } from "@/components/ui/Skeleton";
import { StatsGrid } from "@/components/tracker/StatsGrid";
import { PriceHistoryChart } from "@/components/tracker/PriceHistoryChart";
import { VolatilityChart } from "@/components/tracker/VolatilityChart";
import { PriceHistogram } from "@/components/tracker/PriceHistogram";
import { AnalyticsSection } from "@/components/tracker/AnalyticsSection";
import { SeasonalitySection } from "@/components/tracker/SeasonalitySection";
import { PredictionSection } from "@/components/tracker/PredictionSection";
import { RecommendationSection } from "@/components/tracker/RecommendationSection";
import { api, ApiError } from "@/lib/api";
import { buildHistogram, buildSeries } from "@/lib/clientAnalytics";
import { formatDate } from "@/lib/format";
import type { TrackerDetail } from "@/lib/types";

export default function TrackerDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const trackerId = params.id;

  const [detail, setDetail] = useState<TrackerDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const data = await api.getTracker(trackerId);
      setDetail(data);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiError && err.status === 404 ? "Tracker not found." : "Could not load tracker.");
    }
  }, [trackerId]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- intentional fetch-on-mount + poll
    load();
    const interval = setInterval(load, 30_000);
    return () => clearInterval(interval);
  }, [load]);

  async function handleRefresh() {
    setRefreshing(true);
    try {
      await api.refreshTracker(trackerId);
      await load();
    } catch {
      setError("Failed to refresh price data.");
    } finally {
      setRefreshing(false);
    }
  }

  async function handleDelete() {
    if (!confirm("Delete this tracker and all its data? This cannot be undone.")) return;
    await api.deleteTracker(trackerId);
    router.push("/");
  }

  if (error) {
    return (
      <div className="flex min-h-screen flex-col">
        <TopNav />
        <main className="mx-auto w-full max-w-5xl flex-1 px-6 py-16 text-center">
          <p className="text-lg text-foreground">{error}</p>
          <Button className="mt-4" variant="secondary" onClick={() => router.push("/")}>
            Back to Dashboard
          </Button>
        </main>
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="flex min-h-screen flex-col">
        <TopNav />
        <main className="mx-auto w-full max-w-7xl flex-1 px-6 py-8 space-y-6">
          <Skeleton className="h-10 w-64" />
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-24 w-full" />
            ))}
          </div>
          <Skeleton className="h-72 w-full" />
        </main>
      </div>
    );
  }

  const { tracker, observations, latest_prediction: prediction } = detail;
  const series = buildSeries(observations);
  const histogram = buildHistogram(observations.map((o) => o.price));

  return (
    <div className="flex min-h-screen flex-col">
      <TopNav />
      <main className="mx-auto w-full max-w-7xl flex-1 px-6 py-8 space-y-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <button onClick={() => router.push("/")} className="text-xs text-muted hover:text-foreground">
              ← Back to Dashboard
            </button>
            <h1 className="font-numeric mt-2 flex items-center gap-3 text-3xl font-bold tracking-tight text-foreground">
              <span>{tracker.origin_airport}</span>
              <span className="text-accent-blue neon-text-blue">→</span>
              <span>{tracker.destination_airport}</span>
              {prediction && <RecommendationBadge recommendation={prediction.recommendation} />}
            </h1>
            <p className="mt-1 text-sm text-muted">
              Departs {formatDate(tracker.departure_date)}
              {tracker.return_date ? ` · Returns ${formatDate(tracker.return_date)}` : ""} ·{" "}
              {observations.length} observations collected
            </p>
          </div>
          <div className="flex gap-3">
            <Button variant="secondary" onClick={handleRefresh} disabled={refreshing}>
              {refreshing ? "Refreshing…" : "Refresh Now"}
            </Button>
            <Button variant="danger" onClick={handleDelete}>
              Delete
            </Button>
          </div>
        </div>

        {!prediction ? (
          <Card>
            <p className="text-sm text-muted">No prediction available yet for this tracker.</p>
          </Card>
        ) : (
          <>
            <StatsGrid prediction={prediction} />
            <PriceHistoryChart series={series} />
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              <VolatilityChart series={series} />
              <PriceHistogram buckets={histogram} />
            </div>
            <AnalyticsSection prediction={prediction} />
            <SeasonalitySection prediction={prediction} />
            <PredictionSection prediction={prediction} />
            <RecommendationSection prediction={prediction} />
          </>
        )}
      </main>
    </div>
  );
}

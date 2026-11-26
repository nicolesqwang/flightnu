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
import { LatestFareCard } from "@/components/tracker/LatestFareCard";
import { api, ApiError, getAdminKey, setAdminKey } from "@/lib/api";
import { buildHistogram, buildSeries } from "@/lib/clientAnalytics";
import { formatDate, formatRelative } from "@/lib/format";
import type { TrackerDetail } from "@/lib/types";

export default function TrackerDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const trackerId = params.id;

  const [detail, setDetail] = useState<TrackerDetail | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState<"refresh" | "delete" | "pause" | null>(null);

  const load = useCallback(async () => {
    try {
      const data = await api.getTracker(trackerId);
      setDetail(data);
      setLoadError(null);
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) setLoadError("Tracker not found.");
      else setLoadError(err instanceof ApiError ? err.message : "Could not load tracker.");
    }
  }, [trackerId]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- intentional fetch-on-mount + poll
    load();
    const interval = setInterval(load, 30_000);
    return () => clearInterval(interval);
  }, [load]);

  async function handleRefresh() {
    setBusy("refresh");
    setNotice(null);
    try {
      const t = await api.refreshTracker(trackerId);
      await load();
      setNotice(t.last_error ? `No new price: ${t.last_error}` : "Fetched the latest real fare.");
    } catch (err) {
      setNotice(err instanceof ApiError ? err.message : "Failed to refresh price data.");
    } finally {
      setBusy(null);
    }
  }

  /** Runs an owner-only action, asking for the admin key once if needed. */
  async function withAdmin(action: () => Promise<void>) {
    try {
      await action();
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        const key = window.prompt("Enter the FlightNu admin key to manage trackers:");
        if (!key) return;
        setAdminKey(key);
        try {
          await action();
        } catch (retryErr) {
          if (retryErr instanceof ApiError && retryErr.status === 401) setAdminKey(null);
          setNotice(retryErr instanceof ApiError ? retryErr.message : "Action failed.");
        }
        return;
      }
      setNotice(err instanceof ApiError ? err.message : "Action failed.");
    }
  }

  async function handleDelete() {
    if (!confirm("Delete this tracker and all its price history? This cannot be undone.")) return;
    setBusy("delete");
    await withAdmin(async () => {
      await api.deleteTracker(trackerId);
      router.push("/");
    });
    setBusy(null);
  }

  async function handleTogglePause() {
    if (!detail) return;
    setBusy("pause");
    await withAdmin(async () => {
      await api.setTrackerActive(trackerId, !detail.tracker.active);
      await load();
    });
    setBusy(null);
  }

  if (loadError && !detail) {
    return (
      <div className="flex min-h-screen flex-col">
        <TopNav />
        <main className="mx-auto w-full max-w-5xl flex-1 px-6 py-16 text-center">
          <p className="text-lg text-foreground">{loadError}</p>
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
        <main className="mx-auto w-full max-w-7xl flex-1 space-y-6 px-6 py-8">
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
  const latestObs = observations.at(-1) ?? null;
  const departed = tracker.departure_date < new Date().toISOString().slice(0, 10);
  const hasOwnerKey = typeof window !== "undefined" && !!getAdminKey();

  return (
    <div className="flex min-h-screen flex-col">
      <TopNav />
      <main className="mx-auto w-full max-w-7xl flex-1 space-y-6 px-6 py-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <button onClick={() => router.push("/")} className="text-xs text-muted hover:text-foreground">
              ← Back to Dashboard
            </button>
            <h1 className="font-numeric mt-2 flex items-center gap-3 text-3xl font-bold tracking-tight text-foreground">
              <span>{tracker.origin_airport}</span>
              <span className="neon-text-blue text-accent-blue">→</span>
              <span>{tracker.destination_airport}</span>
              {prediction && tracker.active && <RecommendationBadge recommendation={prediction.recommendation} />}
            </h1>
            <p className="mt-1 text-sm text-muted">
              Departs {formatDate(tracker.departure_date)}
              {tracker.return_date ? ` · Returns ${formatDate(tracker.return_date)}` : " · One way"} ·{" "}
              {detail.total_observations} prices collected · checked {formatRelative(tracker.last_checked_at)}
              {!tracker.active && (departed ? " · Departed, tracking stopped" : " · Paused")}
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Button variant="secondary" onClick={handleRefresh} disabled={busy !== null || !tracker.active}>
              {busy === "refresh" ? "Checking…" : "Check Price Now"}
            </Button>
            {!departed && (
              <Button variant="ghost" onClick={handleTogglePause} disabled={busy !== null} title={hasOwnerKey ? undefined : "Owner only"}>
                {tracker.active ? "Pause" : "Resume"}
              </Button>
            )}
            <Button variant="danger" onClick={handleDelete} disabled={busy !== null} title={hasOwnerKey ? undefined : "Owner only"}>
              {busy === "delete" ? "Deleting…" : "Delete"}
            </Button>
          </div>
        </div>

        {(notice || loadError) && (
          <div className="rounded-xl border border-border bg-surface-2 px-4 py-3 text-sm text-muted">{notice ?? loadError}</div>
        )}
        {tracker.last_error && !notice && tracker.active && (
          <div className="rounded-xl border border-accent-yellow/30 bg-accent-yellow/10 px-4 py-3 text-sm text-accent-yellow">
            Last price check found nothing: {tracker.last_error}
          </div>
        )}

        {!prediction ? (
          <Card>
            <p className="text-sm text-muted">
              No real fare has been found for this trip yet. Prices are checked automatically; popular routes usually
              appear within a few hours.
            </p>
          </Card>
        ) : (
          <>
            <StatsGrid prediction={prediction} />
            <RecommendationSection prediction={prediction} />
            {latestObs && <LatestFareCard observation={latestObs} />}
            <PriceHistoryChart series={series} />
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              <VolatilityChart series={series} />
              <PriceHistogram buckets={histogram} />
            </div>
            <AnalyticsSection prediction={prediction} />
            <PredictionSection prediction={prediction} />
            <SeasonalitySection prediction={prediction} />
          </>
        )}
      </main>
    </div>
  );
}

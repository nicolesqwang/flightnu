"use client";

import { useCallback, useEffect, useState } from "react";
import { TopNav } from "@/components/TopNav";
import { SummaryCards } from "@/components/dashboard/SummaryCards";
import { TrackerCard } from "@/components/dashboard/TrackerCard";
import { CreateTrackerModal } from "@/components/CreateTrackerModal";
import { TrackerCardSkeleton } from "@/components/ui/Skeleton";
import { Button } from "@/components/ui/Button";
import { api, ApiError } from "@/lib/api";
import { formatRelative } from "@/lib/format";
import type { DashboardSummary, ServerStatus } from "@/lib/types";

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [status, setStatus] = useState<ServerStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);

  const loadSummary = useCallback(async () => {
    try {
      const [data, st] = await Promise.all([api.getDashboardSummary(), api.getStatus()]);
      setSummary(data);
      setStatus(st);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not reach the FlightNu API.");
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- intentional fetch-on-mount + poll
    loadSummary();
    // Poll faster while the server is waking from sleep, then every 30s.
    const interval = setInterval(loadSummary, summary ? 30_000 : 8_000);
    return () => clearInterval(interval);
  }, [loadSummary, summary]);

  const atCapacity = status ? status.active_trackers >= status.max_active_trackers : false;

  return (
    <div className="flex min-h-screen flex-col">
      <TopNav />
      <main className="mx-auto w-full max-w-7xl flex-1 px-6 py-8">
        <div className="mb-8 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-foreground">Dashboard</h1>
            <p className="mt-1 text-sm text-muted">
              Real airfares tracked over time, with statistical buy/wait signals.
              {status?.last_ingest_at && <> Last price check {formatRelative(status.last_ingest_at)}.</>}
            </p>
          </div>
          <Button onClick={() => setModalOpen(true)} disabled={atCapacity} title={atCapacity ? "Tracker limit reached" : undefined}>
            + New Tracker
          </Button>
        </div>

        {error && (
          <div className="mb-6 rounded-xl border border-accent-yellow/30 bg-accent-yellow/10 px-4 py-3 text-sm text-accent-yellow">
            {error} {!summary && "Retrying automatically…"}
          </div>
        )}

        {status && !status.provider_configured && (
          <div className="mb-6 rounded-xl border border-accent-red/30 bg-accent-red/10 px-4 py-3 text-sm text-accent-red">
            No flight-price API key is configured on the server, so no new prices can be fetched. Set
            TRAVELPAYOUTS_TOKEN on the API service.
          </div>
        )}

        {status?.price_provider === "simulator" && (
          <div className="mb-6 rounded-xl border border-accent-yellow/30 bg-accent-yellow/10 px-4 py-3 text-sm text-accent-yellow">
            Demo mode: prices on this server are simulated, not real fares.
          </div>
        )}

        <SummaryCards summary={summary} />

        <div className="mt-10">
          <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-muted">Your Trackers</h2>

          {!summary ? (
            <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <TrackerCardSkeleton key={i} />
              ))}
            </div>
          ) : summary.tracker_cards.length === 0 ? (
            <EmptyState onCreate={() => setModalOpen(true)} />
          ) : (
            <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
              {summary.tracker_cards.map((card) => (
                <TrackerCard key={card.tracker.id} card={card} />
              ))}
            </div>
          )}
        </div>
      </main>

      <CreateTrackerModal open={modalOpen} onClose={() => setModalOpen(false)} onCreated={loadSummary} />
    </div>
  );
}

function EmptyState({ onCreate }: { onCreate: () => void }) {
  return (
    <div className="glass-card flex flex-col items-center justify-center rounded-2xl px-6 py-16 text-center">
      <p className="text-3xl">✈</p>
      <p className="mt-4 text-base font-medium text-foreground">No trackers yet</p>
      <p className="mt-1 max-w-sm text-sm text-muted">
        Create a tracker to start collecting real fares and getting buy/wait recommendations.
      </p>
      <Button className="mt-5" onClick={onCreate}>
        + New Tracker
      </Button>
    </div>
  );
}

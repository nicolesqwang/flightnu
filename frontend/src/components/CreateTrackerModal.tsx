"use client";

import { useState } from "react";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { api, ApiError } from "@/lib/api";
import type { TrackingFrequency } from "@/lib/types";

const FREQUENCIES: { value: TrackingFrequency; label: string }[] = [
  { value: "HOURLY", label: "Every hour" },
  { value: "EVERY_4_HOURS", label: "Every 4 hours" },
  { value: "DAILY", label: "Once a day" },
];

export function CreateTrackerModal({
  open,
  onClose,
  onCreated,
}: {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}) {
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [departureDate, setDepartureDate] = useState("");
  const [returnDate, setReturnDate] = useState("");
  const [frequency, setFrequency] = useState<TrackingFrequency>("EVERY_4_HOURS");
  const [alertsEnabled, setAlertsEnabled] = useState(true);
  const [discordWebhook, setDiscordWebhook] = useState("");
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function reset() {
    setOrigin("");
    setDestination("");
    setDepartureDate("");
    setReturnDate("");
    setFrequency("EVERY_4_HOURS");
    setAlertsEnabled(true);
    setDiscordWebhook("");
    setEmail("");
    setError(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (origin.trim().length !== 3 || destination.trim().length !== 3) {
      setError("Airport codes must be exactly 3 letters (e.g. SFO).");
      return;
    }
    if (!departureDate) {
      setError("Departure date is required.");
      return;
    }

    setSubmitting(true);
    try {
      await api.createTracker({
        origin_airport: origin.trim().toUpperCase(),
        destination_airport: destination.trim().toUpperCase(),
        departure_date: departureDate,
        return_date: returnDate || null,
        tracking_frequency: frequency,
        alerts_enabled: alertsEnabled,
        discord_webhook_url: discordWebhook || null,
        alert_email: email || null,
      });
      reset();
      onCreated();
      onClose();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create tracker. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Modal
      open={open}
      onClose={() => {
        reset();
        onClose();
      }}
      title="New Flight Tracker"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <Field label="Origin Airport">
            <input
              value={origin}
              onChange={(e) => setOrigin(e.target.value.toUpperCase())}
              maxLength={3}
              placeholder="SFO"
              className="input"
              required
            />
          </Field>
          <Field label="Destination Airport">
            <input
              value={destination}
              onChange={(e) => setDestination(e.target.value.toUpperCase())}
              maxLength={3}
              placeholder="JFK"
              className="input"
              required
            />
          </Field>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <Field label="Departure Date">
            <input
              type="date"
              value={departureDate}
              onChange={(e) => setDepartureDate(e.target.value)}
              className="input"
              required
            />
          </Field>
          <Field label="Return Date (optional)">
            <input
              type="date"
              value={returnDate}
              onChange={(e) => setReturnDate(e.target.value)}
              className="input"
            />
          </Field>
        </div>

        <Field label="Tracking Frequency">
          <select
            value={frequency}
            onChange={(e) => setFrequency(e.target.value as TrackingFrequency)}
            className="input"
          >
            {FREQUENCIES.map((f) => (
              <option key={f.value} value={f.value}>
                {f.label}
              </option>
            ))}
          </select>
        </Field>

        <label className="flex items-center gap-3 rounded-xl border border-border bg-surface-2 px-4 py-3">
          <input
            type="checkbox"
            checked={alertsEnabled}
            onChange={(e) => setAlertsEnabled(e.target.checked)}
            className="h-4 w-4 accent-accent-blue"
          />
          <span className="text-sm text-foreground">Enable BUY NOW alerts</span>
        </label>

        {alertsEnabled && (
          <div className="space-y-3 rounded-xl border border-border bg-surface-2 p-4">
            <Field label="Discord Webhook URL (optional)">
              <input
                value={discordWebhook}
                onChange={(e) => setDiscordWebhook(e.target.value)}
                placeholder="https://discord.com/api/webhooks/..."
                className="input"
              />
            </Field>
            <Field label="Alert Email (optional)">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="input"
              />
            </Field>
          </div>
        )}

        {error && <p className="text-sm text-accent-red">{error}</p>}

        <div className="flex justify-end gap-3 pt-2">
          <Button type="button" variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={submitting}>
            {submitting ? "Creating…" : "Create Tracker"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-muted">{label}</span>
      {children}
    </label>
  );
}

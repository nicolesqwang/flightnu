"use client";

import { useEffect, useId, useState } from "react";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { api, ApiError } from "@/lib/api";
import type { Airport, TrackingFrequency } from "@/lib/types";

const FREQUENCIES: { value: TrackingFrequency; label: string }[] = [
  { value: "HOURLY", label: "Every hour" },
  { value: "EVERY_4_HOURS", label: "Every 4 hours" },
  { value: "DAILY", label: "Once a day" },
];

function localISODate(offsetDays = 0): string {
  const d = new Date();
  d.setDate(d.getDate() + offsetDays);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

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

  function close() {
    reset();
    onClose();
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    const o = origin.trim().toUpperCase();
    const d = destination.trim().toUpperCase();
    if (!/^[A-Z]{3}$/.test(o) || !/^[A-Z]{3}$/.test(d)) {
      setError("Airport codes must be exactly 3 letters (e.g. SFO).");
      return;
    }
    if (o === d) {
      setError("Origin and destination must be different.");
      return;
    }
    if (!departureDate) {
      setError("Departure date is required.");
      return;
    }
    if (returnDate && returnDate < departureDate) {
      setError("Return date must be on or after the departure date.");
      return;
    }

    setSubmitting(true);
    try {
      await api.createTracker({
        origin_airport: o,
        destination_airport: d,
        departure_date: departureDate,
        return_date: returnDate || null,
        tracking_frequency: frequency,
        alerts_enabled: alertsEnabled,
        discord_webhook_url: alertsEnabled && discordWebhook ? discordWebhook : null,
        alert_email: alertsEnabled && email ? email : null,
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
    <Modal open={open} onClose={close} title="New Flight Tracker">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <Field label="Origin Airport">
            <AirportInput value={origin} onChange={setOrigin} placeholder="SFO" />
          </Field>
          <Field label="Destination Airport">
            <AirportInput value={destination} onChange={setDestination} placeholder="JFK" />
          </Field>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <Field label="Departure Date">
            <input
              type="date"
              value={departureDate}
              min={localISODate()}
              max={localISODate(330)}
              onChange={(e) => setDepartureDate(e.target.value)}
              className="input"
              required
            />
          </Field>
          <Field label="Return Date (optional)">
            <input
              type="date"
              value={returnDate}
              min={departureDate || localISODate()}
              max={localISODate(330)}
              onChange={(e) => setReturnDate(e.target.value)}
              className="input"
            />
          </Field>
        </div>

        <Field label="Check Price">
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

        <p className="text-xs text-muted">
          The first real price is fetched right away. Forecasts start after 6 readings spanning 12+ hours.
        </p>

        {error && <p className="text-sm text-accent-red">{error}</p>}

        <div className="flex justify-end gap-3 pt-2">
          <Button type="button" variant="ghost" onClick={close}>
            Cancel
          </Button>
          <Button type="submit" disabled={submitting}>
            {submitting ? "Fetching first price…" : "Create Tracker"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}

function AirportInput({
  value,
  onChange,
  placeholder,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder: string;
}) {
  const listId = useId();
  const [options, setOptions] = useState<Airport[]>([]);

  useEffect(() => {
    const q = value.trim();
    if (q.length < 2) return;
    const timer = setTimeout(() => {
      api
        .searchAirports(q)
        .then(setOptions)
        .catch(() => setOptions([]));
    }, 250);
    return () => clearTimeout(timer);
  }, [value]);

  return (
    <>
      <input
        value={value}
        onChange={(e) => {
          // Picking a suggestion yields "SFO — San Francisco…"; keep the code.
          const v = e.target.value.toUpperCase();
          onChange(/^[A-Z]{3} — /.test(v) ? v.slice(0, 3) : v);
        }}
        list={listId}
        placeholder={placeholder}
        className="input"
        autoComplete="off"
        required
      />
      <datalist id={listId}>
        {options.map((a) => (
          <option key={a.code} value={`${a.code} — ${a.city || a.name}`}>
            {a.name}, {a.country}
          </option>
        ))}
      </datalist>
    </>
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

export function formatCurrency(value: number | null | undefined, opts: { showSign?: boolean } = {}): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  const sign = opts.showSign && value > 0 ? "+" : "";
  return `${sign}$${value.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
}

export function formatPercent(value: number | null | undefined, digits = 0): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `${value.toFixed(digits)}%`;
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  // Date-only strings ("YYYY-MM-DD") are parsed by `Date` as UTC midnight, which
  // shifts a day back once toLocaleDateString renders in a timezone behind UTC.
  // Build the date from its components in local time instead.
  const [year, month, day] = value.slice(0, 10).split("-").map(Number);
  const localDate = new Date(year, month - 1, day);
  return localDate.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

/** Timestamps arrive as ISO strings ending in "Z" and render in the viewer's time zone. */
export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  return new Date(value).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function formatRelative(value: string | null | undefined): string {
  if (!value) return "never";
  const minutes = Math.round((Date.now() - new Date(value).getTime()) / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 48) return `${hours}h ago`;
  return `${Math.round(hours / 24)}d ago`;
}

/** Converts an hour of day in UTC to the viewer's local hour label. */
export function formatUtcHourLocal(hour: number | null | undefined): string {
  if (hour === null || hour === undefined) return "—";
  const d = new Date(Date.UTC(2026, 0, 5, hour));
  return d.toLocaleTimeString("en-US", { hour: "numeric" });
}

export const RECOMMENDATION_LABEL: Record<string, string> = {
  BUY_NOW: "BUY NOW",
  WAIT: "WAIT",
  MONITOR: "MONITOR",
};

export const SOURCE_LABEL: Record<string, string> = {
  travelpayouts: "Aviasales",
  serpapi: "Google Flights",
  serpapi_history: "Google Flights history",
  simulator: "Simulated",
};

export function sourceLabel(source: string | null | undefined): string {
  if (!source) return "Legacy data";
  return SOURCE_LABEL[source] ?? source;
}

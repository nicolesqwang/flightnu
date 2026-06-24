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

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  return new Date(value).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function formatHour(hour: number | null | undefined): string {
  if (hour === null || hour === undefined) return "—";
  const period = hour >= 12 ? "PM" : "AM";
  const h12 = hour % 12 === 0 ? 12 : hour % 12;
  return `${h12}:00 ${period}`;
}

export const RECOMMENDATION_LABEL: Record<string, string> = {
  BUY_NOW: "BUY NOW",
  WAIT: "WAIT",
  MONITOR: "MONITOR",
};

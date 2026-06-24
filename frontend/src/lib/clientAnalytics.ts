import type { PriceObservation } from "./types";

export interface SeriesPoint {
  timestamp: string;
  price: number;
  sma: number;
  ewma: number;
  deviation: number;
}

export function simpleMovingAverage(prices: number[], window = 5): number[] {
  if (prices.length === 0) return [];
  const w = Math.max(1, Math.min(window, prices.length));
  const out: number[] = [];
  for (let i = 0; i < prices.length; i++) {
    const start = Math.max(0, i - w + 1);
    const slice = prices.slice(start, i + 1);
    out.push(slice.reduce((a, b) => a + b, 0) / slice.length);
  }
  return out;
}

export function ewma(prices: number[], alpha = 0.3): number[] {
  if (prices.length === 0) return [];
  const out: number[] = [prices[0]];
  for (let i = 1; i < prices.length; i++) {
    out.push(alpha * prices[i] + (1 - alpha) * out[i - 1]);
  }
  return out;
}

export function buildSeries(observations: PriceObservation[]): SeriesPoint[] {
  const sorted = [...observations].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );
  const prices = sorted.map((o) => o.price);
  const sma = simpleMovingAverage(prices, 5);
  const ew = ewma(prices, 0.3);
  const mean = prices.reduce((a, b) => a + b, 0) / (prices.length || 1);

  return sorted.map((o, i) => ({
    timestamp: o.timestamp,
    price: o.price,
    sma: Math.round(sma[i] * 100) / 100,
    ewma: Math.round(ew[i] * 100) / 100,
    deviation: Math.round((o.price - mean) * 100) / 100,
  }));
}

export function buildHistogram(prices: number[], bucketCount = 10): { bucket: string; count: number }[] {
  if (prices.length === 0) return [];
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const range = max - min || 1;
  const bucketSize = range / bucketCount;

  const buckets = Array.from({ length: bucketCount }, () => 0);
  for (const p of prices) {
    const idx = Math.min(bucketCount - 1, Math.floor((p - min) / bucketSize));
    buckets[idx]++;
  }

  return buckets.map((count, i) => ({
    bucket: `$${Math.round(min + i * bucketSize)}`,
    count,
  }));
}

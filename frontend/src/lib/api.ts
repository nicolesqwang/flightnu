import type {
  DashboardSummary,
  Prediction,
  Tracker,
  TrackerCreatePayload,
  TrackerDetail,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8123";

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
    cache: "no-store",
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new ApiError(res.status, body || `Request to ${path} failed with ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  getDashboardSummary: () => request<DashboardSummary>("/api/dashboard/summary"),
  listTrackers: () => request<Tracker[]>("/api/trackers"),
  getTracker: (id: string) => request<TrackerDetail>(`/api/trackers/${id}`),
  createTracker: (payload: TrackerCreatePayload) =>
    request<Tracker>("/api/trackers", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  refreshTracker: (id: string) => request<Prediction>(`/api/trackers/${id}/refresh`, { method: "POST" }),
  setTrackerActive: (id: string, active: boolean) =>
    request<Tracker>(`/api/trackers/${id}?active=${active}`, { method: "PATCH" }),
  deleteTracker: (id: string) => request<void>(`/api/trackers/${id}`, { method: "DELETE" }),
};

export { ApiError };

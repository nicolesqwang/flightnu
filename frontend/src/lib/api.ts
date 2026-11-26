import type {
  Airport,
  DashboardSummary,
  ServerStatus,
  Tracker,
  TrackerCreatePayload,
  TrackerDetail,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8123";
const ADMIN_KEY_STORAGE = "flightnu.adminKey";

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export function getAdminKey(): string | null {
  try {
    return window.localStorage.getItem(ADMIN_KEY_STORAGE);
  } catch {
    return null;
  }
}

export function setAdminKey(key: string | null) {
  try {
    if (key) window.localStorage.setItem(ADMIN_KEY_STORAGE, key);
    else window.localStorage.removeItem(ADMIN_KEY_STORAGE);
  } catch {
    // storage unavailable (private mode etc.); key lasts for this action only
  }
}

/** Turns FastAPI error bodies ({detail: string | [{msg}]}) into one readable line. */
function errorMessage(status: number, body: string, path: string): string {
  try {
    const parsed = JSON.parse(body);
    const detail = parsed?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail.length) {
      return detail
        .map((d: { msg?: string }) => (d.msg ?? "").replace(/^Value error, /, ""))
        .filter(Boolean)
        .join(" ");
    }
  } catch {
    // not JSON
  }
  if (status === 502 || status === 503) {
    return "The server is waking up (free hosting sleeps when idle). This takes about a minute.";
  }
  return body || `Request to ${path} failed with ${status}`;
}

async function request<T>(path: string, init?: RequestInit & { admin?: boolean }): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (init?.admin) {
    const key = getAdminKey();
    if (key) headers["X-Admin-Key"] = key;
  }
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: { ...headers, ...(init?.headers as Record<string, string> | undefined) },
      cache: "no-store",
    });
  } catch {
    throw new ApiError(0, "The server is waking up (free hosting sleeps when idle). This takes about a minute.");
  }
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new ApiError(res.status, errorMessage(res.status, body, path));
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  getStatus: () => request<ServerStatus>("/api/status"),
  getDashboardSummary: () => request<DashboardSummary>("/api/dashboard/summary"),
  getTracker: (id: string) => request<TrackerDetail>(`/api/trackers/${id}`),
  searchAirports: (q: string) => request<Airport[]>(`/api/airports?q=${encodeURIComponent(q)}&limit=8`),
  createTracker: (payload: TrackerCreatePayload) =>
    request<Tracker>("/api/trackers", { method: "POST", body: JSON.stringify(payload) }),
  refreshTracker: (id: string) => request<Tracker>(`/api/trackers/${id}/refresh`, { method: "POST" }),
  setTrackerActive: (id: string, active: boolean) =>
    request<Tracker>(`/api/trackers/${id}?active=${active}`, { method: "PATCH", admin: true }),
  deleteTracker: (id: string) => request<void>(`/api/trackers/${id}`, { method: "DELETE", admin: true }),
};

export { ApiError };

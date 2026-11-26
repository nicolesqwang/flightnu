export type Recommendation = "BUY_NOW" | "WAIT" | "MONITOR";

export type TrackingFrequency = "HOURLY" | "EVERY_4_HOURS" | "DAILY";

export interface Tracker {
  id: string;
  origin_airport: string;
  destination_airport: string;
  departure_date: string;
  return_date: string | null;
  tracking_frequency: TrackingFrequency;
  alerts_enabled: boolean;
  active: boolean;
  created_at: string;
  last_checked_at: string | null;
  last_error: string | null;
}

export interface PriceObservation {
  id: string;
  price: number;
  airline: string;
  timestamp: string;
  source: string | null;
  flight_number: string | null;
  transfers: number | null;
  booking_link: string | null;
}

export interface Prediction {
  id: string;
  historical_average: number;
  historical_low: number;
  historical_high: number;
  std_dev: number;
  z_score: number;
  current_price: number;
  sma: number;
  ewma: number;
  predicted_price_24h: number;
  predicted_price_48h: number;
  prob_increase_24h: number;
  prob_increase_48h: number;
  expected_increase: number;
  expected_decrease: number;
  confidence_interval_low: number;
  confidence_interval_high: number;
  confidence_score: number;
  recommendation: Recommendation;
  explanation: string;
  cheapest_day_of_week: string | null;
  most_expensive_day_of_week: string | null;
  cheapest_hour_of_day: number | null;
  most_expensive_hour_of_day: number | null;
  observation_count: number | null;
  percentile: number | null;
  days_to_departure: number | null;
  has_forecast: boolean | null;
  generated_at: string;
}

export interface TrackerCard {
  tracker: Tracker;
  current_price: number | null;
  historical_average: number | null;
  savings_opportunity: number | null;
  confidence_score: number | null;
  recommendation: Recommendation | null;
  observation_count: number;
  data_source: string | null;
}

export interface TrackerDetail {
  tracker: Tracker;
  observations: PriceObservation[];
  latest_prediction: Prediction | null;
  prediction_history: Prediction[];
  total_observations: number;
}

export interface DashboardSummary {
  total_active_trackers: number;
  total_observations: number;
  average_savings_opportunity: number;
  average_prediction_confidence: number;
  tracker_cards: TrackerCard[];
}

export interface ServerStatus {
  price_provider: string;
  provider_configured: boolean;
  serpapi_configured: boolean;
  admin_key_required: boolean;
  max_active_trackers: number;
  active_trackers: number;
  last_ingest_at: string | null;
}

export interface Airport {
  code: string;
  name: string;
  city: string;
  country: string;
}

export interface TrackerCreatePayload {
  origin_airport: string;
  destination_airport: string;
  departure_date: string;
  return_date?: string | null;
  tracking_frequency: TrackingFrequency;
  alerts_enabled: boolean;
  discord_webhook_url?: string | null;
  alert_email?: string | null;
}

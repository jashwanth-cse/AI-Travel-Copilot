import type { CityAnalytics, TripGenerateData, TripRequest } from "../types/api";

const RESULT_KEY = "ai-travel-copilot-result";

export interface StoredTripResult {
  trip: TripRequest;
  result: TripGenerateData;
  analytics: CityAnalytics | null;
  createdAt: string;
}

export function saveTripResult(value: StoredTripResult): void {
  sessionStorage.setItem(RESULT_KEY, JSON.stringify(value));
}

export function loadTripResult(): StoredTripResult | null {
  const raw = sessionStorage.getItem(RESULT_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as StoredTripResult;
  } catch {
    sessionStorage.removeItem(RESULT_KEY);
    return null;
  }
}


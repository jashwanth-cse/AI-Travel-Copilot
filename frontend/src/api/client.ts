import axios from "axios";
import type {
  ApiEnvelope,
  ChatData,
  CityAnalytics,
  HealthData,
  TripGenerateData,
  TripRequest,
} from "../types/api";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
});

export async function generateTrip(payload: TripRequest): Promise<ApiEnvelope<TripGenerateData>> {
  const response = await apiClient.post<ApiEnvelope<TripGenerateData>>("/api/trips/generate", payload);
  return response.data;
}

export async function getCityAnalytics(city: string): Promise<ApiEnvelope<CityAnalytics>> {
  const response = await apiClient.get<ApiEnvelope<CityAnalytics>>(
    `/api/analytics/${encodeURIComponent(city)}`,
  );
  return response.data;
}

export async function askTravelAssistant(message: string): Promise<ApiEnvelope<ChatData>> {
  const response = await apiClient.post<ApiEnvelope<ChatData>>("/api/chat", { message });
  return response.data;
}

export async function getHealth(): Promise<HealthData> {
  const response = await apiClient.get<HealthData>("/health");
  return response.data;
}


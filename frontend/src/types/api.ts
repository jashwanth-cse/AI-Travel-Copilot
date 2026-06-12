export interface ApiEnvelope<T> {
  success: boolean;
  message: string;
  data: T;
  error?: string | null;
}

export interface TripRequest {
  destination: string;
  days: number;
  budget: number;
  travelers: number;
  food_preference: string;
  senior_citizen: boolean;
}

export interface ScoredAttraction {
  place_id: string;
  name: string;
  score: number;
  rating: number | null;
  category: string | null;
  city: string | null;
  description: string | null;
  reasons: string[];
}

export interface ScoredRestaurant {
  place_id: string;
  name: string;
  score: number;
  rating: number | null;
  vegetarian: boolean;
  price_level: number | null;
  reasons: string[];
}

export interface WeatherForecast {
  city: string;
  date: string;
  temperature: number | null;
  condition: string | null;
}

export interface TripGenerateData {
  trip_id: number | null;
  itinerary_id: number | null;
  destination: string;
  attractions: ScoredAttraction[];
  restaurants: ScoredRestaurant[];
  weather: WeatherForecast[];
  itinerary: string | null;
  message: string;
}

export interface CityAnalytics {
  city: string;
  total_attractions: number;
  total_restaurants: number;
  average_rating: number;
  last_updated: string | null;
}

export interface ChatData {
  answer: string;
}

export interface HealthData {
  status: string;
  database: string;
  groq: string;
  cache: string;
  version: string;
}


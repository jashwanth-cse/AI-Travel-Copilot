import { AxiosError } from "axios";
import { motion } from "framer-motion";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { getCityAnalytics, generateTrip } from "../api/client";
import { fadeUp, PageTransition, staggerContainer } from "../components/motion/PageTransition";
import { LoadingScreen } from "../components/travel/LoadingScreen";
import { ErrorState } from "../components/travel/StateBlocks";
import { TripForm } from "../components/travel/TripForm";
import { Card, CardContent } from "../components/ui/Card";
import { saveTripResult } from "../lib/storage";
import type { TripRequest } from "../types/api";

export function PlannerPage() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate(payload: TripRequest) {
    setIsLoading(true);
    setError(null);

    try {
      const tripResponse = await generateTrip(payload);
      const analyticsResponse = await getCityAnalytics(payload.destination);

      saveTripResult({
        trip: payload,
        result: tripResponse.data,
        analytics: analyticsResponse.data,
        createdAt: new Date().toISOString(),
      });

      navigate("/results");
    } catch (requestError) {
      const axiosError = requestError as AxiosError<{ message?: string; error?: string }>;
      setError(
        axiosError.response?.data?.error ??
          axiosError.response?.data?.message ??
          axiosError.message ??
          "Trip generation failed",
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <PageTransition>
      <section className="mx-auto grid max-w-7xl gap-8 px-4 py-10 sm:px-6 lg:grid-cols-[0.9fr_1.1fr] lg:px-8">
        <motion.div variants={staggerContainer} initial="hidden" animate="show" className="space-y-5">
          <motion.div variants={fadeUp}>
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-primary">Trip cockpit</p>
            <h1 className="mt-3 text-4xl font-black tracking-tight sm:text-5xl">Turn a destination into a complete plan.</h1>
            <p className="mt-4 text-muted-foreground">
              The backend refreshes cached city data when needed, scores travel options, and returns a structured AI itinerary.
            </p>
          </motion.div>
          <motion.div variants={fadeUp}>
            <Card>
              <CardContent className="grid gap-4 p-5 text-sm text-muted-foreground">
                <Stat label="Cache window" value="24h" />
                <Stat label="AI model" value="Groq" />
                <Stat label="Storage" value="SQLite" />
              </CardContent>
            </Card>
          </motion.div>
        </motion.div>
        <div className="space-y-5">
          <TripForm onSubmit={handleGenerate} isLoading={isLoading} />
          {error ? <ErrorState message={error} /> : null}
          {isLoading ? <LoadingScreen /> : null}
        </div>
      </section>
    </PageTransition>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between rounded-md bg-secondary px-3 py-2">
      <span>{label}</span>
      <span className="font-semibold text-foreground">{value}</span>
    </div>
  );
}


import { motion } from "framer-motion";
import { ArrowRight, RefreshCcw } from "lucide-react";
import { Link } from "react-router-dom";
import { PageTransition, fadeUp, staggerContainer } from "../components/motion/PageTransition";
import { AnalyticsCard } from "../components/travel/AnalyticsCard";
import { AttractionCard } from "../components/travel/AttractionCard";
import { BudgetCard } from "../components/travel/BudgetCard";
import { ChatWidget } from "../components/travel/ChatWidget";
import { EmptyState } from "../components/travel/StateBlocks";
import { ItineraryTimeline } from "../components/travel/ItineraryTimeline";
import { RestaurantCard } from "../components/travel/RestaurantCard";
import { WeatherCard } from "../components/travel/WeatherCard";
import { Button } from "../components/ui/Button";
import { loadTripResult } from "../lib/storage";

export function ResultsPage() {
  const stored = loadTripResult();

  if (!stored) {
    return (
      <PageTransition>
        <section className="mx-auto max-w-4xl px-4 py-16 sm:px-6 lg:px-8">
          <EmptyState title="No trip result yet" text="Generate a trip from the planner to populate this dashboard with backend data." />
          <div className="mt-5">
            <Link to="/planner">
              <Button>
                Open planner
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>
        </section>
      </PageTransition>
    );
  }

  const { trip, result, analytics } = stored;

  return (
    <PageTransition>
      <section className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-8 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-primary">Results dashboard</p>
            <h1 className="mt-2 text-4xl font-black tracking-tight">{result.destination}</h1>
            <p className="mt-2 text-muted-foreground">{result.message}</p>
          </div>
          <Link to="/planner">
            <Button variant="outline">
              <RefreshCcw className="h-4 w-4" />
              New trip
            </Button>
          </Link>
        </div>

        <motion.div variants={staggerContainer} initial="hidden" animate="show" className="grid gap-5 lg:grid-cols-3">
          <motion.div variants={fadeUp}>
            <WeatherCard weather={result.weather} />
          </motion.div>
          <motion.div variants={fadeUp}>
            <BudgetCard trip={trip} />
          </motion.div>
          <motion.div variants={fadeUp}>
            <AnalyticsCard analytics={analytics} />
          </motion.div>
        </motion.div>

        <div className="mt-8 grid gap-8 xl:grid-cols-[1.2fr_0.8fr]">
          <div className="space-y-8">
            <section>
              <SectionTitle title="Attractions" />
              {result.attractions.length ? (
                <div className="grid gap-4 md:grid-cols-2">
                  {result.attractions.map((item, index) => (
                    <AttractionCard key={item.place_id} attraction={item} index={index} />
                  ))}
                </div>
              ) : (
                <EmptyState title="No attractions" text="The backend did not return attraction recommendations for this trip." />
              )}
            </section>

            <section>
              <SectionTitle title="Restaurants" />
              {result.restaurants.length ? (
                <div className="grid gap-4 md:grid-cols-2">
                  {result.restaurants.map((item, index) => (
                    <RestaurantCard key={item.place_id} restaurant={item} index={index} />
                  ))}
                </div>
              ) : (
                <EmptyState title="No restaurants" text="The backend did not return restaurant recommendations for this trip." />
              )}
            </section>
          </div>

          <aside className="space-y-6">
            <ItineraryTimeline itinerary={result.itinerary} />
            <ChatWidget />
          </aside>
        </div>
      </section>
    </PageTransition>
  );
}

function SectionTitle({ title }: { title: string }) {
  return <h2 className="mb-4 text-2xl font-bold tracking-tight">{title}</h2>;
}


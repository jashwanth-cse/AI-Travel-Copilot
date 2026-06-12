import { motion } from "framer-motion";
import { ArrowRight, Brain, Database, MapPinned, Plane, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";
import { PageTransition, fadeUp, staggerContainer } from "../components/motion/PageTransition";
import { Button } from "../components/ui/Button";
import { Card, CardContent } from "../components/ui/Card";

export function LandingPage() {
  return (
    <PageTransition>
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 -z-10">
          <img
            src="https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1800&q=80"
            alt=""
            className="h-full w-full object-cover"
          />
          <div className="absolute inset-0 bg-slate-950/55" />
        </div>
        <div className="mx-auto grid min-h-[calc(100vh-4rem)] max-w-7xl content-center px-4 py-16 sm:px-6 lg:px-8">
          <motion.div variants={staggerContainer} initial="hidden" animate="show" className="max-w-3xl text-white">
            <motion.div variants={fadeUp} className="mb-5 inline-flex items-center gap-2 rounded-md bg-white/15 px-3 py-2 text-sm backdrop-blur">
              <Sparkles className="h-4 w-4" />
              AI itinerary generation with live travel data
            </motion.div>
            <motion.h1 variants={fadeUp} className="text-5xl font-black leading-tight sm:text-6xl lg:text-7xl">
              AI Travel Copilot
            </motion.h1>
            <motion.p variants={fadeUp} className="mt-6 max-w-2xl text-lg leading-8 text-white/85">
              Plan city trips with cached ETL data, scored recommendations, weather context, and a Groq-powered itinerary.
            </motion.p>
            <motion.div variants={fadeUp} className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link to="/planner">
                <Button size="lg">
                  Start planning
                  <ArrowRight className="h-5 w-5" />
                </Button>
              </Link>
              <Link to="/results">
                <Button size="lg" variant="outline" className="border-white/30 bg-white/10 text-white hover:bg-white/20">
                  View dashboard
                </Button>
              </Link>
            </motion.div>
          </motion.div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="grid gap-4 md:grid-cols-3">
          {[
            { icon: Database, title: "Cache-aware ETL", text: "SQLite freshness checks keep repeated trip requests fast." },
            { icon: Brain, title: "AI planning", text: "Recommendations become reusable prompts for itinerary generation." },
            { icon: MapPinned, title: "Travel dashboard", text: "Weather, analytics, restaurants, and attractions stay together." },
          ].map((item) => (
            <motion.div key={item.title} whileHover={{ y: -4, scale: 1.01 }}>
              <Card className="h-full">
                <CardContent className="p-6">
                  <item.icon className="h-8 w-8 text-primary" />
                  <h2 className="mt-5 text-xl font-bold">{item.title}</h2>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">{item.text}</p>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
        <div className="mt-8 flex items-center gap-3 rounded-lg border bg-card p-4 text-sm text-muted-foreground">
          <Plane className="h-5 w-5 text-primary" />
          <span>Backend APIs only. No frontend mock data.</span>
        </div>
      </section>
    </PageTransition>
  );
}


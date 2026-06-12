import { CalendarDays, Clock, Map } from "lucide-react";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";
import { Badge } from "../ui/Badge";

interface TimelineDay {
  title: string;
  body: string[];
}

interface ItineraryTimelineProps {
  itinerary: string | null;
}

export function parseItinerary(text: string | null): TimelineDay[] {
  if (!text) {
    return [];
  }

  const lines = text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  const days: TimelineDay[] = [];
  let current: TimelineDay | null = null;

  for (const line of lines) {
    const plain = line.replace(/^#+\s*/, "").replace(/\*\*/g, "");
    if (/^day\s+\d+/i.test(plain)) {
      if (current) {
        days.push(current);
      }
      current = { title: plain.replace(/^[-*]\s*/, ""), body: [] };
      continue;
    }

    if (!current) {
      current = { title: "Trip overview", body: [] };
    }
    current.body.push(plain.replace(/^[-*]\s*/, ""));
  }

  if (current) {
    days.push(current);
  }

  return days;
}

export function ItineraryTimeline({ itinerary }: ItineraryTimelineProps) {
  const days = parseItinerary(itinerary);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CalendarDays className="h-5 w-5 text-primary" />
          Itinerary
        </CardTitle>
      </CardHeader>
      <CardContent>
        {days.length ? (
          <div className="relative space-y-4">
            <div className="absolute left-5 top-2 h-[calc(100%-1rem)] w-px bg-border" />
            {days.map((day, index) => (
              <motion.article
                key={`${day.title}-${index}`}
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.08 }}
                className="relative grid grid-cols-[2.5rem_1fr] gap-3"
              >
                <div className="z-10 flex h-10 w-10 items-center justify-center rounded-md bg-primary text-primary-foreground">
                  <Map className="h-5 w-5" />
                </div>
                <div className="rounded-lg border bg-background p-4">
                  <div className="mb-3 flex flex-wrap items-center gap-2">
                    <h3 className="font-semibold">{day.title}</h3>
                    <Badge>
                      <Clock className="mr-1 h-3 w-3" />
                      Day {index + 1}
                    </Badge>
                  </div>
                  <ul className="space-y-2 text-sm text-muted-foreground">
                    {day.body.slice(0, 8).map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
              </motion.article>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">No itinerary returned yet.</p>
        )}
      </CardContent>
    </Card>
  );
}


import { MapPin, Sparkles, Star } from "lucide-react";
import { motion } from "framer-motion";
import { ScoredAttraction } from "../../types/api";
import { Badge } from "../ui/Badge";
import { Card, CardContent } from "../ui/Card";

const attractionImages = [
  "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=900&q=80",
  "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=900&q=80",
  "https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=900&q=80",
];

interface AttractionCardProps {
  attraction: ScoredAttraction;
  index: number;
}

export function AttractionCard({ attraction, index }: AttractionCardProps) {
  return (
    <motion.div whileHover={{ y: -4, scale: 1.01 }} transition={{ duration: 0.2 }}>
      <Card className="h-full overflow-hidden">
        <img
          src={attractionImages[index % attractionImages.length]}
          alt=""
          className="h-40 w-full object-cover"
          loading="lazy"
        />
        <CardContent className="space-y-3 p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h3 className="font-semibold">{attraction.name}</h3>
              <p className="mt-1 flex items-center gap-1 text-sm text-muted-foreground">
                <MapPin className="h-4 w-4" />
                {attraction.city ?? "Destination"}
              </p>
            </div>
            <Badge>
              <Star className="mr-1 h-3 w-3" />
              {attraction.score}
            </Badge>
          </div>
          <p className="line-clamp-3 text-sm text-muted-foreground">{attraction.description ?? attraction.category}</p>
          <div className="flex flex-wrap gap-2">
            {(attraction.reasons.length ? attraction.reasons : [attraction.category ?? "recommended"]).slice(0, 2).map((reason) => (
              <Badge key={reason} className="bg-primary/10 text-primary">
                <Sparkles className="mr-1 h-3 w-3" />
                {reason.replace(/_/g, " ")}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

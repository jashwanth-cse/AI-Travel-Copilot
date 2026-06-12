import { Leaf, Star, Utensils } from "lucide-react";
import { motion } from "framer-motion";
import { ScoredRestaurant } from "../../types/api";
import { Badge } from "../ui/Badge";
import { Card, CardContent } from "../ui/Card";

const restaurantImages = [
  "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=900&q=80",
  "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=900&q=80",
  "https://images.unsplash.com/photo-1551218808-94e220e084d2?auto=format&fit=crop&w=900&q=80",
];

interface RestaurantCardProps {
  restaurant: ScoredRestaurant;
  index: number;
}

export function RestaurantCard({ restaurant, index }: RestaurantCardProps) {
  return (
    <motion.div whileHover={{ y: -4, scale: 1.01 }} transition={{ duration: 0.2 }}>
      <Card className="h-full overflow-hidden">
        <img
          src={restaurantImages[index % restaurantImages.length]}
          alt=""
          className="h-36 w-full object-cover"
          loading="lazy"
        />
        <CardContent className="space-y-3 p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h3 className="font-semibold">{restaurant.name}</h3>
              <p className="mt-1 flex items-center gap-1 text-sm text-muted-foreground">
                <Utensils className="h-4 w-4" />
                Price level {restaurant.price_level ?? "standard"}
              </p>
            </div>
            <Badge>
              <Star className="mr-1 h-3 w-3" />
              {restaurant.score}
            </Badge>
          </div>
          <div className="flex flex-wrap gap-2">
            {restaurant.vegetarian ? (
              <Badge className="bg-emerald-50 text-emerald-700">
                <Leaf className="mr-1 h-3 w-3" />
                Vegetarian
              </Badge>
            ) : null}
            {restaurant.reasons.slice(0, 2).map((reason) => (
              <Badge key={reason}>{reason.replace(/_/g, " ")}</Badge>
            ))}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

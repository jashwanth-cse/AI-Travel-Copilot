import { motion } from "framer-motion";
import { Plane } from "lucide-react";
import { Skeleton } from "../ui/Skeleton";

export function LoadingScreen() {
  return (
    <div className="grid gap-6">
      <motion.div
        className="flex items-center justify-center gap-3 rounded-lg border bg-card p-6"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        <motion.span
          animate={{ y: [0, -8, 0] }}
          transition={{ repeat: Infinity, duration: 1.2 }}
          className="flex h-12 w-12 items-center justify-center rounded-md bg-primary text-primary-foreground"
        >
          <Plane className="h-6 w-6" />
        </motion.span>
        <div>
          <p className="font-semibold">Building your trip</p>
          <p className="text-sm text-muted-foreground">Fetching cached data, recommendations, and AI plan.</p>
        </div>
      </motion.div>
      <div className="grid gap-4 md:grid-cols-3">
        <Skeleton className="h-44" />
        <Skeleton className="h-44" />
        <Skeleton className="h-44" />
      </div>
    </div>
  );
}


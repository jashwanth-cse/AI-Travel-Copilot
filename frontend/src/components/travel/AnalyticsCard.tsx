import { BarChart3, Clock3, Star } from "lucide-react";
import { ReactNode } from "react";
import { CityAnalytics } from "../../types/api";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";

interface AnalyticsCardProps {
  analytics: CityAnalytics | null;
}

export function AnalyticsCard({ analytics }: AnalyticsCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-primary" />
          Analytics
        </CardTitle>
      </CardHeader>
      <CardContent>
        {analytics ? (
          <div className="grid gap-3">
            <div className="grid grid-cols-3 gap-2">
              <Metric label="Attractions" value={analytics.total_attractions} />
              <Metric label="Restaurants" value={analytics.total_restaurants} />
              <Metric label="Rating" value={analytics.average_rating} icon={<Star className="h-4 w-4" />} />
            </div>
            <p className="flex items-center gap-2 text-xs text-muted-foreground">
              <Clock3 className="h-4 w-4" />
              {analytics.last_updated ? new Date(analytics.last_updated).toLocaleString() : "No cache timestamp"}
            </p>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">Analytics unavailable.</p>
        )}
      </CardContent>
    </Card>
  );
}

function Metric({ label, value, icon }: { label: string; value: number; icon?: ReactNode }) {
  return (
    <div className="rounded-md bg-secondary p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 flex items-center gap-1 text-lg font-bold">
        {icon}
        {value}
      </p>
    </div>
  );
}

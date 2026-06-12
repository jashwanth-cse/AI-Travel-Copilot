import { CloudRain, SunMedium, Thermometer } from "lucide-react";
import { WeatherForecast } from "../../types/api";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";

interface WeatherCardProps {
  weather: WeatherForecast[];
}

export function WeatherCard({ weather }: WeatherCardProps) {
  const primary = weather[0];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CloudRain className="h-5 w-5 text-primary" />
          Weather
        </CardTitle>
      </CardHeader>
      <CardContent>
        {primary ? (
          <div className="space-y-4">
            <div className="flex items-end justify-between">
              <div>
                <p className="text-sm text-muted-foreground">{primary.city}</p>
                <p className="text-3xl font-bold">{primary.temperature ?? "--"} C</p>
              </div>
              <SunMedium className="h-10 w-10 text-accent" />
            </div>
            <div className="grid gap-2">
              {weather.slice(0, 5).map((item) => (
                <div key={`${item.city}-${item.date}`} className="flex items-center justify-between rounded-md bg-secondary px-3 py-2 text-sm">
                  <span>{new Date(item.date).toLocaleDateString()}</span>
                  <span className="flex items-center gap-2 text-muted-foreground">
                    <Thermometer className="h-4 w-4" />
                    {item.condition ?? "Forecast"}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">No weather records returned.</p>
        )}
      </CardContent>
    </Card>
  );
}


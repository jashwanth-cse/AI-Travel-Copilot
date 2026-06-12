import { FormEvent, useState } from "react";
import { ArrowRight, Loader2, Users } from "lucide-react";
import { TripRequest } from "../../types/api";
import { Button } from "../ui/Button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/Card";
import { Input } from "../ui/Input";
import { Label } from "../ui/Label";

interface TripFormProps {
  onSubmit: (payload: TripRequest) => Promise<void> | void;
  isLoading?: boolean;
}

export function TripForm({ onSubmit, isLoading = false }: TripFormProps) {
  const [form, setForm] = useState<TripRequest>({
    destination: "Ooty",
    days: 3,
    budget: 15000,
    travelers: 2,
    food_preference: "vegetarian",
    senior_citizen: true,
  });

  function updateField<K extends keyof TripRequest>(key: K, value: TripRequest[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSubmit(form);
  }

  return (
    <Card className="overflow-hidden">
      <CardHeader>
        <CardTitle>Trip Planner</CardTitle>
        <CardDescription>Live data, local cache, AI itinerary.</CardDescription>
      </CardHeader>
      <CardContent>
        <form className="grid gap-4" onSubmit={handleSubmit}>
          <div className="grid gap-2">
            <Label htmlFor="destination">Destination</Label>
            <Input
              id="destination"
              value={form.destination}
              onChange={(event) => updateField("destination", event.target.value)}
              required
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="grid gap-2">
              <Label htmlFor="days">Days</Label>
              <Input
                id="days"
                type="number"
                min={1}
                value={form.days}
                onChange={(event) => updateField("days", Number(event.target.value))}
                required
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="budget">Budget</Label>
              <Input
                id="budget"
                type="number"
                min={0}
                value={form.budget}
                onChange={(event) => updateField("budget", Number(event.target.value))}
                required
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="travelers">Travelers</Label>
              <div className="relative">
                <Users className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  id="travelers"
                  className="pl-9"
                  type="number"
                  min={1}
                  value={form.travelers}
                  onChange={(event) => updateField("travelers", Number(event.target.value))}
                  required
                />
              </div>
            </div>
          </div>
          <div className="grid gap-4 sm:grid-cols-[1fr_auto] sm:items-end">
            <div className="grid gap-2">
              <Label htmlFor="food">Food preference</Label>
              <Input
                id="food"
                value={form.food_preference}
                onChange={(event) => updateField("food_preference", event.target.value)}
                required
              />
            </div>
            <label className="flex h-11 items-center gap-3 rounded-md border px-3 text-sm font-medium">
              <input
                type="checkbox"
                className="h-4 w-4 accent-primary"
                checked={form.senior_citizen}
                onChange={(event) => updateField("senior_citizen", event.target.checked)}
              />
              Senior mode
            </label>
          </div>
          <Button type="submit" size="lg" disabled={isLoading}>
            {isLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : <ArrowRight className="h-5 w-5" />}
            Generate itinerary
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}


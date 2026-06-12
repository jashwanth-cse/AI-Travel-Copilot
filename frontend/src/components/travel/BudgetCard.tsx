import { CircleDollarSign, Users } from "lucide-react";
import { TripRequest } from "../../types/api";
import { formatCurrency } from "../../lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";

interface BudgetCardProps {
  trip: TripRequest;
}

export function BudgetCard({ trip }: BudgetCardProps) {
  const perPerson = trip.budget / Math.max(trip.travelers, 1);
  const perDay = trip.budget / Math.max(trip.days, 1);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CircleDollarSign className="h-5 w-5 text-primary" />
          Budget
        </CardTitle>
      </CardHeader>
      <CardContent className="grid gap-4">
        <div>
          <p className="text-sm text-muted-foreground">Total</p>
          <p className="text-3xl font-bold">{formatCurrency(trip.budget)}</p>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-md bg-secondary p-3">
            <p className="text-xs text-muted-foreground">Per person</p>
            <p className="font-semibold">{formatCurrency(perPerson)}</p>
          </div>
          <div className="rounded-md bg-secondary p-3">
            <p className="text-xs text-muted-foreground">Per day</p>
            <p className="font-semibold">{formatCurrency(perDay)}</p>
          </div>
        </div>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Users className="h-4 w-4" />
          {trip.travelers} travelers
        </div>
      </CardContent>
    </Card>
  );
}


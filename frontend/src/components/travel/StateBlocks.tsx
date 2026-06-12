import { AlertTriangle, Inbox } from "lucide-react";
import { Card, CardContent } from "../ui/Card";

export function EmptyState({ title, text }: { title: string; text: string }) {
  return (
    <Card>
      <CardContent className="flex items-start gap-3 p-6">
        <Inbox className="mt-1 h-5 w-5 text-primary" />
        <div>
          <h3 className="font-semibold">{title}</h3>
          <p className="mt-1 text-sm text-muted-foreground">{text}</p>
        </div>
      </CardContent>
    </Card>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <Card className="border-destructive/30 bg-destructive/5">
      <CardContent className="flex items-start gap-3 p-6">
        <AlertTriangle className="mt-1 h-5 w-5 text-destructive" />
        <div>
          <h3 className="font-semibold text-destructive">Request failed</h3>
          <p className="mt-1 text-sm text-muted-foreground">{message}</p>
        </div>
      </CardContent>
    </Card>
  );
}


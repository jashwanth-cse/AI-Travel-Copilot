import { Github, MapPinned, ShieldCheck } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t bg-card/70">
      <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-8 text-sm text-muted-foreground sm:px-6 md:flex-row md:items-center md:justify-between lg:px-8">
        <div className="flex items-center gap-2">
          <MapPinned className="h-4 w-4 text-primary" />
          <span>AI Travel Copilot</span>
        </div>
        <div className="flex flex-wrap items-center gap-4">
          <span className="inline-flex items-center gap-2">
            <ShieldCheck className="h-4 w-4" />
            SQLite cached
          </span>
          <span className="inline-flex items-center gap-2">
            <Github className="h-4 w-4" />
            MVP backend connected
          </span>
        </div>
      </div>
    </footer>
  );
}


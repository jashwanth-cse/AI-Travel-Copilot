import { FormEvent, useState } from "react";
import { Bot, Loader2, Send, User } from "lucide-react";
import { askTravelAssistant } from "../../api/client";
import { Button } from "../ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";
import { Textarea } from "../ui/Textarea";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
}

export function ChatWidget() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = message.trim();
    if (!trimmed) {
      return;
    }

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
    };
    setMessages((current) => [...current, userMessage]);
    setMessage("");
    setError(null);
    setIsLoading(true);

    try {
      const response = await askTravelAssistant(trimmed);
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: response.data.answer,
        },
      ]);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Chat request failed");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Bot className="h-5 w-5 text-primary" />
          AI Assistant
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="max-h-80 space-y-3 overflow-y-auto rounded-md border bg-background p-3">
          {messages.length ? (
            messages.map((item) => (
              <div key={item.id} className="flex gap-2">
                <span className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-secondary">
                  {item.role === "assistant" ? <Bot className="h-4 w-4" /> : <User className="h-4 w-4" />}
                </span>
                <p className="rounded-md bg-secondary px-3 py-2 text-sm leading-6">{item.content}</p>
              </div>
            ))
          ) : (
            <p className="text-sm text-muted-foreground">Ask about timing, food, weather, or route comfort.</p>
          )}
          {isLoading ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Thinking
            </div>
          ) : null}
        </div>
        {error ? <p className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">{error}</p> : null}
        <form className="grid gap-3" onSubmit={handleSubmit}>
          <Textarea value={message} onChange={(event) => setMessage(event.target.value)} />
          <Button type="submit" disabled={isLoading}>
            <Send className="h-4 w-4" />
            Send
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}


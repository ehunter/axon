import { cn } from "@/lib/utils";

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
}

export function ChatMessage({ role, content }: ChatMessageProps) {
  const isUser = role === "user";

  return (
    <div
      data-message-container
      className={cn(
        "flex w-full",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      <div
        data-message-bubble
        className={cn(
          "px-4 py-2.5",
          isUser
            ? "max-w-[65%] bg-secondary border border-border rounded-2xl rounded-tr-sm"
            : "w-full text-foreground"
        )}
      >
        <p className="text-base leading-6 text-foreground whitespace-pre-wrap">
          {content}
        </p>
      </div>
    </div>
  );
}


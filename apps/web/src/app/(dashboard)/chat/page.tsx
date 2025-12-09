"use client";

import { useRef, useEffect } from "react";
import { AlertCircle } from "lucide-react";
import { ChatMessage, ChatInput, ChatHeader } from "@/components/chat";
import { useChatStream } from "@/hooks/use-chat-stream";

export default function ChatPage() {
  const {
    messages,
    isLoading,
    isStreaming,
    error,
    sendMessage,
  } = useChatStream();

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex flex-col h-full">
      {/* Main container with rounded top corners */}
      <div className="flex-1 flex flex-col bg-surface rounded-tl-3xl rounded-tr-3xl shadow-sm overflow-hidden">
        {/* Header */}
        <ChatHeader
          title="New Chat"
          onDropdownClick={() => {
            // TODO: Open conversation switcher
          }}
        />

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto px-10 scrollbar-thin">
          <div className="max-w-[640px] mx-auto space-y-11 py-6">
            {/* Empty state */}
            {messages.length === 0 && !isLoading && (
              <div className="text-center py-20">
                <h2 className="text-2xl font-light text-foreground mb-2">
                  What can I help you with?
                </h2>
                <p className="text-muted-foreground">
                  Ask me about brain tissue samples, diagnoses, or research criteria.
                </p>
              </div>
            )}

            {/* Messages */}
            {messages.map((message) => (
              <ChatMessage
                key={message.id}
                role={message.role}
                content={message.content}
              />
            ))}

            {/* Loading indicator */}
            {isLoading && !isStreaming && messages[messages.length - 1]?.content === "" && (
              <div className="flex justify-start">
                <div className="text-muted-foreground flex items-center gap-2">
                  <span className="animate-pulse">Thinking...</span>
                </div>
              </div>
            )}

            {/* Error message */}
            {error && (
              <div className="flex items-center gap-2 text-destructive bg-destructive/10 rounded-lg p-4">
                <AlertCircle className="h-5 w-5 flex-shrink-0" />
                <p className="text-base">{error}</p>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Footer with input */}
        <div className="px-10 py-8">
          <div className="max-w-[608px] mx-auto space-y-4">
            <ChatInput onSend={sendMessage} disabled={isLoading} />
            <p className="text-base text-muted-foreground text-center">
              Axon is in Beta and can make mistakes. Please check your tissue
              recommendations
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

"use client";

import { useRef, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { AlertCircle } from "lucide-react";
import { ChatMessage, ChatInput, ChatHeader, type ChatInputRef } from "@/components/chat";
import { useChatStream } from "@/hooks/use-chat-stream";

function ChatPageContent() {
  const {
    messages,
    isLoading,
    isStreaming,
    error,
    sendMessage,
  } = useChatStream();

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatInputRef = useRef<ChatInputRef>(null);
  const searchParams = useSearchParams();
  const router = useRouter();
  const initialMessageSent = useRef(false);
  const wasLoading = useRef(false);

  // Handle initial message from URL query param
  useEffect(() => {
    const initialMessage = searchParams.get("message");
    if (initialMessage && !initialMessageSent.current && messages.length === 0) {
      initialMessageSent.current = true;
      // Clear the URL param
      router.replace("/chat", { scroll: false });
      // Send the message
      sendMessage(initialMessage);
    }
  }, [searchParams, messages.length, sendMessage, router]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Auto-focus input after agent finishes responding
  useEffect(() => {
    if (wasLoading.current && !isLoading) {
      // Loading just finished, focus the input
      chatInputRef.current?.focus();
    }
    wasLoading.current = isLoading;
  }, [isLoading]);

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
            <ChatInput ref={chatInputRef} onSend={sendMessage} disabled={isLoading} />
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

export default function ChatPage() {
  return (
    <Suspense fallback={<ChatPageLoading />}>
      <ChatPageContent />
    </Suspense>
  );
}

function ChatPageLoading() {
  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 flex flex-col bg-surface rounded-tl-3xl rounded-tr-3xl shadow-sm overflow-hidden">
        <div className="flex items-center justify-center h-full">
          <p className="text-muted-foreground animate-pulse">Loading...</p>
        </div>
      </div>
    </div>
  );
}

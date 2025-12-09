"use client";

import { Suspense, useEffect, useRef, useState, type FC, forwardRef } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { ChatHeader } from "@/components/chat";
import { useAxonRuntime } from "@/lib/assistant-ui/use-axon-runtime";
import {
  AssistantRuntimeProvider,
  ThreadPrimitive,
  ComposerPrimitive,
  MessagePrimitive,
  useMessagePartText,
  useMessage,
  useThread,
} from "@assistant-ui/react";
import { ArrowUp, Square } from "lucide-react";
import { cn } from "@/lib/utils";

function ChatPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const initialMessageSent = useRef(false);
  const loadedConversationId = useRef<string | null>(null);
  const { runtime, messages, sendInitialMessage, loadConversation, clearMessages } = useAxonRuntime();
  const [conversationTitle, setConversationTitle] = useState<string | null>(null);

  // Handle loading existing conversation from URL
  useEffect(() => {
    const conversationId = searchParams.get("id");
    
    // If conversation ID changed, load the new conversation
    if (conversationId && conversationId !== loadedConversationId.current) {
      loadedConversationId.current = conversationId;
      // Load the existing conversation
      loadConversation(conversationId).then((result) => {
        if (result) {
          setConversationTitle(result.title);
        }
      });
    } else if (!conversationId && loadedConversationId.current) {
      // URL changed to new chat - clear messages
      loadedConversationId.current = null;
      clearMessages();
      setConversationTitle(null);
    }
  }, [searchParams, loadConversation, clearMessages]);

  // Handle initial message from URL query param (for new chats)
  useEffect(() => {
    const initialMessage = searchParams.get("message");
    const conversationId = searchParams.get("id");
    if (initialMessage && !initialMessageSent.current && messages.length === 0 && !conversationId) {
      initialMessageSent.current = true;
      // Clear the URL param
      router.replace("/chat", { scroll: false });
      // Send the initial message through the runtime
      sendInitialMessage(initialMessage);
    }
  }, [searchParams, messages.length, router, sendInitialMessage]);

  return (
    <div className="flex flex-col h-full">
      {/* Main container with rounded top corners */}
      <div className="flex-1 flex flex-col bg-surface rounded-tl-3xl rounded-tr-3xl shadow-sm overflow-hidden">
        {/* Header */}
        <ChatHeader
          title={conversationTitle || "New Chat"}
          onDropdownClick={() => {
            // TODO: Open conversation switcher
          }}
        />

        {/* Thread from assistant-ui */}
        <AssistantRuntimeProvider runtime={runtime}>
          <ThreadPrimitive.Root className="flex flex-col flex-1 overflow-hidden">
            {/* Messages area with auto-scroll */}
            <ThreadPrimitive.Viewport className="flex-1 overflow-y-auto px-10 scrollbar-thin">
              <div className="max-w-[640px] mx-auto space-y-11 py-6">
                {/* Empty state */}
                <ThreadPrimitive.Empty>
                  <div className="text-center py-20">
                    <h2 className="text-2xl font-light text-foreground mb-2">
                      What can I help you with?
                    </h2>
                    <p className="text-muted-foreground">
                      Ask me about brain tissue samples, diagnoses, or research criteria.
                    </p>
                  </div>
                </ThreadPrimitive.Empty>

                {/* Messages */}
                <ThreadPrimitive.Messages
                  components={{
                    UserMessage,
                    AssistantMessage,
                  }}
                />
              </div>
            </ThreadPrimitive.Viewport>

            {/* Footer with input */}
            <div className="px-10 py-8">
              <div className="max-w-[608px] mx-auto space-y-4">
                <Composer />
                <p className="text-base text-muted-foreground text-center">
                  Axon is in Beta and can make mistakes. Please check your tissue
                  recommendations
                </p>
              </div>
            </div>
          </ThreadPrimitive.Root>
        </AssistantRuntimeProvider>
      </div>
    </div>
  );
}

/**
 * User message bubble - right aligned with secondary background
 */
const UserMessage: FC = () => {
  return (
    <MessagePrimitive.Root className="flex w-full justify-end">
      <div className="max-w-[65%] px-4 py-2.5 bg-secondary border border-border rounded-2xl rounded-tr-sm">
        <MessagePrimitive.Content
          components={{
            Text: UserMessageText,
          }}
        />
      </div>
    </MessagePrimitive.Root>
  );
};

const UserMessageText: FC = () => {
  const part = useMessagePartText();
  const text = part.type === "text" ? part.text : "";
  return (
    <p className="text-base leading-6 text-foreground whitespace-pre-wrap">
      {text}
    </p>
  );
};

/**
 * Assistant message - left aligned, full width
 * Shows "Thinking..." when message is running with no content
 */
const AssistantMessage: FC = () => {
  const message = useMessage();
  const isRunning = message.status?.type === "running";
  const hasContent = message.content.some(
    (part) => part.type === "text" && (part as { text: string }).text.length > 0
  );

  return (
    <MessagePrimitive.Root className="flex w-full justify-start">
      <div className="w-full px-4 py-2.5">
        {/* Show "Thinking..." when running with no content */}
        {isRunning && !hasContent && (
          <span className="text-muted-foreground animate-pulse">Thinking...</span>
        )}
        
        {/* Show content when available */}
        {hasContent && (
          <MessagePrimitive.Content
            components={{
              Text: AssistantMessageText,
            }}
          />
        )}
      </div>
    </MessagePrimitive.Root>
  );
};

const AssistantMessageText: FC = () => {
  const part = useMessagePartText();
  const text = part.type === "text" ? part.text : "";
  return (
    <p className="text-base leading-6 text-foreground whitespace-pre-wrap">
      {text}
    </p>
  );
};

/**
 * Composer - chat input with send button
 * Shows cancel button when thread is running
 */
const Composer: FC = () => {
  const isRunning = useThread((state) => state.isRunning);

  return (
    <ComposerPrimitive.Root className="flex items-center justify-between bg-input rounded-full px-5 py-4 shadow-sm">
      <ComposerPrimitive.Input
        autoFocus
        placeholder="Ask anything"
        className="flex-1 bg-transparent text-base text-foreground placeholder:text-muted-foreground focus:outline-none resize-none max-h-[200px]"
        submitOnEnter
      />
      
      {/* Show Cancel button when running, Send button otherwise */}
      {isRunning ? (
        <ComposerPrimitive.Cancel asChild>
          <button
            type="button"
            className="flex items-center justify-center rounded-full p-1 bg-foreground text-background transition-colors"
            aria-label="Cancel"
          >
            <Square className="h-5 w-5" />
          </button>
        </ComposerPrimitive.Cancel>
      ) : (
        <ComposerPrimitive.Send asChild>
          <SendButton />
        </ComposerPrimitive.Send>
      )}
    </ComposerPrimitive.Root>
  );
};

/**
 * Send button that changes style based on whether there's content
 */
const SendButton = forwardRef<HTMLButtonElement, React.ComponentPropsWithoutRef<"button">>(
  ({ disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        type="button"
        disabled={disabled}
        aria-label="Send message"
        className={cn(
          "flex items-center justify-center rounded-full p-1 transition-colors",
          disabled
            ? "bg-muted text-muted-foreground"
            : "bg-foreground text-background"
        )}
        {...props}
      >
        <ArrowUp className="h-5 w-5" />
      </button>
    );
  }
);
SendButton.displayName = "SendButton";

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

"use client";

import {
  useExternalStoreRuntime,
  ThreadMessageLike,
  AppendMessage,
} from "@assistant-ui/react";
import { useState, useCallback, useRef } from "react";

interface StreamEvent {
  type: "text" | "tool_start" | "tool_end" | "done" | "error" | "conversation_id";
  content: string;
  tool_input?: Record<string, unknown>;
}

interface AxonMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
}

// Store conversation ID in module scope so it persists across re-renders
let currentConversationId: string | null = null;

/**
 * Custom runtime adapter for Axon's SSE chat backend
 */
export function useAxonRuntime() {
  const [messages, setMessages] = useState<AxonMessage[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Convert our messages to assistant-ui format
  const threadMessages: ThreadMessageLike[] = messages.map((msg) => ({
    id: msg.id,
    role: msg.role,
    content: [{ type: "text" as const, text: msg.content }],
  }));

  const onNew = useCallback(async (message: AppendMessage) => {
    // Extract text content from the message
    const textContent = message.content
      .filter((c): c is { type: "text"; text: string } => c.type === "text")
      .map((c) => c.text)
      .join("");

    if (!textContent.trim()) return;

    // Add user message
    const userMessage: AxonMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: textContent.trim(),
    };
    setMessages((prev) => [...prev, userMessage]);

    // Create placeholder for assistant message
    const assistantId = `assistant-${Date.now()}`;
    const assistantMessage: AxonMessage = {
      id: assistantId,
      role: "assistant",
      content: "",
    };
    setMessages((prev) => [...prev, assistantMessage]);

    setIsRunning(true);
    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          message: textContent,
          conversationId: currentConversationId, // Send conversation ID to maintain state
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to send message");
      }

      if (!response.body) {
        throw new Error("No response body");
      }

      // Read the SSE stream
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Process complete SSE events
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const event: StreamEvent = JSON.parse(line.slice(6));

              if (event.type === "conversation_id") {
                // Store conversation ID for subsequent requests
                currentConversationId = event.content;
              } else if (event.type === "text") {
                // Append text to assistant message (immutable)
                setMessages((prev) => {
                  const lastIndex = prev.length - 1;
                  const lastMessage = prev[lastIndex];
                  if (lastMessage?.id === assistantId) {
                    return [
                      ...prev.slice(0, lastIndex),
                      { ...lastMessage, content: lastMessage.content + event.content },
                    ];
                  }
                  return prev;
                });
              } else if (event.type === "error") {
                throw new Error(event.content);
              }
            } catch (parseError) {
              if (parseError instanceof SyntaxError) {
                console.error("Failed to parse SSE event:", parseError);
              } else {
                throw parseError;
              }
            }
          }
        }
      }
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") {
        return;
      }

      // Update assistant message with error
      setMessages((prev) => {
        const lastIndex = prev.length - 1;
        const lastMessage = prev[lastIndex];
        if (lastMessage?.id === assistantId && !lastMessage.content) {
          return [
            ...prev.slice(0, lastIndex),
            {
              ...lastMessage,
              content: `Error: ${err instanceof Error ? err.message : "Unknown error"}`,
            },
          ];
        }
        return prev;
      });
    } finally {
      setIsRunning(false);
      abortControllerRef.current = null;
    }
  }, []);

  const onCancel = useCallback(async () => {
    abortControllerRef.current?.abort();
    setIsRunning(false);
  }, []);

  const runtime = useExternalStoreRuntime({
    messages: threadMessages,
    isRunning,
    onNew,
    onCancel,
    convertMessage: (message) => message, // Identity converter for ThreadMessageLike
  });

  // Clear messages and reset conversation
  const clearMessages = useCallback(() => {
    setMessages([]);
    currentConversationId = null; // Start fresh conversation
  }, []);

  // Send an initial message directly (used for URL-based message sending)
  // This bypasses the AppendMessage format and calls the streaming logic directly
  const sendInitialMessage = useCallback(async (content: string) => {
    if (!content.trim() || isRunning) return;

    // Add user message
    const userMessage: AxonMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: content.trim(),
    };
    setMessages((prev) => [...prev, userMessage]);

    // Create placeholder for assistant message
    const assistantId = `assistant-${Date.now()}`;
    const assistantMessage: AxonMessage = {
      id: assistantId,
      role: "assistant",
      content: "",
    };
    setMessages((prev) => [...prev, assistantMessage]);

    setIsRunning(true);
    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          message: content,
          conversationId: currentConversationId,
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to send message");
      }

      if (!response.body) {
        throw new Error("No response body");
      }

      // Read the SSE stream
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Process complete SSE events
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const event: StreamEvent = JSON.parse(line.slice(6));

              if (event.type === "conversation_id") {
                currentConversationId = event.content;
              } else if (event.type === "text") {
                setMessages((prev) => {
                  const lastIndex = prev.length - 1;
                  const lastMessage = prev[lastIndex];
                  if (lastMessage?.id === assistantId) {
                    return [
                      ...prev.slice(0, lastIndex),
                      { ...lastMessage, content: lastMessage.content + event.content },
                    ];
                  }
                  return prev;
                });
              } else if (event.type === "error") {
                throw new Error(event.content);
              }
            } catch (parseError) {
              if (parseError instanceof SyntaxError) {
                console.error("Failed to parse SSE event:", parseError);
              } else {
                throw parseError;
              }
            }
          }
        }
      }
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") {
        return;
      }

      setMessages((prev) => {
        const lastIndex = prev.length - 1;
        const lastMessage = prev[lastIndex];
        if (lastMessage?.id === assistantId && !lastMessage.content) {
          return [
            ...prev.slice(0, lastIndex),
            {
              ...lastMessage,
              content: `Error: ${err instanceof Error ? err.message : "Unknown error"}`,
            },
          ];
        }
        return prev;
      });
    } finally {
      setIsRunning(false);
      abortControllerRef.current = null;
    }
  }, [isRunning]);

  return {
    runtime,
    messages,
    isRunning,
    clearMessages,
    sendInitialMessage,
    conversationId: currentConversationId,
  };
}


"use client";

import { useState, useRef, useEffect } from "react";
import { ChatMessage, ChatInput, ChatHeader } from "@/components/chat";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

// Mock initial messages for demo
const initialMessages: Message[] = [
  {
    id: "1",
    role: "user",
    content: "How many samples do you have?",
  },
  {
    id: "2",
    role: "assistant",
    content: "The database contains 17,870 brain tissue samples.",
  },
  {
    id: "3",
    role: "user",
    content:
      "how many of those have a clinical and neuropathological diagnosis of alzheimer's disease?",
  },
  {
    id: "4",
    role: "assistant",
    content: `The database contains 1,761 samples with an Alzheimer's disease diagnosis:

• 957 samples: Alzheimer's disease, unspecified
• 700 samples: Alzheimer's disease with late onset
• 104 samples: Alzheimer's disease with early onset`,
  },
];

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (content: string) => {
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content,
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    // TODO: Implement actual API call
    // For now, simulate a response
    setTimeout(() => {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content:
          "I understand your question. Let me search the database for relevant information.\n\n*This is a placeholder response. The chat API integration will be implemented in the next phase.*",
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setIsLoading(false);
    }, 1500);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Main container with rounded top corners */}
      <div className="flex-1 flex flex-col bg-surface rounded-tl-3xl rounded-tr-3xl shadow-sm overflow-hidden">
        {/* Header */}
        <ChatHeader
          title="Sample Inventory Count"
          onDropdownClick={() => {
            // TODO: Open conversation switcher
          }}
        />

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto px-10 scrollbar-thin">
          <div className="max-w-[640px] mx-auto space-y-11 py-6">
            {messages.map((message) => (
              <ChatMessage
                key={message.id}
                role={message.role}
                content={message.content}
              />
            ))}

            {isLoading && (
              <div className="flex justify-start">
                <div className="text-muted-foreground">Thinking...</div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Footer with input */}
        <div className="px-10 py-8">
          <div className="max-w-[608px] mx-auto space-y-4">
            <ChatInput onSend={handleSend} disabled={isLoading} />
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

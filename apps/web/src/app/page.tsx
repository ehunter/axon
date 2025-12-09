"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Dna, HelpCircle, Paperclip, ArrowUp } from "lucide-react";
import { Sidebar } from "@/components/layout/sidebar";

export default function Home() {
  return (
    <div className="min-h-screen bg-background flex">
      {/* Sidebar */}
      <Sidebar />
      
      {/* Main content */}
      <div className="flex-1 p-4 pr-4 pt-4 pb-0">
        <div className="main-container h-full flex flex-col items-center">
          {/* Header spacer */}
          <div className="w-full p-6" />
          
          {/* Content */}
          <div className="flex-1 flex flex-col items-center justify-center px-4 py-20 w-full max-w-[700px]">
            {/* Greeting */}
            <div className="w-full space-y-8">
              <h1 className="text-display text-surface-foreground animate-fade-in">
                What can I help you with?
              </h1>
              
              {/* Suggestion Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 animate-fade-in-up">
                <SuggestionCard
                  icon={<Dna className="h-6 w-6" />}
                  title="Find Tissue Samples"
                  description="I need 8 Alzheimer's tissue samples and 8 control samples"
                />
                <SuggestionCard
                  icon={<HelpCircle className="h-6 w-6" />}
                  title="Answer Questions"
                  description="Why are Braak scores important when selecting tissue samples?"
                />
                <SuggestionCard
                  icon={<Dna className="h-6 w-6" />}
                  title="Inventory Management"
                  description="Pull up my samples from last cohort"
                />
              </div>
            </div>
          </div>
          
          {/* Footer with chat input */}
          <div className="w-full max-w-[700px] px-10 py-8 space-y-4">
            <ChatInputHome />
            <p className="text-base text-muted-foreground text-center">
              Axon is in Beta and can make mistakes. Please check your tissue recommendations
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function SuggestionCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <Link 
      href={`/chat?message=${encodeURIComponent(description)}`}
      className="suggestion-card flex flex-col gap-6"
    >
      <div className="text-card-foreground">
        {icon}
      </div>
      <div className="space-y-2">
        <h3 className="text-base font-semibold text-card-foreground leading-6">{title}</h3>
        <p className="text-base text-card-foreground/80 leading-6">{description}</p>
      </div>
    </Link>
  );
}

function ChatInputHome() {
  const [message, setMessage] = useState("");
  const router = useRouter();

  const handleSubmit = () => {
    if (message.trim()) {
      // Navigate to chat with initial message as query param
      router.push(`/chat?message=${encodeURIComponent(message.trim())}`);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="w-full bg-input rounded-[20px] px-5 py-4 h-[120px]">
      <div className="flex flex-col justify-between h-full">
        {/* Text input */}
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask anything"
          className="w-full bg-transparent text-base text-foreground placeholder:text-muted-foreground leading-6 resize-none focus:outline-none"
          rows={2}
        />
        
        {/* Bottom row with attach and send */}
        <div className="flex items-center justify-between">
          {/* Attach button */}
          <button 
            type="button"
            className="flex items-center gap-1.5 text-muted-foreground hover:text-foreground transition-colors"
          >
            <Paperclip className="h-5 w-5" />
            <span className="text-base font-medium">Attach</span>
          </button>
          
          {/* Send button */}
          <button
            type="button"
            onClick={handleSubmit}
            disabled={!message.trim()}
            className="bg-primary text-primary-foreground rounded-full p-1.5 hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ArrowUp className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
}

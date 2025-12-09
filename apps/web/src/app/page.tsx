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
      <div className="flex-1 flex items-center justify-center">
        <div className="flex flex-col items-center w-full max-w-[700px] space-y-6 -mt-16">
          {/* Greeting */}
          <h1 className="text-display text-surface-foreground animate-fade-in text-center">
            What can I help you with?
          </h1>
          
          {/* Chat input */}
          <div className="w-full animate-fade-in-up">
            <ChatInputHome />
          </div>
          
          {/* Suggestion Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 w-full animate-fade-in-up">
            <SuggestionCard
              icon={<Dna className="h-5 w-5" />}
              title="Find Tissue Samples"
              description="I need 8 Alzheimer's tissue samples and 8 control samples"
            />
            <SuggestionCard
              icon={<HelpCircle className="h-5 w-5" />}
              title="Answer Questions"
              description="Why are Braak scores important when selecting tissue samples?"
            />
            <SuggestionCard
              icon={<Dna className="h-5 w-5" />}
              title="Inventory Management"
              description="Pull up my samples from last cohort"
            />
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
      className="suggestion-card flex flex-col gap-4 p-4 rounded-xl border border-border bg-card hover:bg-muted/50 transition-colors"
    >
      <div className="text-muted-foreground">
        {icon}
      </div>
      <div className="space-y-1">
        <h3 className="text-base font-medium text-card-foreground">{title}</h3>
        <p className="text-base text-muted-foreground leading-6">{description}</p>
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
    <div className="w-full bg-input rounded-[20px] px-5 py-4 h-[120px] border border-transparent hover:border-muted-foreground/30 focus-within:border-muted-foreground/30 transition-colors">
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

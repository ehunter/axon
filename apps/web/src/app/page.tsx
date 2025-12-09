"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Dna, HelpCircle, Paperclip, ArrowUp, Sparkles, Briefcase, Lightbulb } from "lucide-react";
import { Sidebar } from "@/components/layout/sidebar";

export default function Home() {
  return (
    <div className="min-h-screen bg-background flex">
      {/* Sidebar */}
      <Sidebar />
      
      {/* Main content */}
      <div className="flex-1 p-4 pr-4 pt-4 pb-0">
        <div className="main-container h-full flex flex-col items-center justify-center">
          {/* Centered content area */}
          <div className="flex flex-col items-center w-full max-w-[700px] space-y-6">
            {/* Greeting */}
            <h1 className="text-display text-surface-foreground animate-fade-in text-center">
              What can I help you with?
            </h1>
            
            {/* Chat input */}
            <div className="w-full animate-fade-in-up">
              <ChatInputHome />
            </div>
            
            {/* Category pills */}
            <div className="flex flex-wrap justify-center gap-2 animate-fade-in-up">
              <CategoryPill icon={<Dna className="h-4 w-4" />} label="Find Samples" />
              <CategoryPill icon={<HelpCircle className="h-4 w-4" />} label="Learn" />
              <CategoryPill icon={<Sparkles className="h-4 w-4" />} label="Explore" />
              <CategoryPill icon={<Briefcase className="h-4 w-4" />} label="My Cohorts" />
              <CategoryPill icon={<Lightbulb className="h-4 w-4" />} label="Suggestions" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function CategoryPill({
  icon,
  label,
}: {
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <button
      type="button"
      className="flex items-center gap-2 px-4 py-2 rounded-full border border-border bg-transparent text-foreground hover:bg-muted transition-colors"
    >
      {icon}
      <span className="text-base">{label}</span>
    </button>
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

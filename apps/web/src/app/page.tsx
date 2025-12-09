import Link from "next/link";
import { Dna, HelpCircle, Paperclip, ArrowUp } from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-screen bg-background flex">
      {/* Sidebar placeholder for consistent layout */}
      <div className="hidden lg:block w-[270px] bg-sidebar shrink-0" />
      
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
            <ChatInputPreview />
            <p className="text-sm text-muted-foreground text-center">
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
      href="/chat"
      className="suggestion-card flex flex-col gap-6"
    >
      <div className="text-card-foreground">
        {icon}
      </div>
      <div className="space-y-2">
        <h3 className="text-base font-semibold text-card-foreground leading-5">{title}</h3>
        <p className="text-sm text-card-foreground/80 leading-5">{description}</p>
      </div>
    </Link>
  );
}

function ChatInputPreview() {
  return (
    <Link 
      href="/chat"
      className="block w-full bg-input rounded-[20px] px-5 py-4 h-[120px] hover:bg-input/80 transition-colors group"
    >
      <div className="flex flex-col justify-between h-full">
        {/* Placeholder text */}
        <p className="text-sm text-muted-foreground leading-5">
          Ask anything
        </p>
        
        {/* Bottom row with attach and send */}
        <div className="flex items-center justify-between">
          {/* Attach button */}
          <div className="flex items-center gap-1 text-muted-foreground">
            <Paperclip className="h-4 w-4" />
            <span className="text-xs font-medium">Attach</span>
          </div>
          
          {/* Send button */}
          <div className="bg-primary text-primary-foreground rounded-full p-1 group-hover:bg-primary/90 transition-colors">
            <ArrowUp className="h-5 w-5" />
          </div>
        </div>
      </div>
    </Link>
  );
}

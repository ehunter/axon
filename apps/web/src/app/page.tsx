import Link from "next/link";
import { Brain, Search, MessageSquare, Database, ArrowRight, Dna, HelpCircle } from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-screen bg-background flex">
      {/* Sidebar placeholder for consistent layout */}
      <div className="hidden lg:block w-[270px] bg-sidebar shrink-0" />
      
      {/* Main content */}
      <div className="flex-1 p-4 pr-4 pt-4 pb-0">
        <div className="main-container bg-surface h-full flex flex-col items-center">
          {/* Header spacer */}
          <div className="w-full p-6" />
          
          {/* Content */}
          <div className="flex-1 flex flex-col items-center justify-center px-4 py-20 w-full max-w-[700px]">
            {/* Greeting */}
            <div className="w-full space-y-8">
              <h1 className="text-display text-white animate-fade-in">
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
          
          {/* Footer with chat input preview */}
          <div className="w-full max-w-[700px] px-10 py-8 space-y-4">
            <Link 
              href="/chat"
              className="block w-full bg-[#343b50] rounded-[20px] px-5 py-4 text-[#969598] hover:bg-[#3d4560] transition-colors"
            >
              Ask anything
            </Link>
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
      <div className="text-white">
        {icon}
      </div>
      <div className="space-y-2">
        <h3 className="text-base font-semibold text-white leading-5">{title}</h3>
        <p className="text-sm text-[#d7d8da] leading-5">{description}</p>
      </div>
    </Link>
  );
}

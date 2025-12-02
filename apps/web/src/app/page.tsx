import Link from "next/link";
import { Brain, Search, MessageSquare, Database, ArrowRight, Sparkles } from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 glass border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-2">
              <Brain className="h-8 w-8" />
              <span className="text-xl font-bold">Axon</span>
            </div>
            <div className="flex items-center gap-4">
              <Link
                href="/login"
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                Sign In
              </Link>
              <Link
                href="/login"
                className="bg-primary text-primary-foreground px-4 py-2 rounded-lg font-medium hover:opacity-90 transition-opacity"
              >
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4">
        <div className="max-w-5xl mx-auto text-center">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 bg-secondary text-secondary-foreground px-4 py-2 rounded-full text-sm font-medium mb-6 animate-fade-in">
            <Sparkles className="h-4 w-4" />
            AI-Powered Brain Bank Discovery
          </div>
          
          {/* Headline */}
          <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6 animate-fade-in-up">
            Find the perfect brain tissue samples for your research
          </h1>
          
          {/* Subheadline */}
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-10 animate-fade-in-up stagger-1">
            Axon uses AI to help neuroscience researchers discover and access 
            brain tissue samples from multiple brain banks. Search by diagnosis, 
            region, quality metrics, and more.
          </p>
          
          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-fade-in-up stagger-2">
            <Link
              href="/chat"
              className="group flex items-center gap-2 bg-primary text-primary-foreground px-8 py-4 rounded-xl font-semibold text-lg hover:opacity-90 transition-opacity"
            >
              Start Searching
              <ArrowRight className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link
              href="/samples"
              className="flex items-center gap-2 bg-secondary text-secondary-foreground px-8 py-4 rounded-xl font-semibold text-lg hover:bg-accent transition-colors"
            >
              Browse Samples
            </Link>
          </div>
        </div>
      </section>

      {/* Visual Element - Minimal line */}
      <section className="py-12 px-4 overflow-hidden">
        <div className="max-w-6xl mx-auto">
          <div className="relative h-16 flex items-center justify-center">
            <div className="w-full h-px bg-gradient-to-r from-transparent via-border to-transparent" />
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-20 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold mb-4">
              Intelligent Sample Discovery
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Powered by advanced AI, Axon understands your research needs and 
              finds the most suitable samples across multiple brain banks.
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            <FeatureCard
              icon={<MessageSquare className="h-6 w-6" />}
              title="Natural Language Search"
              description="Describe your research needs in plain English. Our AI understands complex requirements like tissue type, quality metrics, and disease staging."
              delay={0}
            />
            <FeatureCard
              icon={<Database className="h-6 w-6" />}
              title="Multi-Bank Access"
              description="Search across NIH NeuroBioBank, Harvard, Mount Sinai, and more. One search, all sources, ranked by relevance."
              delay={1}
            />
            <FeatureCard
              icon={<Search className="h-6 w-6" />}
              title="Smart Filtering"
              description="Filter by RIN score, PMI, Braak stage, diagnosis, brain region, and demographics. Find exactly what you need."
              delay={2}
            />
            <FeatureCard
              icon={<Brain className="h-6 w-6" />}
              title="Expert Knowledge"
              description="Built-in neuroscience expertise. Get guidance on tissue quality requirements for different experimental techniques."
              delay={3}
            />
            <FeatureCard
              icon={<MessageSquare className="h-6 w-6" />}
              title="Conversation History"
              description="Pick up where you left off. Your searches and selections are saved, ready to resume anytime."
              delay={4}
            />
            <FeatureCard
              icon={<ArrowRight className="h-6 w-6" />}
              title="Direct Requests"
              description="Generate sample request lists with all the details you need to contact brain banks directly."
              delay={5}
            />
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-20 px-4 border-y border-border">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            <StatCard value="50,000+" label="Samples Available" />
            <StatCard value="4+" label="Brain Banks" />
            <StatCard value="100+" label="Disease Categories" />
            <StatCard value="24/7" label="AI Assistance" />
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl font-bold mb-4">
            Ready to accelerate your research?
          </h2>
          <p className="text-muted-foreground mb-8">
            Join researchers who are finding the perfect samples faster with Axon.
          </p>
          <Link
            href="/login"
            className="inline-flex items-center gap-2 bg-primary text-primary-foreground px-8 py-4 rounded-xl font-semibold text-lg hover:opacity-90 transition-opacity"
          >
            Get Started Free
            <ArrowRight className="h-5 w-5" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-12 px-4">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Brain className="h-6 w-6" />
            <span className="font-semibold">Axon</span>
          </div>
          <p className="text-sm text-muted-foreground">
            © {new Date().getFullYear()} Axon Brain Bank Discovery. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  description,
  delay,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  delay: number;
}) {
  return (
    <div 
      className="group p-6 rounded-xl border border-border bg-card card-interactive animate-fade-in-up"
      style={{ animationDelay: `${delay * 0.1}s` }}
    >
      <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-secondary text-secondary-foreground mb-4 group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
        {icon}
      </div>
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <p className="text-muted-foreground text-sm">{description}</p>
    </div>
  );
}

function StatCard({ value, label }: { value: string; label: string }) {
  return (
    <div className="text-center">
      <div className="text-4xl font-bold mb-2">{value}</div>
      <div className="text-muted-foreground text-sm">{label}</div>
    </div>
  );
}

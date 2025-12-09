export default function AboutPage() {
  return (
    <div className="p-6">
      <div className="max-w-2xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">About Axon</h1>
          <p className="text-muted-foreground">
            Learn more about the Axon Brain Bank Discovery platform
          </p>
        </div>

        <div className="space-y-6">
          <section className="p-6 rounded-xl border border-border bg-card">
            <h2 className="text-lg font-semibold mb-4">What is Axon?</h2>
            <p className="text-base text-muted-foreground">
              Axon is an AI-powered platform designed to help neuroscience researchers
              discover and access brain tissue samples from multiple brain banks. Our
              intelligent assistant understands your research needs and helps you find
              the perfect samples for your studies.
            </p>
          </section>

          <section className="p-6 rounded-xl border border-border bg-card">
            <h2 className="text-lg font-semibold mb-4">Features</h2>
            <ul className="space-y-2 text-base text-muted-foreground">
              <li>• Natural language search for brain tissue samples</li>
              <li>• Multi-bank access across NIH NeuroBioBank and other sources</li>
              <li>• Smart filtering by diagnosis, region, quality metrics, and more</li>
              <li>• Conversation history and sample selection management</li>
              <li>• Expert guidance on tissue quality requirements</li>
            </ul>
          </section>

          <section className="p-6 rounded-xl border border-border bg-card">
            <h2 className="text-lg font-semibold mb-4">Beta Notice</h2>
            <p className="text-base text-muted-foreground">
              Axon is currently in Beta. While we strive for accuracy, please verify
              all tissue recommendations and sample details before submitting requests
              to brain banks.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}


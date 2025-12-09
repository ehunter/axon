"use client";

import { useState } from "react";
import { Search, Database } from "lucide-react";

const sampleData = [
  {
    id: "1",
    external_id: "BEB21160",
    source_bank: "NIH Miami",
    diagnosis: "Alzheimer's Disease",
    age: 81,
    sex: "Female",
    brain_region: "Frontal Cortex",
    rin: 6.6,
    pmi: 21.2,
  },
  {
    id: "2",
    external_id: "4608",
    source_bank: "NIH Sepulveda",
    diagnosis: "Alzheimer's Disease",
    age: 80,
    sex: "Male",
    brain_region: "Frontal Cortex",
    rin: 7.1,
    pmi: 3.1,
  },
];

export default function SamplesPage() {
  const [searchQuery, setSearchQuery] = useState("");

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Sample Browser</h1>
          <p className="text-muted-foreground">
            Search and filter brain tissue samples
          </p>
        </div>

        <div className="mb-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search samples..."
              className="w-full pl-10 pr-4 py-3 rounded-xl border border-input bg-background text-base focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
        </div>

        <div className="grid gap-4">
          {sampleData.map((sample) => (
            <div
              key={sample.id}
              className="p-4 rounded-xl border border-border bg-card hover:border-secondary transition-all"
            >
              <div className="flex items-center gap-4">
                <Database className="h-6 w-6" />
                <div className="flex-1">
                  <h3 className="font-semibold">{sample.external_id}</h3>
                  <p className="text-base text-muted-foreground">
                    {sample.diagnosis} | {sample.source_bank}
                  </p>
                </div>
                <div className="text-base text-muted-foreground">
                  RIN: {sample.rin} | PMI: {sample.pmi}h
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

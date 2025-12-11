/**
 * Demo page for the Recommended Samples Widget
 */

"use client";

import { RecommendedSamplesCard, RecommendedSample, ActiveFilter } from "@/components/chat/recommended-samples";

// Mock data for demonstration (brain bank samples)
const MOCK_SAMPLES: RecommendedSample[] = [
  {
    id: "1",
    externalId: "HBCC-2041",
    type: "Frozen",
    rin: 8.2,
    age: 72,
    sex: "Male",
    diagnosis: "Alzheimer's Disease",
    braakStage: "IV",
    price: 150,
    sourceBank: "NIH HBCC",
    pmi: 12,
    coPathologies: "CAA",
    details: {
      tissueRegion: "Frontal Cortex",
      collectionDate: "2024-03-15",
      pathologyNotes: "Moderate amyloid plaques, neurofibrillary tangles present.",
    },
  },
  {
    id: "2",
    externalId: "MSN-1587",
    type: "Frozen",
    rin: 7.5,
    age: 68,
    sex: "Female",
    diagnosis: "Alzheimer's Disease",
    braakStage: "V",
    price: 120,
    sourceBank: "Mt. Sinai",
    pmi: 8,
    coPathologies: "LBD",
    details: {
      tissueRegion: "Hippocampus",
      collectionDate: "2024-02-28",
      pathologyNotes: "Severe tau pathology with Lewy body co-pathology.",
    },
  },
  {
    id: "3",
    externalId: "HVD-0923",
    type: "Frozen",
    rin: 7.8,
    age: 75,
    sex: "Male",
    diagnosis: "Alzheimer's Disease",
    braakStage: "IV",
    price: 150,
    sourceBank: "Harvard",
    pmi: 15,
    coPathologies: null,
    details: {
      tissueRegion: "Temporal Cortex",
      collectionDate: "2024-01-20",
    },
  },
  {
    id: "4",
    externalId: "MIA-3342",
    type: "Frozen",
    rin: 6.9,
    age: 80,
    sex: "Female",
    diagnosis: "Alzheimer's Disease",
    braakStage: "VI",
    price: 110,
    sourceBank: "NIH Miami",
    pmi: 18,
    coPathologies: "TDP-43, CAA",
    details: {
      tissueRegion: "Entorhinal Cortex",
      collectionDate: "2023-12-10",
      pathologyNotes: "Advanced AD with multiple co-pathologies.",
    },
  },
  {
    id: "5",
    externalId: "HBCC-1876",
    type: "Frozen",
    rin: 8.9,
    age: 65,
    sex: "Male",
    diagnosis: "Control",
    braakStage: "I",
    price: 165,
    sourceBank: "NIH HBCC",
    pmi: 6,
    coPathologies: null,
    details: {
      tissueRegion: "Frontal Cortex",
      collectionDate: "2024-04-01",
      donorHistory: "No neurological conditions. Cardiac arrest.",
    },
  },
];

const MOCK_FILTERS: ActiveFilter[] = [
  { id: "1", label: "Diagnosis", value: "Alzheimer's", removable: false },
  { id: "2", label: "RIN", value: "≥ 6.5", removable: true },
  { id: "3", label: "Braak", value: "≥ IV", removable: true },
];

export default function SamplesWidgetDemoPage() {
  const handleSaveToCohort = (sampleIds: string[]) => {
    console.log("Save to cohort:", sampleIds);
    alert(`Saved ${sampleIds.length} samples to cohort!`);
  };

  const handleSubmitOrder = (sampleIds: string[], config: any) => {
    console.log("Submit order:", { sampleIds, config });
  };

  const handleFilterRemove = (filterId: string) => {
    console.log("Remove filter:", filterId);
  };

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          <div>
            <h1 className="text-2xl font-semibold text-foreground mb-2">
              Recommended Samples Widget Demo
            </h1>
            <p className="text-muted-foreground">
              Interactive widget for selecting and ordering tissue samples.
            </p>
          </div>

          {/* The widget */}
          <RecommendedSamplesCard
            samples={MOCK_SAMPLES}
            filters={MOCK_FILTERS}
            title="Recommended Samples"
            onSaveToCohort={handleSaveToCohort}
            onSubmitOrder={handleSubmitOrder}
            onFilterRemove={handleFilterRemove}
          />

          {/* Instructions */}
          <div className="bg-muted/50 rounded-lg p-4 text-sm text-muted-foreground">
            <h3 className="font-medium text-foreground mb-2">Try it out:</h3>
            <ul className="list-disc list-inside space-y-1">
              <li>Click rows to expand and see details</li>
              <li>Use checkboxes to select samples</li>
              <li>Click "Configure Order" to see the order form</li>
              <li>Submit to see the success state</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}


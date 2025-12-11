/**
 * Demo page for the Recommended Samples Widget
 */

"use client";

import { RecommendedSamplesCard, RecommendedSample, ActiveFilter } from "@/components/chat/recommended-samples";

// Mock data for demonstration
const MOCK_SAMPLES: RecommendedSample[] = [
  {
    id: "1",
    externalId: "LVR-01",
    type: "Frozen",
    rin: 8.2,
    age: 45,
    sex: "Male",
    diagnosis: "Hepatocellular Carcinoma",
    braakStage: null,
    price: 150,
    sourceBank: "NIH HBCC",
    details: {
      tissueRegion: "Left Lobe",
      collectionDate: "2024-03-15",
      pathologyNotes: "Well-differentiated tumor with clear margins.",
      donorHistory: "No significant medical history. Non-smoker.",
    },
  },
  {
    id: "2",
    externalId: "LVR-04",
    type: "FFPE",
    rin: 7.5,
    age: 52,
    sex: "Female",
    diagnosis: "Cirrhosis",
    braakStage: null,
    price: 120,
    sourceBank: "Mt. Sinai",
    details: {
      tissueRegion: "Right Lobe",
      collectionDate: "2024-02-28",
      pathologyNotes: "Stage 3 fibrosis with nodular regeneration.",
    },
  },
  {
    id: "3",
    externalId: "LVR-09",
    type: "Frozen",
    rin: 7.1,
    age: 33,
    sex: "Male",
    diagnosis: "Fatty Liver Disease",
    braakStage: null,
    price: 150,
    sourceBank: "Harvard",
    details: {
      tissueRegion: "Central",
      collectionDate: "2024-01-20",
    },
  },
  {
    id: "4",
    externalId: "LVR-12",
    type: "FFPE",
    rin: 6.8,
    age: 61,
    sex: "Female",
    diagnosis: "Metastatic Colon Cancer",
    braakStage: null,
    price: 110,
    sourceBank: "NIH Miami",
    details: {
      tissueRegion: "Multiple Lobes",
      collectionDate: "2023-12-10",
      pathologyNotes: "Multiple metastatic lesions, largest 2.3cm.",
    },
  },
  {
    id: "5",
    externalId: "LVR-15",
    type: "Frozen",
    rin: 8.9,
    age: 28,
    sex: "Male",
    diagnosis: "Normal Control",
    braakStage: null,
    price: 165,
    sourceBank: "NIH HBCC",
    details: {
      tissueRegion: "Left Lobe",
      collectionDate: "2024-04-01",
      donorHistory: "Trauma victim, no liver pathology.",
    },
  },
];

const MOCK_FILTERS: ActiveFilter[] = [
  { id: "1", label: "Organ", value: "Liver", removable: true },
  { id: "2", label: "RIN", value: "> 6.5", removable: true },
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


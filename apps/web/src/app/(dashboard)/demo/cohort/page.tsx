"use client";

import { SampleDataTable } from "@/components/cohort";
import { CohortSample } from "@/types/cohort";

/**
 * Demo page for testing the interactive cohort data table
 */
export default function CohortDemoPage() {
  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 flex flex-col bg-surface shadow-sm overflow-hidden">
        <div className="flex-1 overflow-auto p-10">
          <SampleDataTable
            samples={MOCK_SAMPLES}
            title="RNA Seq - March 2025"
            onExport={() => alert("Export clicked!")}
          />
        </div>
      </div>
    </div>
  );
}

/**
 * Mock sample data for demo
 */
const MOCK_SAMPLES: CohortSample[] = [
  {
    id: "1",
    externalId: "BC-123456",
    sourceBank: "NIH Miami",
    group: "case",
    age: 78,
    sex: "Male",
    race: "Caucasian",
    primaryDiagnosis: "Alzheimer's Disease",
    diagnoses: ["Alzheimer's", "Lewy Body"],
    braakStage: "IV",
    rin: 7.4,
    pmi: 8.5,
    ph: 6.5,
    rawData: {},
  },
  {
    id: "2",
    externalId: "BC-123457",
    sourceBank: "NIH Miami",
    group: "case",
    age: 82,
    sex: "Female",
    race: "Caucasian",
    primaryDiagnosis: "Alzheimer's Disease",
    diagnoses: ["Alzheimer's", "Lewy Body"],
    braakStage: "V",
    rin: 6.8,
    pmi: 21,
    ph: 6.4,
    rawData: {},
  },
  {
    id: "3",
    externalId: "BC-123458",
    sourceBank: "NIH Sepulveda",
    group: "case",
    age: 74,
    sex: "Male",
    race: "Hispanic",
    primaryDiagnosis: "Alzheimer's Disease",
    diagnoses: ["Alzheimer's", "Parkinson's"],
    braakStage: "III",
    rin: 7.1,
    pmi: 14,
    ph: 6.6,
    rawData: {},
  },
  {
    id: "4",
    externalId: "BC-123459",
    sourceBank: "Mt. Sinai",
    group: "case",
    age: 69,
    sex: "Female",
    race: "Caucasian",
    primaryDiagnosis: "Frontotemporal Dementia",
    diagnoses: ["FTD"],
    braakStage: "IV",
    rin: 8.2,
    pmi: 12,
    ph: 6.5,
    rawData: {},
  },
  {
    id: "5",
    externalId: "NIH0001234",
    sourceBank: "NIH HBCC",
    group: "control",
    age: 75,
    sex: "Female",
    race: "Caucasian",
    primaryDiagnosis: "Control",
    diagnoses: [],
    braakStage: "I",
    rin: 8.5,
    pmi: 6.5,
    ph: 6.7,
    rawData: {},
  },
  {
    id: "6",
    externalId: "NIH0001235",
    sourceBank: "NIH HBCC",
    group: "control",
    age: 71,
    sex: "Male",
    race: "African American",
    primaryDiagnosis: "Control",
    diagnoses: [],
    braakStage: "II",
    rin: 7.9,
    pmi: 12.5,
    ph: 6.6,
    rawData: {},
  },
  {
    id: "7",
    externalId: "NIH0001236",
    sourceBank: "NIH Miami",
    group: "control",
    age: 79,
    sex: "Female",
    race: "Caucasian",
    primaryDiagnosis: "Control",
    diagnoses: [],
    braakStage: "I",
    rin: 8.1,
    pmi: 8.5,
    ph: 6.5,
    rawData: {},
  },
  {
    id: "8",
    externalId: "NIH0001237",
    sourceBank: "NIH Sepulveda",
    group: "control",
    age: 68,
    sex: "Male",
    race: "Caucasian",
    primaryDiagnosis: "Control",
    diagnoses: [],
    braakStage: "0",
    rin: 7.6,
    pmi: 24,
    ph: 6.4,
    rawData: {},
  },
  {
    id: "9",
    externalId: "NIH0001238",
    sourceBank: "Mt. Sinai",
    group: "control",
    age: 83,
    sex: "Female",
    race: "Hispanic",
    primaryDiagnosis: "Control",
    diagnoses: [],
    braakStage: "II",
    rin: 6.9,
    pmi: 29,
    ph: 6.3,
    rawData: {},
  },
  {
    id: "10",
    externalId: "NIH0001239",
    sourceBank: "Harvard",
    group: "control",
    age: 77,
    sex: "Male",
    race: "Caucasian",
    primaryDiagnosis: "Control",
    diagnoses: [],
    braakStage: "I",
    rin: 8.8,
    pmi: 49,
    ph: 6.5,
    rawData: {},
  },
];


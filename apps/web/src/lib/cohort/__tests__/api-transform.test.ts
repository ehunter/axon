/**
 * Tests for API response transformation
 * Ensures API data is correctly transformed to CohortSample format
 */

import { describe, it, expect } from "@jest/globals";
import { CohortSample } from "@/types/cohort";

// This is the same interface as in the cohort detail page
interface APICohortSample {
  id: string;
  external_id: string;
  sample_group: string;
  diagnosis: string | null;
  age: number | null;
  sex: string | null;
  source_bank: string | null;
  race: string | null;
  braak_stage: string | null;
  rin: number | null;
  pmi: number | null;
  ph: number | null;
  diagnoses: string[];
}

// Transform function (extracted for testing)
export function transformAPISamples(apiSamples: APICohortSample[]): CohortSample[] {
  return apiSamples.map((s) => ({
    id: s.id,
    externalId: s.external_id,
    sourceBank: s.source_bank || "",
    group: s.sample_group as "case" | "control",
    age: s.age,
    sex: s.sex as "Male" | "Female" | null,
    race: s.race,
    primaryDiagnosis: s.diagnosis,
    diagnoses: s.diagnoses || [],
    braakStage: s.braak_stage,
    rin: s.rin,
    pmi: s.pmi,
    ph: s.ph,
    rawData: {},
  }));
}

describe("API transform", () => {
  const mockAPISample: APICohortSample = {
    id: "uuid-123",
    external_id: "BC-123456",
    sample_group: "case",
    diagnosis: "Alzheimer's Disease",
    age: 78,
    sex: "Male",
    source_bank: "NIH Miami",
    race: "Caucasian",
    braak_stage: "IV",
    rin: 7.4,
    pmi: 8.5,
    ph: 6.5,
    diagnoses: ["Alzheimer's", "Lewy Body"],
  };

  describe("transformAPISamples", () => {
    it("should transform snake_case API fields to camelCase", () => {
      const result = transformAPISamples([mockAPISample]);
      
      expect(result).toHaveLength(1);
      const sample = result[0];
      
      // Check field name transformations
      expect(sample.externalId).toBe("BC-123456");
      expect(sample.sourceBank).toBe("NIH Miami");
      expect(sample.braakStage).toBe("IV");
    });

    it("should preserve all data fields", () => {
      const result = transformAPISamples([mockAPISample]);
      const sample = result[0];
      
      expect(sample.id).toBe("uuid-123");
      expect(sample.group).toBe("case");
      expect(sample.age).toBe(78);
      expect(sample.sex).toBe("Male");
      expect(sample.race).toBe("Caucasian");
      expect(sample.rin).toBe(7.4);
      expect(sample.pmi).toBe(8.5);
      expect(sample.ph).toBe(6.5);
      expect(sample.diagnoses).toEqual(["Alzheimer's", "Lewy Body"]);
    });

    it("should handle null values correctly", () => {
      const sampleWithNulls: APICohortSample = {
        ...mockAPISample,
        race: null,
        braak_stage: null,
        rin: null,
        pmi: null,
        ph: null,
        diagnoses: [],
      };
      
      const result = transformAPISamples([sampleWithNulls]);
      const sample = result[0];
      
      expect(sample.race).toBeNull();
      expect(sample.braakStage).toBeNull();
      expect(sample.rin).toBeNull();
      expect(sample.pmi).toBeNull();
      expect(sample.ph).toBeNull();
      expect(sample.diagnoses).toEqual([]);
    });

    it("should default sourceBank to empty string if null", () => {
      const sampleWithNullSource: APICohortSample = {
        ...mockAPISample,
        source_bank: null,
      };
      
      const result = transformAPISamples([sampleWithNullSource]);
      expect(result[0].sourceBank).toBe("");
    });

    it("should transform control samples correctly", () => {
      const controlSample: APICohortSample = {
        ...mockAPISample,
        sample_group: "control",
        diagnosis: "Control",
        braak_stage: "I",
      };
      
      const result = transformAPISamples([controlSample]);
      expect(result[0].group).toBe("control");
    });
  });
});


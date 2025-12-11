/**
 * Tests for column generator
 */

import { describe, it, expect } from "@jest/globals";
import { generateColumns, getFieldValue } from "../column-generator";
import { CohortSample } from "@/types/cohort";

describe("column-generator", () => {
  const mockSamples: CohortSample[] = [
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
  ];

  describe("generateColumns", () => {
    it("should generate columns for all fields with data", () => {
      const columns = generateColumns(mockSamples);
      
      // Should have columns for: externalId, group, diagnoses, braakStage, sex, age, rin, pmi, sourceBank
      // (ph and race are also available but may not be in DEFAULT_COLUMNS)
      expect(columns.length).toBeGreaterThan(5);
      
      // Check for essential columns
      const columnIds = columns.map(c => c.id);
      expect(columnIds).toContain("externalId");
      expect(columnIds).toContain("group");
      expect(columnIds).toContain("sex");
      expect(columnIds).toContain("age");
      expect(columnIds).toContain("rin");
      expect(columnIds).toContain("pmi");
    });

    it("should filter out columns without data", () => {
      const samplesWithMissingData: CohortSample[] = [
        {
          id: "1",
          externalId: "BC-123456",
          sourceBank: "NIH Miami",
          group: "case",
          age: 78,
          sex: null, // Missing sex
          race: null,
          primaryDiagnosis: null,
          diagnoses: [],
          braakStage: null, // Missing braak
          rin: null, // Missing RIN
          pmi: null,
          ph: null,
          rawData: {},
        },
      ];

      const columns = generateColumns(samplesWithMissingData);
      const columnIds = columns.map(c => c.id);
      
      // Should NOT have sex, braakStage, rin columns since no data
      expect(columnIds).not.toContain("sex");
      expect(columnIds).not.toContain("braakStage");
      expect(columnIds).not.toContain("rin");
      
      // Should still have externalId and group
      expect(columnIds).toContain("externalId");
      expect(columnIds).toContain("group");
    });

    it("should include diagnoses column when samples have diagnoses", () => {
      const columns = generateColumns(mockSamples);
      const columnIds = columns.map(c => c.id);
      expect(columnIds).toContain("diagnoses");
    });

    it("should not include diagnoses column when all diagnoses arrays are empty", () => {
      const samplesNoDiagnoses: CohortSample[] = mockSamples.map(s => ({
        ...s,
        diagnoses: [],
      }));
      
      const columns = generateColumns(samplesNoDiagnoses);
      const columnIds = columns.map(c => c.id);
      expect(columnIds).not.toContain("diagnoses");
    });
  });

  describe("getFieldValue", () => {
    const sample = mockSamples[0];

    it("should get top-level field values", () => {
      expect(getFieldValue(sample, "externalId")).toBe("BC-123456");
      expect(getFieldValue(sample, "age")).toBe(78);
      expect(getFieldValue(sample, "rin")).toBe(7.4);
    });

    it("should handle null values", () => {
      const sampleWithNull: CohortSample = {
        ...sample,
        rin: null,
      };
      expect(getFieldValue(sampleWithNull, "rin")).toBeNull();
    });

    it("should get nested field values using dot notation", () => {
      const sampleWithRawData: CohortSample = {
        ...sample,
        rawData: { braak_stage: "V", custom_field: 123 },
      };
      expect(getFieldValue(sampleWithRawData, "rawData.braak_stage")).toBe("V");
      expect(getFieldValue(sampleWithRawData, "rawData.custom_field")).toBe(123);
    });

    it("should return null for non-existent nested paths", () => {
      expect(getFieldValue(sample, "rawData.nonexistent")).toBeNull();
    });
  });
});


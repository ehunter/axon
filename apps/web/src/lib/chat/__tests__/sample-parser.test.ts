/**
 * Tests for sample parser
 */

import { describe, it, expect } from "@jest/globals";
import { parseSampleRecommendations, mightContainSamples } from "../sample-parser";

describe("sample-parser", () => {
  describe("parseSampleRecommendations", () => {
    const sampleTableMarkdown = `
Found 2 Alzheimer's samples:

**Alzheimer's Samples:**

| Sample ID | Source | Age/Sex | RIN | PMI | Co-Pathologies |
|-----------|--------|---------|-----|-----|----------------|
| \`5735\` | NIH Sepulveda | 79M | 7.4 | 21.5h | None |
| \`5780\` | NIH Sepulveda | 72F | 8.2 | 24.2h | CAA |

**Control Samples:**

| Sample ID | Source | Age/Sex | RIN | PMI | Co-Pathologies |
|-----------|--------|---------|-----|-----|----------------|
| \`6724\` | NIH Miami | 55F | 8.1 | 22.5h | None |
| \`6708\` | NIH Miami | 63M | 7.8 | 21.2h | None |

Please review these samples.
`;

    it("should detect samples in message", () => {
      const result = parseSampleRecommendations(sampleTableMarkdown);
      expect(result.hasSamples).toBe(true);
      expect(result.samples.length).toBe(4);
    });

    it("should strip backticks from sample IDs", () => {
      const result = parseSampleRecommendations(sampleTableMarkdown);
      
      // All external IDs should NOT have backticks
      expect(result.samples[0].externalId).toBe("5735");
      expect(result.samples[1].externalId).toBe("5780");
      expect(result.samples[2].externalId).toBe("6724");
      expect(result.samples[3].externalId).toBe("6708");
      
      // None should contain backticks
      result.samples.forEach((sample) => {
        expect(sample.externalId).not.toContain("`");
      });
    });

    it("should parse Age/Sex combined column correctly", () => {
      const result = parseSampleRecommendations(sampleTableMarkdown);
      
      expect(result.samples[0].age).toBe(79);
      expect(result.samples[0].sex).toBe("Male");
      expect(result.samples[1].age).toBe(72);
      expect(result.samples[1].sex).toBe("Female");
    });

    it("should parse RIN values correctly", () => {
      const result = parseSampleRecommendations(sampleTableMarkdown);
      
      expect(result.samples[0].rin).toBe(7.4);
      expect(result.samples[1].rin).toBe(8.2);
    });

    it("should parse PMI values correctly", () => {
      const result = parseSampleRecommendations(sampleTableMarkdown);
      
      expect(result.samples[0].pmi).toBe(21.5);
      expect(result.samples[1].pmi).toBe(24.2);
    });

    it("should parse source bank correctly", () => {
      const result = parseSampleRecommendations(sampleTableMarkdown);
      
      expect(result.samples[0].sourceBank).toBe("NIH Sepulveda");
      expect(result.samples[2].sourceBank).toBe("NIH Miami");
    });

    it("should identify case vs control samples", () => {
      const result = parseSampleRecommendations(sampleTableMarkdown);
      
      // First two should be case samples
      expect(result.samples[0].sampleGroup).toBe("case");
      expect(result.samples[1].sampleGroup).toBe("case");
      
      // Last two should be control samples
      expect(result.samples[2].sampleGroup).toBe("control");
      expect(result.samples[3].sampleGroup).toBe("control");
    });

    it("should create groups for cases and controls", () => {
      const result = parseSampleRecommendations(sampleTableMarkdown);
      
      expect(result.groups).toHaveLength(2);
      expect(result.groups[0].id).toBe("case");
      expect(result.groups[0].samples).toHaveLength(2);
      expect(result.groups[1].id).toBe("control");
      expect(result.groups[1].samples).toHaveLength(2);
    });

    it("should extract text before and after tables", () => {
      const result = parseSampleRecommendations(sampleTableMarkdown);
      
      expect(result.beforeTable).toContain("Found 2 Alzheimer's samples");
      expect(result.afterTable).toContain("Please review these samples");
    });

    it("should handle sample IDs without backticks", () => {
      const tableWithoutBackticks = `
| Sample ID | Source |
|-----------|--------|
| 5735 | NIH Sepulveda |
| 5780 | NIH Miami |
`;
      const result = parseSampleRecommendations(tableWithoutBackticks);
      
      expect(result.samples[0].externalId).toBe("5735");
      expect(result.samples[1].externalId).toBe("5780");
    });
  });

  describe("mightContainSamples", () => {
    it("should return true for text with sample keywords and tables", () => {
      expect(mightContainSamples("Found 2 samples | ID | Source |")).toBe(true);
      expect(mightContainSamples("I recommend these tissue specimens | ID |")).toBe(true);
    });

    it("should return false for text without tables", () => {
      expect(mightContainSamples("Found 2 samples but no table")).toBe(false);
    });

    it("should return false for text without sample keywords", () => {
      expect(mightContainSamples("| ID | Source |")).toBe(false);
    });
  });
});


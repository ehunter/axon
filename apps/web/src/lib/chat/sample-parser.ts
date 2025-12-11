/**
 * Sample Parser
 *
 * Detects and extracts sample recommendation data from agent messages.
 * Converts markdown tables to structured data for the interactive widget.
 */

import { RecommendedSample, ActiveFilter } from "@/components/chat/recommended-samples/types";

/**
 * Result of parsing an agent message for sample recommendations
 */
export interface ParsedSampleData {
  hasSamples: boolean;
  samples: RecommendedSample[];
  filters: ActiveFilter[];
  beforeTable: string;
  afterTable: string;
}

/**
 * Pattern to detect sample recommendation tables
 * Looks for markdown tables with common sample columns
 */
const SAMPLE_TABLE_PATTERN = /\|[^\n]*(?:Sample\s*ID|External\s*ID|Subject\s*ID|ID)[^\n]*\|[\s\S]*?\n(?:\|[-:\s|]+\|\n)((?:\|[^\n]+\|\n?)+)/gi;

/**
 * Pattern to extract filter context from the message
 */
const FILTER_PATTERNS = [
  /(?:Braak|Braak\s*Stage)\s*[><=]+\s*(\w+)/gi,
  /(?:RIN|RIN\s*Score)\s*[><=]+\s*([\d.]+)/gi,
  /(?:Age)\s*[><=]+\s*(\d+)/gi,
  /(?:diagnosis|diagnosed\s*with)\s*[:\s]*([A-Za-z'\s]+?)(?:\.|,|$)/gi,
];

/**
 * Parse an agent message to extract sample recommendations
 */
export function parseSampleRecommendations(text: string): ParsedSampleData {
  const result: ParsedSampleData = {
    hasSamples: false,
    samples: [],
    filters: [],
    beforeTable: text,
    afterTable: "",
  };

  // Find sample table in the message
  const tableMatch = text.match(SAMPLE_TABLE_PATTERN);
  if (!tableMatch) {
    return result;
  }

  // Extract text before and after the table
  const tableIndex = text.indexOf(tableMatch[0]);
  result.beforeTable = text.slice(0, tableIndex).trim();
  result.afterTable = text.slice(tableIndex + tableMatch[0].length).trim();

  // Parse the table
  const samples = parseMarkdownTable(tableMatch[0]);
  if (samples.length > 0) {
    result.hasSamples = true;
    result.samples = samples;
  }

  // Extract filters from context
  result.filters = extractFilters(result.beforeTable);

  return result;
}

/**
 * Parse a markdown table into sample objects
 */
function parseMarkdownTable(tableText: string): RecommendedSample[] {
  const lines = tableText.trim().split("\n").filter((line) => line.trim());
  if (lines.length < 3) return []; // Need header, separator, and at least one data row

  // Parse header to get column indices
  const headerLine = lines[0];
  const headers = headerLine
    .split("|")
    .map((h) => h.trim().toLowerCase())
    .filter((h) => h);

  // Find column indices
  const columnMap: Record<string, number> = {};
  headers.forEach((header, index) => {
    // Normalize header names
    if (header.includes("sample") || header.includes("external") || header.includes("subject") || header === "id") {
      columnMap.id = index;
    } else if (header.includes("rin")) {
      columnMap.rin = index;
    } else if (header.includes("age")) {
      columnMap.age = index;
    } else if (header.includes("sex") || header.includes("gender")) {
      columnMap.sex = index;
    } else if (header.includes("diagnosis") || header.includes("primary")) {
      columnMap.diagnosis = index;
    } else if (header.includes("braak")) {
      columnMap.braak = index;
    } else if (header.includes("pmi") || header.includes("postmortem")) {
      columnMap.pmi = index;
    } else if (header.includes("source") || header.includes("bank")) {
      columnMap.source = index;
    } else if (header.includes("type") || header.includes("preservation") || header.includes("format")) {
      columnMap.type = index;
    } else if (header.includes("price") || header.includes("cost")) {
      columnMap.price = index;
    }
  });

  // Skip separator line (index 1)
  const dataLines = lines.slice(2);

  // Parse data rows
  const samples: RecommendedSample[] = [];
  dataLines.forEach((line, rowIndex) => {
    const cells = line
      .split("|")
      .map((c) => c.trim())
      .filter((c) => c);

    if (cells.length === 0) return;

    const sample: RecommendedSample = {
      id: `sample-${rowIndex}`,
      externalId: columnMap.id !== undefined ? cells[columnMap.id] || `S-${rowIndex + 1}` : `S-${rowIndex + 1}`,
      type: parsePreservationType(columnMap.type !== undefined ? cells[columnMap.type] : ""),
      rin: columnMap.rin !== undefined ? parseFloat(cells[columnMap.rin]) || null : null,
      age: columnMap.age !== undefined ? parseInt(cells[columnMap.age]) || null : null,
      sex: columnMap.sex !== undefined ? parseSex(cells[columnMap.sex]) : null,
      diagnosis: columnMap.diagnosis !== undefined ? cells[columnMap.diagnosis] || "Unknown" : "Unknown",
      braakStage: columnMap.braak !== undefined ? cells[columnMap.braak] || null : null,
      price: columnMap.price !== undefined ? parsePrice(cells[columnMap.price]) : null,
      sourceBank: columnMap.source !== undefined ? cells[columnMap.source] || "Unknown" : "Unknown",
    };

    // Add PMI to details if available
    if (columnMap.pmi !== undefined && cells[columnMap.pmi]) {
      sample.details = {
        ...sample.details,
        additionalMetadata: { pmi: cells[columnMap.pmi] },
      };
    }

    samples.push(sample);
  });

  return samples;
}

/**
 * Parse preservation type from string
 */
function parsePreservationType(value: string): RecommendedSample["type"] {
  const lower = value.toLowerCase();
  if (lower.includes("frozen") || lower.includes("fresh frozen")) {
    return "Frozen";
  }
  if (lower.includes("ffpe") || lower.includes("formalin") || lower.includes("paraffin")) {
    return "FFPE";
  }
  if (lower.includes("fresh")) {
    return "Fresh";
  }
  return "Frozen"; // Default
}

/**
 * Parse sex from string
 */
function parseSex(value: string): "Male" | "Female" | null {
  const lower = value.toLowerCase();
  if (lower.includes("male") || lower === "m") {
    return "Male";
  }
  if (lower.includes("female") || lower === "f") {
    return "Female";
  }
  return null;
}

/**
 * Parse price from string
 */
function parsePrice(value: string): number | null {
  const match = value.match(/[\d.]+/);
  if (match) {
    const price = parseFloat(match[0]);
    return isNaN(price) ? null : price;
  }
  return null;
}

/**
 * Extract filter context from message text
 */
function extractFilters(text: string): ActiveFilter[] {
  const filters: ActiveFilter[] = [];
  let filterId = 1;

  // Look for Braak stage mentions
  const braakMatch = text.match(/Braak\s*(?:stage)?\s*[><=]*\s*([IV0]+|[0-6])/i);
  if (braakMatch) {
    filters.push({
      id: `filter-${filterId++}`,
      label: "Braak",
      value: `≥ ${braakMatch[1]}`,
      removable: false,
    });
  }

  // Look for RIN mentions
  const rinMatch = text.match(/RIN\s*(?:score)?\s*[><=]*\s*([\d.]+)/i);
  if (rinMatch) {
    filters.push({
      id: `filter-${filterId++}`,
      label: "RIN",
      value: `≥ ${rinMatch[1]}`,
      removable: false,
    });
  }

  // Look for diagnosis mentions
  const diagnosisMatch = text.match(/(?:Alzheimer|Parkinson|Control|FTD|Lewy\s*Body)/i);
  if (diagnosisMatch) {
    filters.push({
      id: `filter-${filterId++}`,
      label: "Diagnosis",
      value: diagnosisMatch[0],
      removable: false,
    });
  }

  return filters;
}

/**
 * Check if a message likely contains sample recommendations
 * Quick check before full parsing
 */
export function mightContainSamples(text: string): boolean {
  const keywords = [
    "sample",
    "recommend",
    "found",
    "match",
    "tissue",
    "specimen",
  ];
  const lower = text.toLowerCase();
  return (
    keywords.some((kw) => lower.includes(kw)) &&
    text.includes("|") // Has table-like content
  );
}


/**
 * Column Generator for Cohort Data Table
 * 
 * Analyzes sample data and generates appropriate column configurations
 * with visualizations based on data type and distribution.
 */

import {
  CohortSample,
  ColumnDefinition,
  DEFAULT_COLUMNS,
  VisualizationType,
  CellType,
  NumericStats,
  CategoryDistribution,
  BarChartData,
  HistogramData,
  ScaleChartData,
} from "@/types/cohort";

// ============================================================================
// Constants for Width Calculation
// ============================================================================

/** Approximate character width at 13px font size */
const CHAR_WIDTH = 8;

/** Padding for labels and spacing */
const LABEL_PADDING = 24;

/** Space reserved for value column in horizontal bar charts */
const VALUE_COLUMN_WIDTH = 40;

/** Space for the bar itself (minimum) */
const MIN_BAR_SPACE = 60;

// ============================================================================
// Column Generation
// ============================================================================

/**
 * Generate column definitions from sample data with dynamic widths
 * Uses default columns for known fields, calculates widths based on content
 */
export function generateColumns(samples: CohortSample[]): ColumnDefinition[] {
  // Start with default columns, filter to those with data
  const columns = DEFAULT_COLUMNS.filter((col) => {
    // Check if any sample has data for this field
    return samples.some((sample) => {
      const value = getFieldValue(sample, col.field);
      return value != null && value !== "" && 
        (Array.isArray(value) ? value.length > 0 : true);
    });
  });

  // Calculate dynamic widths for each column
  return columns.map((col) => ({
    ...col,
    width: calculateColumnWidth(col, samples),
  }));
}

/**
 * Calculate optimal column width based on data content
 */
function calculateColumnWidth(
  column: ColumnDefinition,
  samples: CohortSample[]
): number {
  // If explicit width is set, use it
  if (column.width) {
    return column.width;
  }

  const minWidth = column.minWidth ?? 120;
  const maxWidth = column.maxWidth ?? 300;

  // Get all values for this field
  const values = samples
    .map((s) => getFieldValue(s, column.field))
    .filter((v) => v != null && v !== "");

  // Find the longest value
  let maxLabelLength = column.label.length; // Start with header label
  
  for (const value of values) {
    if (Array.isArray(value)) {
      // For arrays, consider each item
      for (const item of value) {
        maxLabelLength = Math.max(maxLabelLength, String(item).length);
      }
    } else {
      maxLabelLength = Math.max(maxLabelLength, String(value).length);
    }
  }

  // Calculate width based on visualization type
  let calculatedWidth: number;

  switch (column.visualization) {
    case "horizontal-bar":
      // Label inside bar + bar space + value column + padding
      calculatedWidth = (maxLabelLength * CHAR_WIDTH) + MIN_BAR_SPACE + VALUE_COLUMN_WIDTH + LABEL_PADDING;
      break;
    
    case "vertical-bar":
    case "donut":
      // These have fixed chart sizes, width based on header + padding
      calculatedWidth = Math.max(
        (column.label.length * CHAR_WIDTH) + LABEL_PADDING,
        140 // Minimum for charts
      );
      break;
    
    case "none":
    default:
      // Text columns: based on content width
      calculatedWidth = (maxLabelLength * CHAR_WIDTH) + LABEL_PADDING;
      break;
  }

  // Apply constraints
  return Math.max(minWidth, Math.min(maxWidth, calculatedWidth));
}

/**
 * Get a field value from a sample, supporting nested paths
 */
export function getFieldValue(sample: CohortSample, field: string): unknown {
  if (field.includes(".")) {
    // Handle nested paths like "rawData.braakStage"
    const parts = field.split(".");
    let value: unknown = sample;
    for (const part of parts) {
      if (value == null || typeof value !== "object") return null;
      value = (value as Record<string, unknown>)[part];
    }
    return value;
  }
  return sample[field as keyof CohortSample];
}

// ============================================================================
// Statistics Calculation
// ============================================================================

/**
 * Calculate numeric statistics for a field
 */
export function calculateNumericStats(
  samples: CohortSample[],
  field: string
): NumericStats | null {
  const values = samples
    .map((s) => getFieldValue(s, field))
    .filter((v): v is number => typeof v === "number" && !isNaN(v));

  if (values.length === 0) return null;

  const sorted = [...values].sort((a, b) => a - b);
  const sum = values.reduce((a, b) => a + b, 0);
  const mean = sum / values.length;
  const median =
    sorted.length % 2 === 0
      ? (sorted[sorted.length / 2 - 1] + sorted[sorted.length / 2]) / 2
      : sorted[Math.floor(sorted.length / 2)];

  return {
    min: sorted[0],
    max: sorted[sorted.length - 1],
    mean,
    median,
  };
}

/**
 * Calculate category distribution for a field
 */
export function calculateCategoryDistribution(
  samples: CohortSample[],
  field: string
): CategoryDistribution {
  const distribution: CategoryDistribution = {};

  for (const sample of samples) {
    const value = getFieldValue(sample, field);
    
    if (Array.isArray(value)) {
      // Handle array fields like diagnoses
      for (const item of value) {
        if (item != null && item !== "") {
          const key = String(item);
          distribution[key] = (distribution[key] || 0) + 1;
        }
      }
    } else if (value != null && value !== "") {
      const key = String(value);
      distribution[key] = (distribution[key] || 0) + 1;
    }
  }

  return distribution;
}

// ============================================================================
// Chart Data Preparation
// ============================================================================

/**
 * Prepare horizontal bar chart data from category distribution
 */
export function prepareBarChartData(
  distribution: CategoryDistribution,
  colorMap?: Record<string, string>
): BarChartData[] {
  return Object.entries(distribution)
    .sort((a, b) => b[1] - a[1]) // Sort by count descending
    .map(([label, value]) => ({
      label,
      value,
      color: colorMap?.[label],
    }));
}

/**
 * Prepare histogram data from numeric values
 * 
 * Uses smart binning:
 * - For sparse data (< 15 unique values): each value gets its own bar
 * - For dense data: uses histogram binning with empty bins filtered out
 */
export function prepareHistogramData(
  samples: CohortSample[],
  field: string,
  maxBinCount: number = 10
): HistogramData | null {
  const values = samples
    .map((s) => getFieldValue(s, field))
    .filter((v): v is number => typeof v === "number" && !isNaN(v));

  if (values.length === 0) return null;

  // Calculate median
  const sorted = [...values].sort((a, b) => a - b);
  const median =
    sorted.length % 2 === 0
      ? (sorted[sorted.length / 2 - 1] + sorted[sorted.length / 2]) / 2
      : sorted[Math.floor(sorted.length / 2)];

  // Get unique values
  const uniqueValues = [...new Set(values)].sort((a, b) => a - b);

  // For sparse data (< 15 unique values), use value-based bars (no binning)
  if (uniqueValues.length < 15) {
    const counts = uniqueValues.map(
      (v) => values.filter((x) => x === v).length
    );
    return {
      bins: uniqueValues,
      counts,
      median,
    };
  }

  // For dense data, use histogram binning
  const min = Math.min(...values);
  const max = Math.max(...values);
  
  // Adaptive bin count based on data
  const binCount = Math.min(maxBinCount, Math.ceil(uniqueValues.length / 2));
  const binWidth = (max - min) / binCount;

  // Create bins and count values
  const allBins: number[] = [];
  const allCounts: number[] = new Array(binCount).fill(0);

  for (let i = 0; i < binCount; i++) {
    allBins.push(min + i * binWidth);
  }

  for (const value of values) {
    const binIndex = Math.min(
      Math.floor((value - min) / binWidth),
      binCount - 1
    );
    allCounts[binIndex]++;
  }

  // Filter out empty bins
  const bins: number[] = [];
  const counts: number[] = [];
  
  for (let i = 0; i < allBins.length; i++) {
    if (allCounts[i] > 0) {
      bins.push(allBins[i]);
      counts.push(allCounts[i]);
    }
  }

  return { bins, counts, median };
}

/**
 * Prepare ordinal bar chart data (e.g., Braak stages)
 */
export function prepareOrdinalBarData(
  distribution: CategoryDistribution,
  categories: string[]
): BarChartData[] {
  // Use predefined order
  return categories.map((label) => ({
    label,
    value: distribution[label] || 0,
  }));
}

/**
 * Prepare scale chart data for bounded continuous values (e.g., RIN 1-10)
 */
export function prepareScaleChartData(
  samples: CohortSample[],
  field: string,
  scaleMin: number,
  scaleMax: number
): ScaleChartData | null {
  const values = samples
    .map((s) => getFieldValue(s, field))
    .filter((v): v is number => typeof v === "number" && !isNaN(v));

  if (values.length === 0) return null;

  // Calculate median
  const sorted = [...values].sort((a, b) => a - b);
  const median =
    sorted.length % 2 === 0
      ? (sorted[sorted.length / 2 - 1] + sorted[sorted.length / 2]) / 2
      : sorted[Math.floor(sorted.length / 2)];

  return {
    values,
    min: scaleMin,
    max: scaleMax,
    median,
  };
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Get unique values for a categorical field
 */
export function getUniqueValues(
  samples: CohortSample[],
  field: string
): string[] {
  const values = new Set<string>();

  for (const sample of samples) {
    const value = getFieldValue(sample, field);
    
    if (Array.isArray(value)) {
      for (const item of value) {
        if (item != null && item !== "") {
          values.add(String(item));
        }
      }
    } else if (value != null && value !== "") {
      values.add(String(value));
    }
  }

  return Array.from(values);
}

/**
 * Determine the best visualization type for a field based on data
 */
export function inferVisualizationType(
  samples: CohortSample[],
  field: string,
  dataType: "text" | "categorical" | "ordinal" | "numeric"
): VisualizationType {
  const uniqueValues = getUniqueValues(samples, field);

  if (dataType === "numeric") {
    return "vertical-bar";
  }

  if (dataType === "ordinal") {
    return "vertical-bar";
  }

  if (dataType === "categorical") {
    // Use donut for binary, bar for multi-value
    return uniqueValues.length <= 2 ? "donut" : "horizontal-bar";
  }

  return "none";
}

/**
 * Format a value for display based on data type
 */
export function formatValue(
  value: unknown,
  dataType: string,
  format?: (v: unknown) => string
): string {
  if (format) {
    return format(value);
  }

  if (value == null) {
    return "—";
  }

  if (Array.isArray(value)) {
    return value.join(", ");
  }

  if (typeof value === "number") {
    return value.toFixed(dataType === "numeric" ? 1 : 0);
  }

  return String(value);
}


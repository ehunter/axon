/**
 * Types for the interactive cohort data table
 * 
 * These types define the structure for displaying recommended samples
 * from the chat agent in an interactive tabular view with visualizations.
 */

// ============================================================================
// Sample Data Types
// ============================================================================

/**
 * A sample from the agent's selection
 */
export interface CohortSample {
  id: string;
  externalId: string;
  sourceBank: string;
  group: "case" | "control";
  
  // Demographics
  age: number | null;
  sex: "Male" | "Female" | null;
  race: string | null;
  
  // Clinical
  primaryDiagnosis: string | null;
  diagnoses: string[]; // Can have multiple (primary + co-pathologies)
  braakStage: string | null; // Roman numerals: I, II, III, IV, V, VI
  
  // Quality metrics
  rin: number | null;
  pmi: number | null; // postmortem interval in hours
  ph: number | null;
  
  // Additional data from raw_data JSON
  rawData: Record<string, unknown>;
}

/**
 * Statistics for a cohort selection
 */
export interface CohortStats {
  totalSamples: number;
  caseCount: number;
  controlCount: number;
  
  // Per-field stats
  ageStats: NumericStats | null;
  rinStats: NumericStats | null;
  pmiStats: NumericStats | null;
  
  sexDistribution: CategoryDistribution;
  diagnosisDistribution: CategoryDistribution;
  braakDistribution: CategoryDistribution;
}

export interface NumericStats {
  min: number;
  max: number;
  mean: number;
  median: number;
}

export interface CategoryDistribution {
  [category: string]: number;
}

// ============================================================================
// Column Configuration Types
// ============================================================================

/**
 * Types of visualizations for column headers
 */
export type VisualizationType = 
  | "none"           // No chart, just text preview
  | "horizontal-bar" // Horizontal bar chart for categorical
  | "vertical-bar"   // Vertical bar chart / histogram for numeric
  | "donut"          // Donut/pie chart for binary categorical
  | "scale"          // Scale/strip chart for bounded continuous data (e.g., RIN 1-10)
  ;

/**
 * Types of data cells
 */
export type CellType = 
  | "text"    // Plain text
  | "badge"   // Single badge/pill
  | "badges"  // Multiple badges
  | "numeric" // Numeric value
  ;

/**
 * Column definition for the data table
 */
export interface ColumnDefinition {
  id: string;
  label: string;
  field: keyof CohortSample | string; // Field path in sample data
  
  // Visualization
  visualization: VisualizationType;
  cellType: CellType;
  
  // Display options
  width?: number; // Override width (otherwise calculated dynamically)
  minWidth?: number; // Minimum width constraint
  maxWidth?: number; // Maximum width constraint
  sticky?: boolean; // Sticky column (first column)
  
  // Data type hints for visualization
  dataType: "text" | "categorical" | "ordinal" | "numeric";
  categories?: string[]; // For categorical/ordinal - known categories
  
  // Scale visualization options (for bounded continuous data)
  scaleMin?: number; // Minimum value on scale
  scaleMax?: number; // Maximum value on scale
  
  // Formatting
  format?: (value: unknown) => string;
  
  // Color mapping for badges
  colorMap?: Record<string, string>;
}

/**
 * Default column configurations for known fields
 */
export const DEFAULT_COLUMNS: ColumnDefinition[] = [
  {
    id: "externalId",
    label: "Subject ID",
    field: "externalId",
    visualization: "none",
    cellType: "text",
    minWidth: 140,
    maxWidth: 220,
    sticky: true,
    dataType: "text",
  },
  {
    id: "group",
    label: "Sample Type",
    field: "group",
    visualization: "horizontal-bar",
    cellType: "badge",
    minWidth: 160,
    maxWidth: 220,
    dataType: "categorical",
    categories: ["case", "control"],
    colorMap: {
      case: "teal",
      control: "neutral",
    },
  },
  {
    id: "diagnoses",
    label: "Clinical Diagnosis",
    field: "diagnoses",
    visualization: "horizontal-bar",
    cellType: "badges",
    minWidth: 200,
    maxWidth: 320,
    dataType: "categorical",
  },
  {
    id: "braakStage",
    label: "Braak Score",
    field: "braakStage",
    visualization: "vertical-bar",
    cellType: "text",
    minWidth: 140,
    maxWidth: 180,
    dataType: "ordinal",
    categories: ["0", "I", "II", "III", "IV", "V", "VI"],
  },
  {
    id: "sex",
    label: "Gender",
    field: "sex",
    visualization: "donut",
    cellType: "text",
    minWidth: 140,
    maxWidth: 180,
    dataType: "categorical",
    categories: ["Male", "Female"],
    colorMap: {
      Male: "teal",
      Female: "rose",
    },
  },
  {
    id: "age",
    label: "Age",
    field: "age",
    visualization: "vertical-bar",
    cellType: "numeric",
    minWidth: 120,
    maxWidth: 160,
    dataType: "numeric",
    format: (v) => v != null ? `${v}` : "—",
  },
  {
    id: "pmi",
    label: "PMI",
    field: "pmi",
    visualization: "vertical-bar",
    cellType: "numeric",
    minWidth: 120,
    maxWidth: 160,
    dataType: "numeric",
    format: (v) => v != null ? `${Number(v).toFixed(1)}h` : "—",
  },
  {
    id: "rin",
    label: "RIN",
    field: "rin",
    visualization: "scale",
    cellType: "numeric",
    minWidth: 200,
    maxWidth: 260,
    dataType: "numeric",
    scaleMin: 1,
    scaleMax: 10,
    format: (v) => v != null ? `${Number(v).toFixed(1)}` : "—",
  },
  {
    id: "sourceBank",
    label: "Source",
    field: "sourceBank",
    visualization: "horizontal-bar",
    cellType: "text",
    minWidth: 180,
    maxWidth: 280,
    dataType: "categorical",
  },
];

// ============================================================================
// Chart Data Types
// ============================================================================

export interface BarChartData {
  label: string;
  value: number;
  color?: string;
}

export interface DonutChartData {
  label: string;
  value: number;
  color: string;
}

export interface HistogramData {
  bins: number[];
  counts: number[];
  median?: number;
}

export interface ScaleChartData {
  values: number[];
  min: number;
  max: number;
  median?: number;
}


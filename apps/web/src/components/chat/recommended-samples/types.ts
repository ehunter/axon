/**
 * Types for the Interactive Recommended Samples Widget
 */

/**
 * A recommended sample from the agent
 */
export interface RecommendedSample {
  id: string;
  externalId: string;
  type: "Frozen" | "FFPE" | "Fresh";
  rin: number | null;
  age: number | null;
  sex: "Male" | "Female" | null;
  race: string | null;
  diagnosis: string;
  braakStage: string | null;
  price: number | null;
  sourceBank: string;
  pmi: number | null;
  coPathologies: string | null;
  // Extended details for accordion
  details?: {
    pathologyNotes?: string;
    donorHistory?: string;
    tissueRegion?: string;
    collectionDate?: string;
    additionalMetadata?: Record<string, unknown>;
  };
}

/**
 * Active filter applied to the recommendation
 */
export interface ActiveFilter {
  id: string;
  label: string;
  value: string;
  removable?: boolean;
}

/**
 * Statistics calculated from the recommended samples
 */
export interface SampleStats {
  count: number;
  avgRin: number | null;
  meanAge: number | null;
  medianBraak: string | null;
  avgPrice: number | null;
}

/**
 * Order configuration form state
 */
export interface OrderConfig {
  format: "slide" | "block" | "shavings";
  quantity: number;
  shippingPriority: "standard" | "overnight";
}

/**
 * Props for the main RecommendedSamplesCard
 */
export interface RecommendedSamplesCardProps {
  samples: RecommendedSample[];
  filters?: ActiveFilter[];
  title?: string;
  onSaveToCohort?: (sampleIds: string[]) => void;
  onSubmitOrder?: (sampleIds: string[], config: OrderConfig) => void;
  onFilterRemove?: (filterId: string) => void;
}

/**
 * Selection state for the widget
 */
export interface SelectionState {
  selectedIds: Set<string>;
  isConfiguring: boolean;
  expandedRowId: string | null;
  orderSuccess: boolean;
}

/**
 * Price calculation result
 */
export interface PriceEstimate {
  subtotal: number;
  shippingCost: number;
  total: number;
}


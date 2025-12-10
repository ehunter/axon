/**
 * Hook for fetching and managing the current sample selection
 * 
 * Retrieves samples selected by the agent in a conversation
 * and transforms them for display in the cohort data table.
 */

import { useQuery } from "@tanstack/react-query";
import { CohortSample, CohortStats } from "@/types/cohort";
import {
  calculateNumericStats,
  calculateCategoryDistribution,
} from "@/lib/cohort/column-generator";

// ============================================================================
// API Response Types
// ============================================================================

interface SelectionSample {
  id: string;
  sample_external_id: string;
  sample_group: "case" | "control";
  diagnosis: string | null;
  age: number | null;
  sex: string | null;
  source_bank: string | null;
  added_at: string;
  // Full sample data when available
  sample_data?: {
    rin_score: number | null;
    postmortem_interval_hours: number | null;
    ph_level: number | null;
    primary_diagnosis: string | null;
    donor_race: string | null;
    raw_data: Record<string, unknown>;
  };
}

interface SelectionResponse {
  conversation_id: string;
  samples: SelectionSample[];
  case_count: number;
  control_count: number;
}

// ============================================================================
// Data Transformation
// ============================================================================

/**
 * Transform API response to CohortSample format
 */
function transformSample(apiSample: SelectionSample): CohortSample {
  const rawData = apiSample.sample_data?.raw_data || {};
  
  // Extract Braak stage from raw_data
  let braakStage: string | null = null;
  if (rawData.braak_stage_nft != null) {
    braakStage = String(rawData.braak_stage_nft);
  } else if (rawData.braak_stage != null) {
    braakStage = String(rawData.braak_stage);
  }

  // Build diagnoses array
  const diagnoses: string[] = [];
  if (apiSample.diagnosis) {
    diagnoses.push(apiSample.diagnosis);
  }
  if (apiSample.sample_data?.primary_diagnosis && 
      apiSample.sample_data.primary_diagnosis !== apiSample.diagnosis) {
    diagnoses.push(apiSample.sample_data.primary_diagnosis);
  }
  // Add co-pathologies from raw_data if available
  if (rawData.co_pathologies && Array.isArray(rawData.co_pathologies)) {
    diagnoses.push(...rawData.co_pathologies.map(String));
  }

  return {
    id: apiSample.id,
    externalId: apiSample.sample_external_id,
    sourceBank: apiSample.source_bank || "Unknown",
    group: apiSample.sample_group === "case" ? "case" : "control",
    age: apiSample.age,
    sex: apiSample.sex === "Male" || apiSample.sex === "Female" 
      ? apiSample.sex 
      : apiSample.sex === "M" ? "Male" : apiSample.sex === "F" ? "Female" : null,
    race: apiSample.sample_data?.donor_race || null,
    primaryDiagnosis: apiSample.diagnosis,
    diagnoses: [...new Set(diagnoses)], // Remove duplicates
    braakStage,
    rin: apiSample.sample_data?.rin_score || null,
    pmi: apiSample.sample_data?.postmortem_interval_hours || null,
    ph: apiSample.sample_data?.ph_level || null,
    rawData,
  };
}

/**
 * Calculate statistics for a cohort
 */
function calculateStats(samples: CohortSample[]): CohortStats {
  const cases = samples.filter((s) => s.group === "case");
  const controls = samples.filter((s) => s.group === "control");

  return {
    totalSamples: samples.length,
    caseCount: cases.length,
    controlCount: controls.length,
    ageStats: calculateNumericStats(samples, "age"),
    rinStats: calculateNumericStats(samples, "rin"),
    pmiStats: calculateNumericStats(samples, "pmi"),
    sexDistribution: calculateCategoryDistribution(samples, "sex"),
    diagnosisDistribution: calculateCategoryDistribution(samples, "diagnoses"),
    braakDistribution: calculateCategoryDistribution(samples, "braakStage"),
  };
}

// ============================================================================
// Hook
// ============================================================================

interface UseSelectionOptions {
  conversationId?: string | null;
  enabled?: boolean;
}

interface UseSelectionResult {
  samples: CohortSample[];
  stats: CohortStats | null;
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
}

/**
 * Hook to fetch the current sample selection for a conversation
 */
export function useSelection({
  conversationId,
  enabled = true,
}: UseSelectionOptions = {}): UseSelectionResult {
  const query = useQuery<SelectionResponse, Error>({
    queryKey: ["selection", conversationId],
    queryFn: async () => {
      const url = conversationId
        ? `/api/selection?conversationId=${conversationId}`
        : "/api/selection";
      
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error("Failed to fetch selection");
      }
      return response.json();
    },
    enabled: enabled && !!conversationId,
    staleTime: 1000 * 60, // 1 minute
  });

  const samples = query.data?.samples.map(transformSample) || [];
  const stats = samples.length > 0 ? calculateStats(samples) : null;

  return {
    samples,
    stats,
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
  };
}

/**
 * Hook to use with samples passed directly (not fetched)
 * Useful when displaying samples from chat context
 */
export function useSelectionFromSamples(
  rawSamples: SelectionSample[] | null
): Omit<UseSelectionResult, "refetch"> {
  const samples = rawSamples?.map(transformSample) || [];
  const stats = samples.length > 0 ? calculateStats(samples) : null;

  return {
    samples,
    stats,
    isLoading: false,
    error: null,
  };
}


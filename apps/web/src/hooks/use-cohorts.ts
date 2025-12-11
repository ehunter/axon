/**
 * Hook to fetch saved cohorts from the API
 */

import { useState, useEffect } from "react";

export interface Cohort {
  id: string;
  name: string;
  description: string | null;
  sample_count: number;
  case_count: number;
  control_count: number;
  created_at: string;
  updated_at: string;
}

interface UseCohorts {
  cohorts: Cohort[];
  isLoading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useCohorts(limit: number = 5): UseCohorts {
  const [cohorts, setCohorts] = useState<Cohort[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCohorts = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await fetch(`/api/cohorts?limit=${limit}`);
      
      if (!response.ok) {
        throw new Error("Failed to fetch cohorts");
      }
      
      const data = await response.json();
      setCohorts(data);
    } catch (err) {
      console.error("Error fetching cohorts:", err);
      setError(err instanceof Error ? err.message : "Unknown error");
      setCohorts([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCohorts();
  }, [limit]);

  return {
    cohorts,
    isLoading,
    error,
    refetch: fetchCohorts,
  };
}


/**
 * Cohort Detail Page
 *
 * Displays a saved cohort with the interactive data table.
 */

"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Folder, Trash2 } from "lucide-react";
import Link from "next/link";
import { SampleDataTable } from "@/components/cohort";
import { CohortSample } from "@/types/cohort";

interface APICohortSample {
  id: string;
  external_id: string;
  sample_group: string;
  diagnosis: string | null;
  neuropathology_diagnosis: string | null;
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

interface CohortDetail {
  id: string;
  name: string;
  description: string | null;
  sample_count: number;
  case_count: number;
  control_count: number;
  created_at: string;
  updated_at: string;
  samples: APICohortSample[];
}

export default function CohortDetailPage() {
  const params = useParams();
  const router = useRouter();
  const cohortId = params.id as string;

  const [cohort, setCohort] = useState<CohortDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    const fetchCohort = async () => {
      try {
        setIsLoading(true);
        const response = await fetch(`/api/cohorts/${cohortId}`);
        
        if (!response.ok) {
          if (response.status === 404) {
            setError("Cohort not found");
          } else {
            setError("Failed to load cohort");
          }
          return;
        }

        const data = await response.json();
        setCohort(data);
      } catch (err) {
        console.error("Error fetching cohort:", err);
        setError("Failed to load cohort");
      } finally {
        setIsLoading(false);
      }
    };

    if (cohortId) {
      fetchCohort();
    }
  }, [cohortId]);

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this cohort?")) {
      return;
    }

    try {
      setIsDeleting(true);
      const response = await fetch(`/api/cohorts/${cohortId}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error("Failed to delete cohort");
      }

      router.push("/cohorts");
    } catch (err) {
      console.error("Error deleting cohort:", err);
      alert("Failed to delete cohort");
    } finally {
      setIsDeleting(false);
    }
  };

  // Transform API samples to CohortSample format for the table
  const transformSamples = (apiSamples: APICohortSample[]): CohortSample[] => {
    return apiSamples.map((s) => ({
      id: s.id,
      externalId: s.external_id,
      sourceBank: s.source_bank || "",
      group: s.sample_group as "case" | "control",
      age: s.age,
      sex: s.sex as "Male" | "Female" | null,
      race: s.race,
      neuropathologyDiagnosis: s.neuropathology_diagnosis,
      primaryDiagnosis: s.diagnosis,
      diagnoses: s.diagnoses || [],
      braakStage: s.braak_stage,
      rin: s.rin,
      pmi: s.pmi,
      ph: s.ph,
      rawData: {},
    }));
  };

  if (isLoading) {
    return (
      <div className="flex flex-col h-full">
        <div className="flex-1 flex flex-col bg-surface shadow-sm overflow-hidden">
          <div className="flex-1 overflow-auto p-10">
            <div className="animate-pulse">
              <div className="h-8 bg-muted rounded w-1/3 mb-4" />
              <div className="h-4 bg-muted rounded w-1/2 mb-8" />
              <div className="h-64 bg-muted rounded" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !cohort) {
    return (
      <div className="flex flex-col h-full">
        <div className="flex-1 flex flex-col bg-surface shadow-sm overflow-hidden">
          <div className="flex-1 overflow-auto p-10">
            <Link
              href="/cohorts"
              className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground mb-6"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Cohorts
            </Link>
            <div className="text-center py-12">
              <Folder className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-foreground mb-2">
                {error || "Cohort not found"}
              </h2>
              <p className="text-muted-foreground">
                This cohort may have been deleted or doesn't exist.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const samples = transformSamples(cohort.samples);

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 flex flex-col bg-surface shadow-sm overflow-hidden">
        <div className="flex-1 overflow-auto p-10">
          {/* Back link and delete button */}
          <div className="flex items-center justify-between mb-6">
            <Link
              href="/cohorts"
              className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Cohorts
            </Link>
            <button
              onClick={handleDelete}
              disabled={isDeleting}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium border border-red-500/30 text-red-400 hover:bg-red-500/10 transition-colors disabled:opacity-50"
            >
              <Trash2 className="h-4 w-4" />
              {isDeleting ? "Deleting..." : "Delete"}
            </button>
          </div>

          {/* Interactive data table */}
          <SampleDataTable
            samples={samples}
            title={cohort.name}
            onExport={() => alert("Export functionality coming soon!")}
          />
        </div>
      </div>
    </div>
  );
}

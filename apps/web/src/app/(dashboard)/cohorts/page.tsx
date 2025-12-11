/**
 * Cohorts List Page
 *
 * Displays all saved cohorts.
 */

"use client";

import { useCohorts } from "@/hooks/use-cohorts";
import { Folder, Users, FlaskConical } from "lucide-react";
import Link from "next/link";

export default function CohortsPage() {
  const { cohorts, isLoading, error } = useCohorts(50);

  if (isLoading) {
    return (
      <div className="flex-1 p-8">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-2xl font-semibold text-foreground mb-6">Cohorts</h1>
          <div className="animate-pulse space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-20 bg-muted rounded-lg" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 p-8">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-2xl font-semibold text-foreground mb-6">Cohorts</h1>
          <div className="text-center py-12">
            <p className="text-muted-foreground">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 p-8 overflow-y-auto">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-semibold text-foreground mb-6">Cohorts</h1>

        {cohorts.length === 0 ? (
          <div className="text-center py-12 border border-dashed border-muted-foreground/30 rounded-lg">
            <Folder className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h2 className="text-lg font-medium text-foreground mb-2">
              No saved cohorts
            </h2>
            <p className="text-muted-foreground max-w-md mx-auto">
              Save samples from a chat conversation to create a cohort for your research project.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {cohorts.map((cohort) => (
              <Link
                key={cohort.id}
                href={`/cohorts/${cohort.id}`}
                className="block p-4 border border-muted-foreground/30 rounded-lg hover:bg-muted/30 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="text-base font-medium text-foreground mb-1">
                      {cohort.name}
                    </h2>
                    {cohort.description && (
                      <p className="text-sm text-muted-foreground mb-2">
                        {cohort.description}
                      </p>
                    )}
                    <div className="flex items-center gap-4 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Users className="h-3 w-3" />
                        {cohort.sample_count} samples
                      </span>
                      <span className="flex items-center gap-1">
                        <FlaskConical className="h-3 w-3" />
                        {cohort.case_count} cases, {cohort.control_count} controls
                      </span>
                    </div>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {new Date(cohort.created_at).toLocaleDateString()}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}


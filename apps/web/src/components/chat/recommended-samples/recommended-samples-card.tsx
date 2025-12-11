/**
 * Recommended Samples Card
 *
 * Interactive widget for displaying and selecting recommended samples.
 * Renders in the chat feed as a specialized card component.
 */

"use client";

import { useState, useMemo, useCallback } from "react";
import {
  RecommendedSample,
  ActiveFilter,
  OrderConfig,
  SelectionState,
  SampleStats,
  RecommendedSamplesCardProps,
} from "./types";
import { CardHeader } from "./card-header";
import { StatsBar } from "./stats-bar";
import { SampleTable } from "./sample-table";
import { CardFooter } from "./card-footer";
import { ConfigForm } from "./config-form";
import { SaveCohortForm } from "./save-cohort-form";
import { CheckCircle2, FolderPlus } from "lucide-react";

/**
 * Calculate two-sample t-test p-value (Welch's t-test)
 * Returns null if either group has fewer than 2 samples
 */
function calculateTTestPValue(group1: number[], group2: number[]): number | null {
  if (group1.length < 2 || group2.length < 2) return null;

  const n1 = group1.length;
  const n2 = group2.length;
  
  const mean1 = group1.reduce((a, b) => a + b, 0) / n1;
  const mean2 = group2.reduce((a, b) => a + b, 0) / n2;
  
  const var1 = group1.reduce((sum, x) => sum + (x - mean1) ** 2, 0) / (n1 - 1);
  const var2 = group2.reduce((sum, x) => sum + (x - mean2) ** 2, 0) / (n2 - 1);
  
  // Welch's t-test
  const se = Math.sqrt(var1 / n1 + var2 / n2);
  if (se === 0) return 1; // No variance means no difference
  
  const t = (mean1 - mean2) / se;
  
  // Welch-Satterthwaite degrees of freedom
  const df = ((var1 / n1 + var2 / n2) ** 2) /
    ((var1 / n1) ** 2 / (n1 - 1) + (var2 / n2) ** 2 / (n2 - 1));
  
  // Approximate p-value using t-distribution CDF
  // Using a simple approximation for the t-distribution
  const pValue = 2 * (1 - tCDF(Math.abs(t), df));
  
  return Math.max(0, Math.min(1, pValue));
}

/**
 * Approximate cumulative distribution function for t-distribution
 * Using the approximation from Abramowitz and Stegun
 */
function tCDF(t: number, df: number): number {
  const x = df / (df + t * t);
  const a = df / 2;
  const b = 0.5;
  
  // Incomplete beta function approximation
  const beta = incompleteBeta(x, a, b);
  
  return t >= 0 ? 1 - 0.5 * beta : 0.5 * beta;
}

/**
 * Incomplete beta function approximation
 */
function incompleteBeta(x: number, a: number, b: number): number {
  if (x === 0) return 0;
  if (x === 1) return 1;
  
  // Use continued fraction for better accuracy
  const bt = Math.exp(
    lgamma(a + b) - lgamma(a) - lgamma(b) +
    a * Math.log(x) + b * Math.log(1 - x)
  );
  
  if (x < (a + 1) / (a + b + 2)) {
    return bt * betaCF(x, a, b) / a;
  } else {
    return 1 - bt * betaCF(1 - x, b, a) / b;
  }
}

/**
 * Continued fraction for incomplete beta function
 */
function betaCF(x: number, a: number, b: number): number {
  const maxIterations = 100;
  const epsilon = 1e-10;
  
  let c = 1;
  let d = 1 / (1 - (a + b) * x / (a + 1));
  let h = d;
  
  for (let m = 1; m <= maxIterations; m++) {
    const m2 = 2 * m;
    
    // Even step
    let aa = m * (b - m) * x / ((a + m2 - 1) * (a + m2));
    d = 1 / (1 + aa * d);
    c = 1 + aa / c;
    h *= d * c;
    
    // Odd step
    aa = -(a + m) * (a + b + m) * x / ((a + m2) * (a + m2 + 1));
    d = 1 / (1 + aa * d);
    c = 1 + aa / c;
    const del = d * c;
    h *= del;
    
    if (Math.abs(del - 1) < epsilon) break;
  }
  
  return h;
}

/**
 * Log gamma function approximation (Stirling's approximation)
 */
function lgamma(x: number): number {
  const coefficients = [
    76.18009172947146,
    -86.50532032941677,
    24.01409824083091,
    -1.231739572450155,
    0.001208650973866179,
    -0.000005395239384953,
  ];
  
  let y = x;
  let tmp = x + 5.5;
  tmp -= (x + 0.5) * Math.log(tmp);
  
  let ser = 1.000000000190015;
  for (let j = 0; j < 6; j++) {
    ser += coefficients[j] / ++y;
  }
  
  return -tmp + Math.log(2.5066282746310005 * ser / x);
}

export function RecommendedSamplesCard({
  samples,
  filters = [],
  title = "Recommended Samples",
  onSaveToCohort,
  onSubmitOrder,
  onFilterRemove,
}: RecommendedSamplesCardProps) {
  // Selection state
  const [state, setState] = useState<SelectionState>({
    selectedIds: new Set(),
    isConfiguring: false,
    expandedRowId: null,
    orderSuccess: false,
  });

  // Collapsed groups state
  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(new Set());

  // Save to cohort state
  const [isSavingCohort, setIsSavingCohort] = useState(false);
  const [cohortSaveSuccess, setCohortSaveSuccess] = useState<string | null>(null);

  // Order configuration
  const [orderConfig, setOrderConfig] = useState<OrderConfig>({
    format: "slide",
    quantity: 1,
    shippingPriority: "standard",
  });

  // Calculate statistics
  const stats = useMemo<SampleStats>(() => {
    const rinValues = samples.map((s) => s.rin).filter((r): r is number => r != null);
    const ageValues = samples.map((s) => s.age).filter((a): a is number => a != null);
    const pmiValues = samples.map((s) => s.pmi).filter((p): p is number => p != null);
    const braakValues = samples
      .map((s) => s.braakStage)
      .filter((b): b is string => b != null && b !== "");

    // Calculate median Braak
    const braakOrder = ["0", "I", "II", "III", "IV", "V", "VI"];
    const sortedBraak = braakValues
      .map((b) => braakOrder.indexOf(b))
      .filter((i) => i >= 0)
      .sort((a, b) => a - b);
    const medianBraakIndex =
      sortedBraak.length > 0
        ? sortedBraak[Math.floor(sortedBraak.length / 2)]
        : null;

    // Separate case and control samples for p-value calculation
    const caseSamples = samples.filter((s) => s.sampleGroup === "case");
    const controlSamples = samples.filter((s) => s.sampleGroup === "control");

    // Calculate p-values for Age and RIN (comparing case vs control)
    const caseAges = caseSamples.map((s) => s.age).filter((a): a is number => a != null);
    const controlAges = controlSamples.map((s) => s.age).filter((a): a is number => a != null);
    const agePValue = calculateTTestPValue(caseAges, controlAges);

    const caseRins = caseSamples.map((s) => s.rin).filter((r): r is number => r != null);
    const controlRins = controlSamples.map((s) => s.rin).filter((r): r is number => r != null);
    const rinPValue = calculateTTestPValue(caseRins, controlRins);

    const casePmis = caseSamples.map((s) => s.pmi).filter((p): p is number => p != null);
    const controlPmis = controlSamples.map((s) => s.pmi).filter((p): p is number => p != null);
    const pmiPValue = calculateTTestPValue(casePmis, controlPmis);

    return {
      count: samples.length,
      avgRin: rinValues.length > 0 ? rinValues.reduce((a, b) => a + b, 0) / rinValues.length : null,
      meanAge: ageValues.length > 0 ? ageValues.reduce((a, b) => a + b, 0) / ageValues.length : null,
      medianBraak: medianBraakIndex != null ? braakOrder[medianBraakIndex] : null,
      avgPmi: pmiValues.length > 0 ? pmiValues.reduce((a, b) => a + b, 0) / pmiValues.length : null,
      agePValue,
      rinPValue,
      pmiPValue,
    };
  }, [samples]);

  // Selection handlers
  const handleSelectAll = useCallback((checked: boolean) => {
    setState((prev) => ({
      ...prev,
      selectedIds: checked ? new Set(samples.map((s) => s.id)) : new Set(),
    }));
  }, [samples]);

  const handleSelectOne = useCallback((id: string, checked: boolean) => {
    setState((prev) => {
      const newSelected = new Set(prev.selectedIds);
      if (checked) {
        newSelected.add(id);
      } else {
        newSelected.delete(id);
      }
      return { ...prev, selectedIds: newSelected };
    });
  }, []);

  const handleExpandRow = useCallback((id: string | null) => {
    setState((prev) => ({
      ...prev,
      expandedRowId: prev.expandedRowId === id ? null : id,
    }));
  }, []);

  const handleToggleGroup = useCallback((groupId: string) => {
    setCollapsedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(groupId)) {
        next.delete(groupId);
      } else {
        next.add(groupId);
      }
      return next;
    });
  }, []);

  // Action handlers
  const handleConfigureOrder = useCallback(() => {
    setState((prev) => ({ ...prev, isConfiguring: true }));
  }, []);

  const handleCancelConfig = useCallback(() => {
    setState((prev) => ({ ...prev, isConfiguring: false }));
  }, []);

  const handleSaveToCohort = useCallback(() => {
    setIsSavingCohort(true);
  }, []);

  const handleCancelSaveCohort = useCallback(() => {
    setIsSavingCohort(false);
  }, []);

  const handleConfirmSaveCohort = useCallback(async (name: string, description?: string) => {
    try {
      const selectedSamplesList = samples.filter((s) => state.selectedIds.has(s.id));
      
      const response = await fetch("/api/cohorts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          description,
          samples: selectedSamplesList.map((s) => ({
            external_id: s.externalId,
            source_bank: s.sourceBank, // CRITICAL: Include source_bank for unique identification
            sample_group: s.sampleGroup,
          })),
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to save cohort");
      }

      const data = await response.json();
      setIsSavingCohort(false);
      setCohortSaveSuccess(name);
      
      // Also call the prop callback if provided
      if (onSaveToCohort) {
        onSaveToCohort(Array.from(state.selectedIds));
      }
      
      // Clear success message after 3 seconds
      setTimeout(() => setCohortSaveSuccess(null), 3000);
    } catch (error) {
      console.error("Error saving cohort:", error);
      // TODO: Show error to user
    }
  }, [samples, state.selectedIds, onSaveToCohort]);

  const handleSubmitOrder = useCallback(() => {
    if (onSubmitOrder) {
      onSubmitOrder(Array.from(state.selectedIds), orderConfig);
    }
    setState((prev) => ({
      ...prev,
      isConfiguring: false,
      orderSuccess: true,
    }));
  }, [onSubmitOrder, state.selectedIds, orderConfig]);

  // Get selected samples for price calculation
  const selectedSamples = useMemo(
    () => samples.filter((s) => state.selectedIds.has(s.id)),
    [samples, state.selectedIds]
  );

  // Success state
  if (state.orderSuccess) {
    return (
      <div className="bg-transparent rounded-xl border border-muted-foreground/30 overflow-hidden">
        <div className="flex items-center gap-3 px-5 py-4 bg-teal-900/20 border-b border-teal-700/30">
          <CheckCircle2 className="h-5 w-5 text-teal-400" />
          <div>
            <p className="text-base font-medium text-teal-100">
              Request Submitted Successfully
            </p>
            <p className="text-sm text-teal-200/70">
              {selectedSamples.length} sample{selectedSamples.length !== 1 ? "s" : ""} added to your requests
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-transparent rounded-xl border border-muted-foreground/30 overflow-hidden">
      {/* Header with title and filter chips */}
      <CardHeader
        title={title}
        count={stats.count}
        filters={filters}
        onFilterRemove={onFilterRemove}
      />

      {/* Statistics summary bar */}
      <StatsBar stats={stats} />

      {/* Interactive table */}
      <SampleTable
        samples={samples}
        selectedIds={state.selectedIds}
        expandedRowId={state.expandedRowId}
        collapsedGroups={collapsedGroups}
        onSelectAll={handleSelectAll}
        onSelectOne={handleSelectOne}
        onExpandRow={handleExpandRow}
        onToggleGroup={handleToggleGroup}
      />

      {/* Footer with selection count and actions */}
      <CardFooter
        selectedCount={state.selectedIds.size}
        isConfiguring={state.isConfiguring}
        onConfigureOrder={handleConfigureOrder}
        onSaveToCohort={handleSaveToCohort}
      />

      {/* Cohort save success message */}
      {cohortSaveSuccess && (
        <div className="flex items-center gap-2 px-5 py-3 bg-teal-900/20 border-t border-teal-700/30">
          <FolderPlus className="h-4 w-4 text-teal-400" />
          <span className="text-sm text-teal-200">
            Saved to cohort: <strong>{cohortSaveSuccess}</strong>
          </span>
        </div>
      )}

      {/* Save to cohort form */}
      {isSavingCohort && (
        <SaveCohortForm
          selectedCount={state.selectedIds.size}
          onSave={handleConfirmSaveCohort}
          onCancel={handleCancelSaveCohort}
        />
      )}

      {/* Inline configuration form (progressive disclosure) */}
      {state.isConfiguring && (
        <ConfigForm
          selectedSamples={selectedSamples}
          config={orderConfig}
          onConfigChange={setOrderConfig}
          onSubmit={handleSubmitOrder}
          onCancel={handleCancelConfig}
        />
      )}
    </div>
  );
}


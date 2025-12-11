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
import { CheckCircle2 } from "lucide-react";

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

    return {
      count: samples.length,
      avgRin: rinValues.length > 0 ? rinValues.reduce((a, b) => a + b, 0) / rinValues.length : null,
      meanAge: ageValues.length > 0 ? ageValues.reduce((a, b) => a + b, 0) / ageValues.length : null,
      medianBraak: medianBraakIndex != null ? braakOrder[medianBraakIndex] : null,
      avgPmi: pmiValues.length > 0 ? pmiValues.reduce((a, b) => a + b, 0) / pmiValues.length : null,
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

  // Action handlers
  const handleConfigureOrder = useCallback(() => {
    setState((prev) => ({ ...prev, isConfiguring: true }));
  }, []);

  const handleCancelConfig = useCallback(() => {
    setState((prev) => ({ ...prev, isConfiguring: false }));
  }, []);

  const handleSaveToCohort = useCallback(() => {
    if (onSaveToCohort) {
      onSaveToCohort(Array.from(state.selectedIds));
    }
  }, [onSaveToCohort, state.selectedIds]);

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
        onSelectAll={handleSelectAll}
        onSelectOne={handleSelectOne}
        onExpandRow={handleExpandRow}
      />

      {/* Footer with selection count and actions */}
      <CardFooter
        selectedCount={state.selectedIds.size}
        isConfiguring={state.isConfiguring}
        onConfigureOrder={handleConfigureOrder}
        onSaveToCohort={handleSaveToCohort}
      />

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


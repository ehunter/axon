/**
 * Sample Table
 *
 * Interactive table with checkboxes, expandable rows, and highlighting.
 * Supports grouped sections for cases and controls.
 */

"use client";

import { useMemo } from "react";
import { RecommendedSample, SampleGroup } from "./types";
import { SampleRow } from "./sample-row";
import { ChevronDown } from "lucide-react";

interface SampleTableProps {
  samples: RecommendedSample[];
  selectedIds: Set<string>;
  expandedRowId: string | null;
  collapsedGroups?: Set<string>;
  onSelectAll: (checked: boolean) => void;
  onSelectOne: (id: string, checked: boolean) => void;
  onExpandRow: (id: string | null) => void;
  onToggleGroup?: (groupId: string) => void;
}

export function SampleTable({
  samples,
  selectedIds,
  expandedRowId,
  collapsedGroups = new Set(),
  onSelectAll,
  onSelectOne,
  onExpandRow,
  onToggleGroup,
}: SampleTableProps) {
  const allSelected = samples.length > 0 && selectedIds.size === samples.length;
  const someSelected = selectedIds.size > 0 && selectedIds.size < samples.length;

  // Group samples by sampleGroup
  const groups = useMemo(() => {
    const caseSamples = samples.filter((s) => s.sampleGroup === "case");
    const controlSamples = samples.filter((s) => s.sampleGroup === "control");
    
    const result: SampleGroup[] = [];
    if (caseSamples.length > 0) {
      result.push({ id: "case", label: "Case Samples", samples: caseSamples });
    }
    if (controlSamples.length > 0) {
      result.push({ id: "control", label: "Control Samples", samples: controlSamples });
    }
    
    // If no groups detected, treat all as cases
    if (result.length === 0 && samples.length > 0) {
      result.push({ id: "case", label: "Samples", samples });
    }
    
    return result;
  }, [samples]);

  const hasMultipleGroups = groups.length > 1;

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="bg-[#212636] text-left border-b border-muted-foreground/30">
            {/* Checkbox column */}
            <th className="w-12 px-3 py-2">
              <Checkbox
                checked={allSelected}
                indeterminate={someSelected}
                onChange={(checked) => onSelectAll(checked)}
                aria-label="Select all samples"
              />
            </th>
            <th className="px-3 py-2 text-sm font-semibold text-foreground">
              Sample ID
            </th>
            <th className="px-3 py-2 text-sm font-semibold text-foreground">
              Source
            </th>
            <th className="px-3 py-2 text-sm font-semibold text-foreground">
              Age/Sex
            </th>
            <th className="px-3 py-2 text-sm font-semibold text-foreground">
              Braak
            </th>
            <th className="px-3 py-2 text-sm font-semibold text-foreground">
              PMI
            </th>
            <th className="px-3 py-2 text-sm font-semibold text-foreground">
              Type
            </th>
            {/* Expand column */}
            <th className="w-12 px-3 py-2" />
          </tr>
        </thead>
        <tbody>
          {groups.map((group) => {
            const isCollapsed = collapsedGroups.has(group.id);
            const groupSelectedCount = group.samples.filter((s) =>
              selectedIds.has(s.id)
            ).length;

            return (
              <GroupSection
                key={group.id}
                group={group}
                isCollapsed={isCollapsed}
                selectedCount={groupSelectedCount}
                showHeader={hasMultipleGroups}
                selectedIds={selectedIds}
                expandedRowId={expandedRowId}
                onToggle={() => onToggleGroup?.(group.id)}
                onSelectOne={onSelectOne}
                onExpandRow={onExpandRow}
              />
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

/**
 * Group section with optional header and samples
 */
interface GroupSectionProps {
  group: SampleGroup;
  isCollapsed: boolean;
  selectedCount: number;
  showHeader: boolean;
  selectedIds: Set<string>;
  expandedRowId: string | null;
  onToggle: () => void;
  onSelectOne: (id: string, checked: boolean) => void;
  onExpandRow: (id: string | null) => void;
}

function GroupSection({
  group,
  isCollapsed,
  selectedCount,
  showHeader,
  selectedIds,
  expandedRowId,
  onToggle,
  onSelectOne,
  onExpandRow,
}: GroupSectionProps) {
  return (
    <>
      {/* Group header row */}
      {showHeader && (
        <tr
          className="bg-[#212636] border-b border-muted-foreground/30 cursor-pointer hover:bg-muted/30"
          onClick={onToggle}
        >
          <td colSpan={8} className="px-3 py-2">
            <div className="flex items-center gap-2">
              <ChevronDown
                className={`h-4 w-4 text-muted-foreground transition-transform ${
                  isCollapsed ? "-rotate-90" : ""
                }`}
              />
              <span className="text-sm font-semibold text-foreground uppercase tracking-wide">
                {group.label}
              </span>
              <span className="text-xs text-muted-foreground">
                ({group.samples.length})
              </span>
              {selectedCount > 0 && (
                <span className="text-xs text-primary ml-2">
                  {selectedCount} selected
                </span>
              )}
            </div>
          </td>
        </tr>
      )}

      {/* Sample rows */}
      {!isCollapsed &&
        group.samples.map((sample) => (
          <SampleRow
            key={sample.id}
            sample={sample}
            isSelected={selectedIds.has(sample.id)}
            isExpanded={expandedRowId === sample.id}
            onSelect={(checked) => onSelectOne(sample.id, checked)}
            onExpand={() => onExpandRow(sample.id)}
          />
        ))}
    </>
  );
}

/**
 * Custom checkbox component
 */
interface CheckboxProps {
  checked: boolean;
  indeterminate?: boolean;
  onChange: (checked: boolean) => void;
  "aria-label"?: string;
}

function Checkbox({
  checked,
  indeterminate,
  onChange,
  "aria-label": ariaLabel,
}: CheckboxProps) {
  return (
    <button
      role="checkbox"
      aria-checked={indeterminate ? "mixed" : checked}
      aria-label={ariaLabel}
      onClick={() => onChange(!checked)}
      className={`
        w-5 h-5 rounded border-2 flex items-center justify-center transition-colors
        ${
          checked || indeterminate
            ? "bg-primary border-primary"
            : "bg-transparent border-muted-foreground/50 hover:border-muted-foreground"
        }
      `}
    >
      {checked && (
        <svg className="w-3 h-3 text-primary-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
      )}
      {indeterminate && !checked && (
        <div className="w-2.5 h-0.5 bg-primary-foreground rounded-full" />
      )}
    </button>
  );
}


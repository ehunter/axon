/**
 * Sample Table
 *
 * Interactive table with checkboxes, expandable rows, and highlighting.
 */

"use client";

import { RecommendedSample } from "./types";
import { SampleRow } from "./sample-row";

interface SampleTableProps {
  samples: RecommendedSample[];
  selectedIds: Set<string>;
  expandedRowId: string | null;
  onSelectAll: (checked: boolean) => void;
  onSelectOne: (id: string, checked: boolean) => void;
  onExpandRow: (id: string | null) => void;
}

export function SampleTable({
  samples,
  selectedIds,
  expandedRowId,
  onSelectAll,
  onSelectOne,
  onExpandRow,
}: SampleTableProps) {
  const allSelected = samples.length > 0 && selectedIds.size === samples.length;
  const someSelected = selectedIds.size > 0 && selectedIds.size < samples.length;

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="bg-[#212636] text-left">
            {/* Checkbox column */}
            <th className="w-12 px-4 py-3">
              <Checkbox
                checked={allSelected}
                indeterminate={someSelected}
                onChange={(checked) => onSelectAll(checked)}
                aria-label="Select all samples"
              />
            </th>
            <th className="px-4 py-3 text-sm font-semibold text-foreground">
              ID
            </th>
            <th className="px-4 py-3 text-sm font-semibold text-foreground">
              Type
            </th>
            <th className="px-4 py-3 text-sm font-semibold text-foreground">
              RIN
            </th>
            <th className="px-4 py-3 text-sm font-semibold text-foreground">
              Age
            </th>
            <th className="px-4 py-3 text-sm font-semibold text-foreground">
              Price
            </th>
            {/* Expand column */}
            <th className="w-12 px-4 py-3" />
          </tr>
        </thead>
        <tbody>
          {samples.map((sample) => (
            <SampleRow
              key={sample.id}
              sample={sample}
              isSelected={selectedIds.has(sample.id)}
              isExpanded={expandedRowId === sample.id}
              onSelect={(checked) => onSelectOne(sample.id, checked)}
              onExpand={() => onExpandRow(sample.id)}
            />
          ))}
        </tbody>
      </table>
    </div>
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


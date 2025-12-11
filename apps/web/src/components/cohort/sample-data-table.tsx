/**
 * Sample Data Table
 * 
 * Interactive tabular view for exploring recommended cohort samples.
 * Each column has a header with visualization and data rows below.
 * Supports bidirectional hover highlighting between table rows and chart data points.
 */

"use client";

import { useState } from "react";
import { CohortSample, ColumnDefinition } from "@/types/cohort";
import { generateColumns, getFieldValue } from "@/lib/cohort/column-generator";
import { TableHeaderCell } from "./table-header-cell";
import { TextCell, BadgeCell, NumericCell } from "./data-cells";

interface SampleDataTableProps {
  samples: CohortSample[];
  columns?: ColumnDefinition[];
  title?: string;
  onExport?: () => void;
}

// Hover state type for column-specific highlighting
interface HoverState {
  sampleIndex: number;
  columnId: string;
}

export function SampleDataTable({
  samples,
  columns: customColumns,
  title = "Sample Cohort",
  onExport,
}: SampleDataTableProps) {
  // Generate columns from data if not provided
  const columns = customColumns || generateColumns(samples);
  
  // Hover state for bidirectional highlighting (column-specific)
  const [hoverState, setHoverState] = useState<HoverState | null>(null);

  if (samples.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">
        No samples to display
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 w-full">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex flex-col gap-1">
          <span className="text-xs text-muted-foreground uppercase tracking-wide">
            Cohort
          </span>
          <h2 className="text-2xl font-normal text-foreground">{title}</h2>
        </div>
        
        {onExport && (
          <button
            onClick={onExport}
            className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-secondary border border-border text-sm font-medium text-foreground hover:bg-muted transition-colors"
          >
            <DownloadIcon className="h-4 w-4" />
            Export
          </button>
        )}
      </div>

      {/* Table using CSS Grid for proper row alignment */}
      <div className="overflow-x-auto rounded-xl">
        <div 
          className="grid gap-px min-w-max"
          style={{ 
            gridTemplateColumns: columns.map(col => `${col.width || 150}px`).join(' ')
          }}
        >
          {/* Header row */}
          {columns.map((column) => {
            const isHoveredColumn = hoverState?.columnId === column.id;
            const hoveredSampleIndex = isHoveredColumn ? hoverState.sampleIndex : null;
            
            return (
              <TableHeaderCell
                key={`header-${column.id}`}
                column={column}
                samples={samples}
                hoveredSampleIndex={hoveredSampleIndex}
                onHoverSample={(index) =>
                  setHoverState(index !== null ? { sampleIndex: index, columnId: column.id } : null)
                }
              />
            );
          })}
          
          {/* Data rows - render row by row for proper height alignment */}
          {samples.map((sample, rowIndex) =>
            columns.map((column) => {
              const isHoveredColumn = hoverState?.columnId === column.id;
              
              return (
                <DataCell
                  key={`${column.id}-${rowIndex}`}
                  column={column}
                  sample={sample}
                  isHovered={isHoveredColumn && hoverState.sampleIndex === rowIndex}
                  onMouseEnter={() => setHoverState({ sampleIndex: rowIndex, columnId: column.id })}
                  onMouseLeave={() => setHoverState(null)}
                />
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * Renders the appropriate cell type based on column configuration
 */
function DataCell({
  column,
  sample,
  isHovered,
  onMouseEnter,
  onMouseLeave,
}: {
  column: ColumnDefinition;
  sample: CohortSample;
  isHovered: boolean;
  onMouseEnter: () => void;
  onMouseLeave: () => void;
}) {
  const value = getFieldValue(sample, column.field);

  switch (column.cellType) {
    case "badge":
    case "badges":
      return (
        <BadgeCell
          value={value as string | string[] | null}
          width={column.width}
          colorMap={column.colorMap}
          isHovered={isHovered}
          onMouseEnter={onMouseEnter}
          onMouseLeave={onMouseLeave}
        />
      );

    case "numeric":
      return (
        <NumericCell
          value={value as number | string | null}
          width={column.width}
          format={column.format}
          isHovered={isHovered}
          onMouseEnter={onMouseEnter}
          onMouseLeave={onMouseLeave}
        />
      );

    case "text":
    default:
      return (
        <TextCell
          value={value != null ? String(value) : null}
          width={column.width}
          isHovered={isHovered}
          onMouseEnter={onMouseEnter}
          onMouseLeave={onMouseLeave}
        />
      );
  }
}

function DownloadIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" y1="15" x2="12" y2="3" />
    </svg>
  );
}


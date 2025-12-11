/**
 * Card Header
 *
 * Displays the title, count badge, and filter chips.
 */

"use client";

import { Beaker, X } from "lucide-react";
import { ActiveFilter } from "./types";

interface CardHeaderProps {
  title: string;
  count: number;
  filters?: ActiveFilter[];
  onFilterRemove?: (filterId: string) => void;
}

export function CardHeader({
  title,
  count,
  filters = [],
  onFilterRemove,
}: CardHeaderProps) {
  return (
    <div className="flex flex-col gap-3 px-5 py-4 border-b border-border">
      {/* Title row */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Beaker className="h-5 w-5 text-primary" />
          <h3 className="text-lg font-semibold text-foreground">{title}</h3>
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary/20 text-primary border border-primary/30">
            {count} found
          </span>
        </div>
      </div>

      {/* Filter chips */}
      {filters.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {filters.map((filter) => (
            <FilterChip
              key={filter.id}
              filter={filter}
              onRemove={
                filter.removable !== false && onFilterRemove
                  ? () => onFilterRemove(filter.id)
                  : undefined
              }
            />
          ))}
        </div>
      )}
    </div>
  );
}

interface FilterChipProps {
  filter: ActiveFilter;
  onRemove?: () => void;
}

function FilterChip({ filter, onRemove }: FilterChipProps) {
  return (
    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-muted border border-border text-foreground">
      <span className="text-muted-foreground">{filter.label}:</span>
      <span>{filter.value}</span>
      {onRemove && (
        <button
          onClick={onRemove}
          className="ml-0.5 p-0.5 rounded-full hover:bg-muted-foreground/20 transition-colors"
          aria-label={`Remove ${filter.label} filter`}
        >
          <X className="h-3 w-3" />
        </button>
      )}
    </span>
  );
}


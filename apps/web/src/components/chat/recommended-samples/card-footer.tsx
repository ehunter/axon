/**
 * Card Footer
 *
 * Sticky footer showing selection count and action buttons.
 */

"use client";

import { FolderPlus, ShoppingCart } from "lucide-react";

interface CardFooterProps {
  selectedCount: number;
  isConfiguring: boolean;
  onConfigureOrder: () => void;
  onSaveToCohort: () => void;
}

export function CardFooter({
  selectedCount,
  isConfiguring,
  onConfigureOrder,
  onSaveToCohort,
}: CardFooterProps) {
  const hasSelection = selectedCount > 0;

  return (
    <div className="flex items-center justify-between px-5 py-3 border-t border-border bg-surface sticky bottom-0">
      {/* Selection count */}
      <div className="flex items-center gap-2">
        <span
          className={`text-sm font-medium ${
            hasSelection ? "text-foreground" : "text-muted-foreground"
          }`}
        >
          {selectedCount} selected
        </span>
      </div>

      {/* Action buttons */}
      <div className="flex items-center gap-2">
        {/* Save to Cohorts - secondary action */}
        <button
          onClick={onSaveToCohort}
          disabled={!hasSelection}
          className={`
            inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium
            border transition-colors
            ${
              hasSelection
                ? "border-border bg-secondary text-foreground hover:bg-muted"
                : "border-border/50 bg-secondary/50 text-muted-foreground cursor-not-allowed"
            }
          `}
        >
          <FolderPlus className="h-4 w-4" />
          Save to Cohorts
        </button>

        {/* Configure Order - primary action */}
        <button
          onClick={onConfigureOrder}
          disabled={!hasSelection || isConfiguring}
          className={`
            inline-flex items-center gap-2 px-4 py-1.5 rounded-lg text-sm font-medium
            transition-colors
            ${
              hasSelection && !isConfiguring
                ? "bg-primary text-primary-foreground hover:bg-primary/90"
                : "bg-primary/50 text-primary-foreground/50 cursor-not-allowed"
            }
          `}
        >
          <ShoppingCart className="h-4 w-4" />
          {isConfiguring ? "Configuring..." : `Configure Order${hasSelection ? ` (${selectedCount})` : ""}`}
        </button>
      </div>
    </div>
  );
}


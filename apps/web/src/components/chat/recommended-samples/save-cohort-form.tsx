/**
 * Save to Cohort Form
 *
 * Simple inline form to name and save a cohort.
 */

"use client";

import { useState, useRef, useEffect } from "react";
import { FolderPlus, X } from "lucide-react";

interface SaveCohortFormProps {
  selectedCount: number;
  onSave: (name: string, description?: string) => void;
  onCancel: () => void;
}

export function SaveCohortForm({
  selectedCount,
  onSave,
  onCancel,
}: SaveCohortFormProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-focus the input when form appears
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    setIsSubmitting(true);
    try {
      await onSave(name.trim(), description.trim() || undefined);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="border-t border-muted-foreground/30 bg-muted/30 px-5 py-4 animate-in slide-in-from-top-2 duration-300">
      <form onSubmit={handleSubmit}>
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2">
            <FolderPlus className="h-4 w-4 text-muted-foreground" />
            <h4 className="text-sm font-semibold text-foreground">
              Save to Cohorts
            </h4>
            <span className="text-xs text-muted-foreground">
              ({selectedCount} sample{selectedCount !== 1 ? "s" : ""})
            </span>
          </div>
          <button
            type="button"
            onClick={onCancel}
            className="p-1 rounded-md hover:bg-muted transition-colors"
            aria-label="Cancel"
          >
            <X className="h-4 w-4 text-muted-foreground" />
          </button>
        </div>

        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1">
              Cohort Name <span className="text-red-400">*</span>
            </label>
            <input
              ref={inputRef}
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., AD Frontal Cortex - RNA-seq Study"
              className="w-full px-3 py-1.5 rounded-md bg-input border border-border text-foreground text-sm placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-primary/50"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1">
              Description <span className="text-muted-foreground/50">(optional)</span>
            </label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief description of this cohort"
              className="w-full px-3 py-1.5 rounded-md bg-input border border-border text-foreground text-sm placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>
        </div>

        <div className="flex items-center justify-end gap-2 mt-4">
          <button
            type="button"
            onClick={onCancel}
            className="px-3 py-1.5 rounded-md text-sm font-medium border border-border bg-secondary text-foreground hover:bg-muted transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={!name.trim() || isSubmitting}
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium bg-primary text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <FolderPlus className="h-4 w-4" />
            {isSubmitting ? "Saving..." : "Save Cohort"}
          </button>
        </div>
      </form>
    </div>
  );
}


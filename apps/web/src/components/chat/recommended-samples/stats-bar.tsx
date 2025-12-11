/**
 * Stats Bar
 *
 * Dense summary bar showing calculated statistics for the recommended samples.
 */

"use client";

import { BarChart3 } from "lucide-react";
import { SampleStats } from "./types";

interface StatsBarProps {
  stats: SampleStats;
}

/**
 * Format p-value for display
 */
function formatPValue(p: number | null): string {
  if (p == null) return "—";
  if (p < 0.001) return "<0.001";
  if (p < 0.01) return p.toFixed(3);
  return p.toFixed(2);
}

/**
 * Determine if p-value is statistically significant
 */
function isSignificant(p: number | null): boolean {
  return p != null && p < 0.05;
}

export function StatsBar({ stats }: StatsBarProps) {
  const statItems: { label: string; value: string; highlight?: boolean; warning?: boolean }[] = [
    {
      label: "P(Age)",
      value: formatPValue(stats.agePValue),
      highlight: isSignificant(stats.agePValue),
      warning: stats.agePValue != null && stats.agePValue < 0.05, // Significant difference may be concerning
    },
    {
      label: "P(RIN)",
      value: formatPValue(stats.rinPValue),
      highlight: !isSignificant(stats.rinPValue), // Non-significant is good (groups are balanced)
    },
    {
      label: "P(PMI)",
      value: formatPValue(stats.pmiPValue),
    },
  ];

  // Only show Braak if available
  if (stats.medianBraak != null) {
    statItems.push({
      label: "Median Braak",
      value: stats.medianBraak,
    });
  }

  return (
    <div className="flex items-center gap-4 px-5 py-2.5 bg-[#212636] border-b border-muted-foreground/30">
      <BarChart3 className="h-4 w-4 text-muted-foreground flex-shrink-0" />
      <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
        Overview
      </span>
      <div className="h-4 w-px bg-muted-foreground/30" />
      <div className="flex items-center gap-6">
        {statItems.map((item, index) => (
          <div key={index} className="flex items-center gap-1.5">
            <span className="text-sm text-muted-foreground">{item.label}:</span>
            <span
              className={`text-sm font-semibold ${
                item.warning
                  ? "text-amber-400"
                  : item.highlight
                  ? "text-teal-400"
                  : "text-foreground"
              }`}
            >
              {item.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}


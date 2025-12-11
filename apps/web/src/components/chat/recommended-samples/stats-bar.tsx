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

export function StatsBar({ stats }: StatsBarProps) {
  const statItems = [
    {
      label: "Avg RIN",
      value: stats.avgRin != null ? stats.avgRin.toFixed(1) : "—",
      highlight: stats.avgRin != null && stats.avgRin >= 7,
    },
    {
      label: "Mean Age",
      value: stats.meanAge != null ? `${Math.round(stats.meanAge)}y` : "—",
    },
    {
      label: "Avg Price",
      value: stats.avgPrice != null ? `$${Math.round(stats.avgPrice)}` : "—",
    },
  ];

  // Only show Braak if available
  if (stats.medianBraak != null) {
    statItems.splice(2, 0, {
      label: "Median Braak",
      value: stats.medianBraak,
    });
  }

  return (
    <div className="flex items-center gap-4 px-5 py-2.5 bg-muted/50 border-b border-border">
      <BarChart3 className="h-4 w-4 text-muted-foreground flex-shrink-0" />
      <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
        Overview
      </span>
      <div className="h-4 w-px bg-border" />
      <div className="flex items-center gap-6">
        {statItems.map((item, index) => (
          <div key={index} className="flex items-center gap-1.5">
            <span className="text-sm text-muted-foreground">{item.label}:</span>
            <span
              className={`text-sm font-semibold ${
                item.highlight ? "text-teal-400" : "text-foreground"
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


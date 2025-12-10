/**
 * Scale Chart (Strip/Dot Plot)
 *
 * Displays continuous values on a bounded scale.
 * Ideal for metrics like RIN (1-10) where the scale context matters.
 * Shows individual dots for each value with median indicator.
 */

"use client";

import { useState } from "react";
import { ScaleChartData } from "@/types/cohort";

interface ScaleChartProps {
  data: ScaleChartData;
  height?: number;
  accentColor?: string;
}

export function ScaleChart({
  data,
  height = 150,
  accentColor = "hsl(186, 53%, 32%)", // Teal
}: ScaleChartProps) {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const { values, min, max, median } = data;

  if (values.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
        No data
      </div>
    );
  }

  // Calculate position on scale (0-100%)
  const getPosition = (value: number): number => {
    return ((value - min) / (max - min)) * 100;
  };

  // Generate tick marks
  const tickCount = max - min <= 10 ? max - min + 1 : 5;
  const tickStep = (max - min) / (tickCount - 1);
  const ticks = Array.from({ length: tickCount }, (_, i) =>
    min + i * tickStep
  );

  // Group overlapping values for display
  const groupedValues = values.reduce((acc, value, index) => {
    const pos = getPosition(value).toFixed(1);
    if (!acc[pos]) {
      acc[pos] = { value, count: 1, indices: [index] };
    } else {
      acc[pos].count++;
      acc[pos].indices.push(index);
    }
    return acc;
  }, {} as Record<string, { value: number; count: number; indices: number[] }>);

  return (
    <div className="flex flex-col w-full" style={{ height }}>
      {/* Scale labels at top */}
      <div className="flex justify-between text-[10px] text-muted-foreground mb-1 px-1">
        <span>{min}</span>
        <span>{max}</span>
      </div>

      {/* Scale track with dots */}
      <div className="relative flex-1 flex items-center">
        {/* Track background */}
        <div className="absolute inset-x-1 h-1 bg-muted rounded-full" />

        {/* Tick marks */}
        {ticks.map((tick, i) => (
          <div
            key={i}
            className="absolute w-px h-2 bg-muted-foreground/30"
            style={{ left: `calc(${getPosition(tick)}% + 4px - 0.5px)` }}
          />
        ))}

        {/* Value dots */}
        {Object.entries(groupedValues).map(([pos, { value, count, indices }]) => {
          const isHovered = indices.some((i) => i === hoveredIndex);
          return (
            <div
              key={pos}
              className="absolute transform -translate-x-1/2 group"
              style={{ left: `calc(${parseFloat(pos)}% + 4px)` }}
              onMouseEnter={() => setHoveredIndex(indices[0])}
              onMouseLeave={() => setHoveredIndex(null)}
            >
              {/* Dot */}
              <div
                className="w-3 h-3 rounded-full border-2 border-background transition-transform hover:scale-125 cursor-pointer"
                style={{ backgroundColor: accentColor }}
              />

              {/* Tooltip */}
              <div
                className={`absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 rounded bg-popover border border-border shadow-md text-xs whitespace-nowrap z-10 transition-opacity ${
                  isHovered ? "opacity-100" : "opacity-0 pointer-events-none"
                }`}
              >
                <span className="font-medium text-foreground">{value.toFixed(1)}</span>
                {count > 1 && (
                  <span className="text-muted-foreground ml-1">({count} samples)</span>
                )}
              </div>
            </div>
          );
        })}

        {/* Median indicator line */}
        {median != null && (
          <div
            className="absolute w-0.5 h-4 bg-muted-foreground/60"
            style={{ left: `calc(${getPosition(median)}% + 4px - 1px)` }}
          />
        )}
      </div>

      {/* Median indicator */}
      {median != null && (
        <div className="flex flex-col items-center mt-3">
          <div
            className="w-0 h-0 border-l-[5px] border-r-[5px] border-b-[6px] border-transparent"
            style={{ borderBottomColor: "hsl(var(--muted-foreground))" }}
          />
          <div className="flex flex-col items-center px-2 py-0.5">
            <span className="text-xs text-muted-foreground">Median</span>
            <span className="text-sm font-medium text-foreground">
              {median.toFixed(1)}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}


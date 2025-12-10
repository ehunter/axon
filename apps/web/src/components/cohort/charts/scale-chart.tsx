/**
 * Scale Chart (Strip/Dot Plot with Beeswarm stacking)
 *
 * Displays continuous values on a bounded scale.
 * Ideal for metrics like RIN (1-10) where the scale context matters.
 * Shows individual dots for each value with vertical stacking for clusters.
 */

"use client";

import { useState, useMemo } from "react";
import { ScaleChartData } from "@/types/cohort";

interface ScaleChartProps {
  data: ScaleChartData;
  height?: number;
  accentColor?: string;
}

interface StackedDot {
  value: number;
  position: number; // 0-100%
  stackIndex: number; // vertical position in stack (0 = bottom)
  stackSize: number; // total dots in this stack
  originalIndex: number;
}

export function ScaleChart({
  data,
  height = 150,
  accentColor = "hsl(186, 53%, 32%)", // Teal
}: ScaleChartProps) {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const { values, min, max, median } = data;

  // Calculate position on scale (0-100%)
  const getPosition = (value: number): number => {
    return ((value - min) / (max - min)) * 100;
  };

  // Stack dots that are close together (within ~3% of scale)
  const stackedDots = useMemo((): StackedDot[] => {
    if (values.length === 0) return [];

    const threshold = 3; // 3% of scale width
    const dots: StackedDot[] = values.map((value, index) => ({
      value,
      position: getPosition(value),
      stackIndex: 0,
      stackSize: 1,
      originalIndex: index,
    }));

    // Sort by position
    dots.sort((a, b) => a.position - b.position);

    // Group into stacks
    const stacks: StackedDot[][] = [];
    let currentStack: StackedDot[] = [];

    for (const dot of dots) {
      if (currentStack.length === 0) {
        currentStack.push(dot);
      } else {
        const stackCenter =
          currentStack.reduce((sum, d) => sum + d.position, 0) / currentStack.length;
        if (Math.abs(dot.position - stackCenter) <= threshold) {
          currentStack.push(dot);
        } else {
          stacks.push(currentStack);
          currentStack = [dot];
        }
      }
    }
    if (currentStack.length > 0) {
      stacks.push(currentStack);
    }

    // Assign stack indices and calculate average position for each stack
    const result: StackedDot[] = [];
    for (const stack of stacks) {
      const avgPosition =
        stack.reduce((sum, d) => sum + d.position, 0) / stack.length;
      stack.forEach((dot, i) => {
        result.push({
          ...dot,
          position: avgPosition, // Align to stack center
          stackIndex: i,
          stackSize: stack.length,
        });
      });
    }

    return result;
  }, [values, min, max]);

  if (values.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
        No data
      </div>
    );
  }

  // Generate tick marks
  const tickCount = max - min <= 10 ? max - min + 1 : 5;
  const tickStep = (max - min) / (tickCount - 1);
  const ticks = Array.from({ length: tickCount }, (_, i) =>
    min + i * tickStep
  );

  const dotSize = 10;
  const dotSpacing = 2;

  return (
    <div className="flex flex-col w-full" style={{ height }}>
      {/* Scale labels at top */}
      <div className="flex justify-between text-[10px] text-muted-foreground mb-1 px-1">
        <span>{min}</span>
        <span>{max}</span>
      </div>

      {/* Scale track with stacked dots */}
      <div className="relative flex-1 flex items-end pb-6">
        {/* Track background - positioned at bottom */}
        <div className="absolute left-1 right-1 bottom-4 h-1 bg-muted rounded-full" />

        {/* Tick marks */}
        {ticks.map((tick, i) => (
          <div
            key={i}
            className="absolute w-px h-2 bg-muted-foreground/30"
            style={{
              left: `calc(${getPosition(tick)}% * 0.95 + 2.5%)`,
              bottom: 12,
            }}
          />
        ))}

        {/* Stacked value dots */}
        {stackedDots.map((dot) => {
          const isHovered = hoveredIndex === dot.originalIndex;
          const bottomOffset = 16 + dot.stackIndex * (dotSize + dotSpacing);

          return (
            <div
              key={dot.originalIndex}
              className="absolute transform -translate-x-1/2"
              style={{
                left: `calc(${dot.position}% * 0.95 + 2.5%)`,
                bottom: bottomOffset,
              }}
              onMouseEnter={() => setHoveredIndex(dot.originalIndex)}
              onMouseLeave={() => setHoveredIndex(null)}
            >
              {/* Dot */}
              <div
                className="rounded-full border-2 border-background transition-transform hover:scale-125 cursor-pointer"
                style={{
                  width: dotSize,
                  height: dotSize,
                  backgroundColor: accentColor,
                }}
              />

              {/* Tooltip */}
              <div
                className={`absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-2 py-1 rounded bg-popover border border-border shadow-md text-xs whitespace-nowrap z-10 transition-opacity ${
                  isHovered ? "opacity-100" : "opacity-0 pointer-events-none"
                }`}
              >
                <span className="font-medium text-foreground">
                  {dot.value.toFixed(1)}
                </span>
              </div>
            </div>
          );
        })}

        {/* Median indicator line */}
        {median != null && (
          <div
            className="absolute w-0.5 h-3 bg-muted-foreground/60"
            style={{
              left: `calc(${getPosition(median)}% * 0.95 + 2.5% - 1px)`,
              bottom: 12,
            }}
          />
        )}
      </div>

      {/* Median indicator */}
      {median != null && (
        <div className="flex flex-col items-center">
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


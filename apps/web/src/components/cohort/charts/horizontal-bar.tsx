/**
 * Horizontal Bar Chart with Custom Labels
 *
 * Displays categorical distribution as horizontal bars.
 * Layout: [Label] [Bar] [Value] - prevents overlap issues.
 * Used for Sample Types, Clinical Diagnosis, Source columns.
 */

"use client";

import { BarChartData } from "@/types/cohort";

interface HorizontalBarChartProps {
  data: BarChartData[];
  height?: number;
  accentColor?: string;
}

export function HorizontalBarChart({
  data,
  height = 160,
  accentColor = "hsl(186, 53%, 32%)", // Teal
}: HorizontalBarChartProps) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
        No data
      </div>
    );
  }

  // Take top 5 categories
  const chartData = data.slice(0, 5);
  const maxValue = Math.max(...chartData.map((d) => d.value));

  return (
    <div className="flex flex-col justify-center gap-1.5 w-full" style={{ height }}>
      {chartData.map((item, index) => (
        <div key={index} className="flex items-center gap-2 h-7">
          {/* Label - fixed width, truncated */}
          <span
            className="text-[13px] font-medium text-[#e0e6ff] truncate flex-shrink-0"
            style={{ width: 90 }}
            title={item.label}
          >
            {item.label}
          </span>

          {/* Bar - scales proportionally */}
          <div className="flex-1 h-full flex items-center">
            <div
              className="h-5 rounded-r"
              style={{
                width: `${(item.value / maxValue) * 100}%`,
                minWidth: 4,
                backgroundColor: accentColor,
              }}
            />
          </div>

          {/* Value - fixed width, right aligned */}
          <span className="text-[13px] font-semibold text-[#b5bcd3] w-6 text-right flex-shrink-0">
            {item.value}
          </span>
        </div>
      ))}
    </div>
  );
}

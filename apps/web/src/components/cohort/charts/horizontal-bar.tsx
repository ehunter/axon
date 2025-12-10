/**
 * Horizontal Bar Chart
 * 
 * Displays categorical distribution as horizontal bars.
 * Used for Sample Types, Clinical Diagnosis, Source columns.
 */

import { BarChartData } from "@/types/cohort";

interface HorizontalBarChartProps {
  data: BarChartData[];
  maxValue?: number;
  height?: number;
  barHeight?: number;
  showLabels?: boolean;
  showCounts?: boolean;
  accentColor?: string;
}

export function HorizontalBarChart({
  data,
  maxValue,
  height = 160,
  barHeight = 32,
  showLabels = true,
  showCounts = true,
  accentColor = "var(--chart-1)",
}: HorizontalBarChartProps) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
        No data
      </div>
    );
  }

  const max = maxValue || Math.max(...data.map((d) => d.value));
  const gap = 2;

  return (
    <div className="flex flex-col gap-[2px] w-full" style={{ maxHeight: height }}>
      {data.slice(0, 5).map((item, index) => {
        const widthPercent = max > 0 ? (item.value / max) * 100 : 0;
        
        return (
          <div
            key={item.label}
            className="flex items-center justify-between px-2 py-2 relative"
            style={{ height: barHeight }}
          >
            {/* Bar background */}
            <div
              className="absolute left-0 top-1/2 -translate-y-1/2 h-full rounded-sm"
              style={{
                width: `${Math.max(widthPercent, 2)}%`,
                backgroundColor: "hsl(var(--muted))",
              }}
            />
            
            {/* Label */}
            {showLabels && (
              <span className="relative z-10 text-sm font-medium text-foreground truncate">
                {item.label}
              </span>
            )}
            
            {/* Count */}
            {showCounts && (
              <span className="relative z-10 text-sm font-medium text-muted-foreground">
                {item.value}
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}


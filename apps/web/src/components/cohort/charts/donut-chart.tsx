/**
 * Donut Chart
 * 
 * Displays binary categorical distribution as a donut/pie chart.
 * Used for Gender column (Male/Female).
 */

import { DonutChartData } from "@/types/cohort";

interface DonutChartProps {
  data: DonutChartData[];
  size?: number;
  strokeWidth?: number;
  showLegend?: boolean;
}

export function DonutChart({
  data,
  size = 100,
  strokeWidth = 16,
  showLegend = true,
}: DonutChartProps) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
        No data
      </div>
    );
  }

  const total = data.reduce((sum, d) => sum + d.value, 0);
  if (total === 0) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
        No data
      </div>
    );
  }

  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const center = size / 2;

  // Calculate stroke dash for each segment
  let cumulativePercent = 0;
  const segments = data.map((item) => {
    const percent = item.value / total;
    const dashArray = `${percent * circumference} ${circumference}`;
    const rotation = cumulativePercent * 360 - 90; // Start at top (-90deg)
    cumulativePercent += percent;
    
    return {
      ...item,
      percent,
      dashArray,
      rotation,
    };
  });

  return (
    <div className="flex flex-col items-center gap-3">
      {/* SVG Donut */}
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {/* Background circle */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="hsl(var(--muted))"
          strokeWidth={strokeWidth}
        />
        
        {/* Data segments */}
        {segments.map((segment, index) => (
          <circle
            key={segment.label}
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke={segment.color}
            strokeWidth={strokeWidth}
            strokeDasharray={segment.dashArray}
            strokeDashoffset={0}
            transform={`rotate(${segment.rotation} ${center} ${center})`}
            className="transition-all duration-300"
          />
        ))}
      </svg>

      {/* Legend */}
      {showLegend && (
        <div className="flex flex-col gap-1 w-full">
          {data.map((item) => (
            <div 
              key={item.label}
              className="flex items-center justify-between px-2 py-0.5"
            >
              <div className="flex items-center gap-2">
                <div 
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: item.color }}
                />
                <span className="text-sm" style={{ color: item.color }}>
                  {item.label}
                </span>
              </div>
              <span className="text-sm font-medium text-muted-foreground">
                {item.value}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * Default colors for common categories
 */
export const DONUT_COLORS = {
  Male: "hsl(186, 53%, 32%)",      // Teal
  Female: "hsl(350, 15%, 55%)",    // Rose/mauve
  Case: "hsl(186, 53%, 32%)",      // Teal
  Control: "hsl(var(--muted-foreground))", // Neutral
};

/**
 * Helper to create DonutChartData from a distribution
 */
export function createDonutData(
  distribution: Record<string, number>,
  colorMap?: Record<string, string>
): DonutChartData[] {
  return Object.entries(distribution).map(([label, value]) => ({
    label,
    value,
    color: colorMap?.[label] || DONUT_COLORS[label as keyof typeof DONUT_COLORS] || "hsl(var(--muted-foreground))",
  }));
}


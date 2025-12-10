/**
 * Donut Chart
 * 
 * Displays binary categorical distribution as a donut/pie chart using Recharts.
 * Used for Gender column (Male/Female).
 */

"use client";

import { Pie, PieChart, Cell, Label } from "recharts";
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { DonutChartData } from "@/types/cohort";

interface DonutChartProps {
  data: DonutChartData[];
  size?: number;
  showLegend?: boolean;
}

export function DonutChart({
  data,
  size = 100,
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

  // Build chart config from data
  const chartConfig: ChartConfig = data.reduce((acc, item) => {
    acc[item.label] = {
      label: item.label,
      color: item.color,
    };
    return acc;
  }, {} as ChartConfig);

  const chartData = data.map((d) => ({
    name: d.label,
    value: d.value,
    fill: d.color,
  }));

  return (
    <div className="flex flex-col items-center gap-2">
      <ChartContainer config={chartConfig} className="aspect-square" style={{ height: size, width: size }}>
        <PieChart>
          <ChartTooltip
            cursor={false}
            content={<ChartTooltipContent hideLabel />}
          />
          <Pie
            data={chartData}
            dataKey="value"
            nameKey="name"
            innerRadius={size * 0.3}
            outerRadius={size * 0.45}
            strokeWidth={0}
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.fill} />
            ))}
          </Pie>
        </PieChart>
      </ChartContainer>

      {/* Legend */}
      {showLegend && (
        <div className="flex flex-col gap-0.5 w-full">
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
                <span className="text-xs" style={{ color: item.color }}>
                  {item.label}
                </span>
              </div>
              <span className="text-xs font-medium text-muted-foreground">
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

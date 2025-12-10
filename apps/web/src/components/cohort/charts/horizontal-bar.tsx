/**
 * Horizontal Bar Chart
 * 
 * Displays categorical distribution as horizontal bars using Recharts.
 * Used for Sample Types, Clinical Diagnosis, Source columns.
 */

"use client";

import { Bar, BarChart, XAxis, YAxis, Cell } from "recharts";
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { BarChartData } from "@/types/cohort";

interface HorizontalBarChartProps {
  data: BarChartData[];
  height?: number;
  showLabels?: boolean;
  accentColor?: string;
}

export function HorizontalBarChart({
  data,
  height = 160,
  showLabels = true,
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
  const chartData = data.slice(0, 5).map((item) => ({
    name: item.label,
    value: item.value,
  }));

  const chartConfig: ChartConfig = {
    value: {
      label: "Count",
      color: accentColor,
    },
  };

  return (
    <ChartContainer config={chartConfig} className="w-full" style={{ height }}>
      <BarChart
        data={chartData}
        layout="vertical"
        margin={{ left: 0, right: 8, top: 0, bottom: 0 }}
      >
        <YAxis
          dataKey="name"
          type="category"
          tickLine={false}
          axisLine={false}
          width={80}
          tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }}
          tickFormatter={(value) => value.length > 12 ? `${value.slice(0, 12)}…` : value}
        />
        <XAxis type="number" hide />
        <ChartTooltip
          cursor={{ fill: "hsl(var(--muted))", opacity: 0.3 }}
          content={<ChartTooltipContent />}
        />
        <Bar
          dataKey="value"
          radius={[0, 4, 4, 0]}
          fill={accentColor}
          background={{ fill: "hsl(var(--muted))", radius: 4 }}
        />
      </BarChart>
    </ChartContainer>
  );
}

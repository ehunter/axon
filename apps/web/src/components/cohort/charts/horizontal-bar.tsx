/**
 * Horizontal Bar Chart with Custom Labels
 * 
 * Displays categorical distribution as horizontal bars using Recharts.
 * Labels are positioned on the bar, values on the right.
 * Used for Sample Types, Clinical Diagnosis, Source columns.
 */

"use client";

import { Bar, BarChart, XAxis, YAxis, LabelList } from "recharts";
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

  // Calculate max value for proper scaling
  const maxValue = Math.max(...chartData.map((d) => d.value));

  return (
    <ChartContainer config={chartConfig} className="w-full" style={{ height }}>
      <BarChart
        data={chartData}
        layout="vertical"
        margin={{ left: 8, right: 40, top: 4, bottom: 4 }}
      >
        <YAxis
          dataKey="name"
          type="category"
          tickLine={false}
          axisLine={false}
          hide
        />
        <XAxis 
          type="number" 
          hide 
          domain={[0, maxValue * 1.2]} // Add space for labels
        />
        <ChartTooltip
          cursor={{ fill: "hsl(var(--muted))", opacity: 0.3 }}
          content={<ChartTooltipContent />}
        />
        <Bar
          dataKey="value"
          radius={[0, 4, 4, 0]}
          fill={accentColor}
          barSize={28}
        >
          {/* Label on the bar (left side) - light color for dark background */}
          <LabelList
            dataKey="name"
            position="insideLeft"
            offset={8}
            className="fill-[#e0e6ff]"
            fontSize={13}
            fontWeight={500}
            formatter={(value: string) => 
              value.length > 14 ? `${value.slice(0, 14)}…` : value
            }
          />
          {/* Value on the right side */}
          <LabelList
            dataKey="value"
            position="right"
            offset={8}
            className="fill-[#b5bcd3]"
            fontSize={13}
            fontWeight={600}
          />
        </Bar>
      </BarChart>
    </ChartContainer>
  );
}

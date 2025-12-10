/**
 * Horizontal Bar Chart with Custom Labels
 *
 * Displays categorical distribution as horizontal bars using Recharts/shadcn.
 * Labels inside bars, values flush right at fixed position.
 * Uses normalized data to ensure minimum bar width for labels.
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

// Custom label renderer for flush-right values
const FlushRightValueLabel = (props: any) => {
  const { y, height, value, viewBox } = props;
  // Position at the right edge of the viewBox
  const rightEdge = (viewBox?.x || 0) + (viewBox?.width || 200);
  return (
    <text
      x={rightEdge + 8}
      y={y + height / 2}
      dy={5}
      textAnchor="start"
      fill="#b5bcd3"
      fontSize={13}
      fontWeight={600}
    >
      {value}
    </text>
  );
};

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
  const rawData = data.slice(0, 5);
  const maxValue = Math.max(...rawData.map((d) => d.value));

  // Normalize values to ensure minimum bar width (40% minimum)
  // Formula: displayValue = minPercent + (value / maxValue) * (1 - minPercent)
  const minPercent = 0.4;
  const chartData = rawData.map((item) => ({
    name: item.label,
    displayValue: minPercent + (item.value / maxValue) * (1 - minPercent),
    actualValue: item.value, // Keep original for label
  }));

  const chartConfig: ChartConfig = {
    displayValue: {
      label: "Count",
      color: accentColor,
    },
  };

  return (
    <ChartContainer config={chartConfig} className="w-full" style={{ height }}>
      <BarChart
        data={chartData}
        layout="vertical"
        margin={{ left: 0, right: 36, top: 4, bottom: 4 }}
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
          domain={[0, 1]} // Normalized 0-1 scale
        />
        <ChartTooltip
          cursor={{ fill: "hsl(var(--muted))", opacity: 0.3 }}
          content={
            <ChartTooltipContent
              formatter={(value, name, item) => [item.payload.actualValue, "Count"]}
            />
          }
        />
        <Bar
          dataKey="displayValue"
          radius={[0, 4, 4, 0]}
          fill={accentColor}
          barSize={28}
        >
          {/* Label inside the bar (left side) */}
          <LabelList
            dataKey="name"
            position="insideLeft"
            offset={12}
            className="fill-[#e0e6ff]"
            fontSize={13}
            fontWeight={500}
            formatter={(value: string) =>
              value.length > 16 ? `${value.slice(0, 16)}…` : value
            }
          />
          {/* Value flush right at fixed position */}
          <LabelList
            dataKey="actualValue"
            content={<FlushRightValueLabel />}
          />
        </Bar>
      </BarChart>
    </ChartContainer>
  );
}

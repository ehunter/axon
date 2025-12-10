/**
 * Horizontal Bar Chart with Custom Labels
 *
 * Displays categorical distribution as horizontal bars using Recharts/shadcn.
 * Layout: [Chart with labels inside bars] [Values column flush right]
 * Uses flexbox to ensure values align to parent container edge.
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
  const rawData = data.slice(0, 5);
  const maxValue = Math.max(...rawData.map((d) => d.value));

  // Use actual values for bar widths (no normalization)
  const chartData = rawData.map((item) => ({
    name: item.label,
    value: item.value,
  }));

  const chartConfig: ChartConfig = {
    value: {
      label: "Count",
      color: accentColor,
    },
  };

  // Calculate row height for value alignment
  const rowCount = chartData.length;
  const chartHeight = height - 8; // Account for top/bottom margin
  const rowHeight = chartHeight / rowCount;

  return (
    <div className="flex w-full gap-2" style={{ height }}>
      {/* Chart area - bars with labels inside */}
      <div className="flex-1 min-w-0">
        <ChartContainer config={chartConfig} className="w-full h-full">
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ left: 0, right: 0, top: 4, bottom: 4 }}
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
              domain={[0, maxValue]}
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
              {/* Label inside the bar (left side) */}
              <LabelList
                dataKey="name"
                position="insideLeft"
                offset={12}
                className="fill-[#e0e6ff]"
                fontSize={13}
                fontWeight={500}
              />
            </Bar>
          </BarChart>
        </ChartContainer>
      </div>

      {/* Values column - flush right */}
      <div
        className="flex flex-col justify-around shrink-0 py-1"
        style={{ width: 32 }}
      >
        {chartData.map((item, index) => (
          <span
            key={index}
            className="text-[13px] font-semibold text-[#b5bcd3] text-right"
            style={{ height: rowHeight, lineHeight: `${rowHeight}px` }}
          >
            {item.value}
          </span>
        ))}
      </div>
    </div>
  );
}

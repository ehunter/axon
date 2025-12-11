/**
 * Horizontal Bar Chart with Custom Labels
 *
 * Displays categorical distribution as horizontal bars using Recharts/shadcn.
 * Layout: [Chart with labels inside bars] [Values column flush right]
 * Uses flexbox to ensure values align to parent container edge.
 */

"use client";

import { Bar, BarChart, XAxis, YAxis, LabelList, Cell } from "recharts";
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
  highlightedCategory?: string | null;
}

const HIGHLIGHT_COLOR = "#5BA8BC"; // Brighter teal for highlight
const DIM_OPACITY = 0.4;
const MAX_LABEL_LENGTH = 36; // Maximum characters before truncation

/**
 * Truncate label with ellipsis if too long
 */
function truncateLabel(label: string, maxLength: number = MAX_LABEL_LENGTH): string {
  if (label.length <= maxLength) return label;
  return label.slice(0, maxLength - 1).trim() + "…";
}

export function HorizontalBarChart({
  data,
  height = 160,
  accentColor = "#408AA0",
  highlightedCategory,
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
  // Keep original name for tooltip, use truncated for display
  const chartData = rawData.map((item) => ({
    name: item.label,
    displayName: truncateLabel(item.label),
    value: item.value,
  }));

  const chartConfig: ChartConfig = {
    value: {
      label: "Count",
      color: accentColor,
    },
  };

  // Fixed row height and gap for consistent spacing
  const rowHeight = 28;
  const rowGap = 6;
  const calculatedHeight = chartData.length * rowHeight + (chartData.length - 1) * rowGap;

  return (
    <div className="flex w-full gap-2" style={{ height }}>
      {/* Chart area - bars with labels inside */}
      <div className="flex-1 min-w-0">
        <ChartContainer config={chartConfig} className="w-full" style={{ height: calculatedHeight }}>
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ left: 0, right: 0, top: 0, bottom: 0 }}
            barCategoryGap={rowGap}
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
              barSize={rowHeight}
              isAnimationActive={false}
            >
              {/* Individual bar colors for highlighting */}
              {chartData.map((entry, index) => {
                const isHighlighted = highlightedCategory === entry.name;
                const isDimmed = highlightedCategory != null && !isHighlighted;
                return (
                  <Cell
                    key={`cell-${index}`}
                    fill={isHighlighted ? HIGHLIGHT_COLOR : accentColor}
                    opacity={isDimmed ? DIM_OPACITY : 1}
                  />
                );
              })}
              {/* Label starting at bar left edge, can extend beyond bar */}
              <LabelList
                dataKey="displayName"
                content={({ x, y, height, value }) => (
                  <text
                    x={(x as number) + 12}
                    y={(y as number) + (height as number) / 2}
                    fill="#e0e6ff"
                    fontSize={13}
                    fontWeight={500}
                    dominantBaseline="middle"
                    style={{ overflow: "visible" }}
                  >
                    {value}
                  </text>
                )}
              />
            </Bar>
          </BarChart>
        </ChartContainer>
      </div>

      {/* Values column - flush right, aligned to top */}
      <div
        className="flex flex-col shrink-0"
        style={{ width: 32, gap: rowGap }}
      >
        {chartData.map((item, index) => {
          const isHighlighted = highlightedCategory === item.name;
          const isDimmed = highlightedCategory != null && !isHighlighted;
          return (
            <span
              key={index}
              className={`text-[13px] font-semibold text-right transition-opacity ${
                isHighlighted ? "text-foreground" : "text-[#b5bcd3]"
              }`}
              style={{
                height: rowHeight,
                lineHeight: `${rowHeight}px`,
                opacity: isDimmed ? DIM_OPACITY : 1,
              }}
            >
              {item.value}
            </span>
          );
        })}
      </div>
    </div>
  );
}

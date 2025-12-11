/**
 * Horizontal Bar Chart with Custom Labels
 *
 * Displays categorical distribution as horizontal bars.
 * Layout: [Labels column] [Bars] [Values column]
 * Labels are independent of bar width and can extend on one line.
 */

"use client";

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

  // Fixed row height and gap for consistent spacing
  const rowHeight = 24;
  const rowGap = 6;

  return (
    <div className="flex flex-col w-full" style={{ height, gap: rowGap }}>
      {rawData.map((item, index) => {
        const isHighlighted = highlightedCategory === item.label;
        const isDimmed = highlightedCategory != null && !isHighlighted;
        const barWidth = maxValue > 0 ? (item.value / maxValue) * 100 : 0;

        return (
          <div
            key={index}
            className="flex items-center gap-2 transition-opacity"
            style={{
              height: rowHeight,
              opacity: isDimmed ? DIM_OPACITY : 1,
            }}
            title={item.label} // Full label on hover
          >
            {/* Label - independent width, truncated with ellipsis */}
            <span
              className={`text-[13px] font-medium shrink-0 truncate transition-colors ${
                isHighlighted ? "text-foreground" : "text-[#e0e6ff]"
              }`}
              style={{ maxWidth: "50%" }}
            >
              {truncateLabel(item.label)}
            </span>

            {/* Bar - flexible width */}
            <div className="flex-1 h-full flex items-center min-w-0">
              <div
                className="h-full rounded-r transition-all"
                style={{
                  width: `${Math.max(barWidth, 4)}%`, // Minimum 4% width for visibility
                  backgroundColor: isHighlighted ? HIGHLIGHT_COLOR : accentColor,
                }}
              />
            </div>

            {/* Value - fixed width, right aligned */}
            <span
              className={`text-[13px] font-semibold text-right shrink-0 transition-colors ${
                isHighlighted ? "text-foreground" : "text-[#b5bcd3]"
              }`}
              style={{ width: 28 }}
            >
              {item.value}
            </span>
          </div>
        );
      })}
    </div>
  );
}

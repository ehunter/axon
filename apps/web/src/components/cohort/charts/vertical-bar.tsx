/**
 * Vertical Bar Chart / Histogram
 * 
 * Displays numeric distribution as vertical bars.
 * Used for Braak Score, PMI, RIN, Age columns.
 * Includes median indicator.
 */

import { HistogramData, BarChartData } from "@/types/cohort";

interface VerticalBarChartProps {
  data: HistogramData | BarChartData[];
  height?: number;
  showMedian?: boolean;
  medianLabel?: string;
  accentColor?: string;
}

export function VerticalBarChart({
  data,
  height = 150,
  showMedian = true,
  medianLabel = "Median",
  accentColor = "hsl(var(--chart-1))",
}: VerticalBarChartProps) {
  // Normalize data to array of values
  const isHistogram = "bins" in data;
  const values = isHistogram ? data.counts : data.map((d) => d.value);
  const labels = isHistogram 
    ? data.bins.slice(0, -1).map((b, i) => `${b.toFixed(0)}-${data.bins[i + 1].toFixed(0)}`)
    : data.map((d) => d.label);
  const median = isHistogram ? data.median : undefined;

  if (values.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
        No data
      </div>
    );
  }

  const maxValue = Math.max(...values);
  const barWidth = Math.max(8, Math.floor(100 / values.length) - 2);
  const chartHeight = height - 50; // Leave room for median indicator

  return (
    <div className="flex flex-col items-center w-full">
      {/* Chart area */}
      <div 
        className="flex items-end justify-center gap-[4px] w-full"
        style={{ height: chartHeight }}
      >
        {values.map((value, index) => {
          const heightPercent = maxValue > 0 ? (value / maxValue) * 100 : 0;
          
          return (
            <div
              key={index}
              className="rounded-t-sm transition-all duration-200 hover:opacity-80"
              style={{
                width: barWidth,
                height: `${Math.max(heightPercent, 2)}%`,
                backgroundColor: accentColor,
                minHeight: 4,
              }}
              title={`${labels[index]}: ${value}`}
            />
          );
        })}
      </div>

      {/* Median indicator */}
      {showMedian && median != null && (
        <div className="flex flex-col items-center mt-2">
          {/* Triangle pointer */}
          <div 
            className="w-0 h-0 border-l-[5px] border-r-[5px] border-b-[6px] border-transparent"
            style={{ borderBottomColor: "hsl(var(--muted-foreground))" }}
          />
          {/* Label and value */}
          <div className="flex flex-col items-center px-2 py-1">
            <span className="text-sm text-muted-foreground">{medianLabel}</span>
            <span className="text-base font-medium text-foreground">
              {typeof median === "number" ? median.toFixed(1) : median}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Ordinal Bar Chart variant
 * For categorical data with a known order (e.g., Braak stages)
 */
interface OrdinalBarChartProps {
  data: BarChartData[];
  height?: number;
  medianValue?: string;
  accentColor?: string;
}

export function OrdinalBarChart({
  data,
  height = 150,
  medianValue,
  accentColor = "hsl(var(--chart-1))",
}: OrdinalBarChartProps) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
        No data
      </div>
    );
  }

  const maxValue = Math.max(...data.map((d) => d.value));
  const chartHeight = height - 50;

  return (
    <div className="flex flex-col items-center w-full">
      {/* Chart area */}
      <div 
        className="flex items-end justify-center gap-[4px] w-full"
        style={{ height: chartHeight }}
      >
        {data.map((item) => {
          const heightPercent = maxValue > 0 ? (item.value / maxValue) * 100 : 0;
          
          return (
            <div
              key={item.label}
              className="rounded-t-sm transition-all duration-200 hover:opacity-80"
              style={{
                width: 12,
                height: `${Math.max(heightPercent, 2)}%`,
                backgroundColor: accentColor,
                minHeight: item.value > 0 ? 4 : 0,
              }}
              title={`${item.label}: ${item.value}`}
            />
          );
        })}
      </div>

      {/* Median indicator */}
      {medianValue && (
        <div className="flex flex-col items-center mt-2">
          <div 
            className="w-0 h-0 border-l-[5px] border-r-[5px] border-b-[6px] border-transparent"
            style={{ borderBottomColor: "hsl(var(--muted-foreground))" }}
          />
          <div className="flex flex-col items-center px-2 py-1">
            <span className="text-sm text-muted-foreground">Median</span>
            <span className="text-base font-medium text-foreground">{medianValue}</span>
          </div>
        </div>
      )}
    </div>
  );
}


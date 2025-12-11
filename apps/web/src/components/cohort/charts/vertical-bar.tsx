/**
 * Vertical Bar Chart / Histogram
 * 
 * Displays numeric distribution as vertical bars using Recharts.
 * Used for Braak Score, PMI, RIN, Age columns.
 * Includes median indicator.
 */

"use client";

import { Bar, BarChart, XAxis, YAxis, ReferenceLine, Cell } from "recharts";
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { HistogramData, BarChartData } from "@/types/cohort";

const HIGHLIGHT_COLOR = "#5BA8BC"; // Brighter version of #408AA0 for highlight
const DIM_OPACITY = 0.4;

interface VerticalBarChartProps {
  data: HistogramData | BarChartData[];
  height?: number;
  showMedian?: boolean;
  medianLabel?: string;
  accentColor?: string;
  highlightedValue?: number | null; // For numeric histograms
}

export function VerticalBarChart({
  data,
  height = 150,
  showMedian = true,
  medianLabel = "Median",
  accentColor = "#408AA0",
  highlightedValue,
}: VerticalBarChartProps) {
  // Normalize data to array format
  const isHistogram = "bins" in data;
  
  // Determine decimal precision based on data
  const getPrecision = (values: number[]): number => {
    // Check if any value has decimals
    const hasDecimals = values.some((v) => v % 1 !== 0);
    if (!hasDecimals) return 0;
    
    // Find max decimal places needed (up to 1)
    return 1;
  };
  
  const precision = isHistogram ? getPrecision(data.bins) : 0;
  
  const chartData = isHistogram
    ? data.counts.map((count, i) => ({
        name: data.bins[i].toFixed(precision),
        value: count,
        binValue: data.bins[i],
      }))
    : data.map((d) => ({
        name: d.label,
        value: d.value,
        binValue: null,
      }));

  const median = isHistogram ? data.median : undefined;

  // Find which bin the highlighted value belongs to
  const getHighlightedBinIndex = (): number | null => {
    if (highlightedValue == null || !isHistogram) return null;
    const bins = data.bins;
    for (let i = 0; i < bins.length; i++) {
      const nextBin = bins[i + 1];
      if (nextBin == null) {
        // Last bin - check if value matches
        if (Math.abs(highlightedValue - bins[i]) < 0.01) return i;
      } else if (highlightedValue >= bins[i] && highlightedValue < nextBin) {
        return i;
      } else if (Math.abs(highlightedValue - bins[i]) < 0.01) {
        return i;
      }
    }
    return null;
  };
  const highlightedBinIndex = getHighlightedBinIndex();

  if (chartData.length === 0 || chartData.every((d) => d.value === 0)) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
        No data
      </div>
    );
  }

  const chartConfig: ChartConfig = {
    value: {
      label: "Count",
      color: accentColor,
    },
  };

  return (
    <div className="flex flex-col items-center w-full">
      <ChartContainer config={chartConfig} className="w-full" style={{ height: height - 40 }}>
        <BarChart
          data={chartData}
          margin={{ left: 0, right: 0, top: 8, bottom: 0 }}
        >
          <XAxis 
            dataKey="name" 
            tickLine={false}
            axisLine={false}
            tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
          />
          <YAxis hide />
          <ChartTooltip
            cursor={{ fill: "hsl(var(--muted))", opacity: 0.3 }}
            content={<ChartTooltipContent />}
          />
          <Bar
            dataKey="value"
            radius={[4, 4, 0, 0]}
            fill={accentColor}
            isAnimationActive={false}
          >
            {chartData.map((entry, index) => {
              const isHighlighted = highlightedBinIndex === index;
              const isDimmed = highlightedBinIndex != null && !isHighlighted;
              return (
                <Cell
                  key={`cell-${index}`}
                  fill={isHighlighted ? HIGHLIGHT_COLOR : accentColor}
                  opacity={isDimmed ? DIM_OPACITY : 1}
                />
              );
            })}
          </Bar>
        </BarChart>
      </ChartContainer>

      {/* Median indicator */}
      {showMedian && median != null && (
        <div className="flex flex-col items-center">
          <div 
            className="w-0 h-0 border-l-[5px] border-r-[5px] border-b-[6px] border-transparent"
            style={{ borderBottomColor: "hsl(var(--muted-foreground))" }}
          />
          <div className="flex flex-col items-center px-2 py-0.5">
            <span className="text-xs text-muted-foreground">{medianLabel}</span>
            <span className="text-sm font-medium text-foreground">
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
  highlightedCategory?: string | null;
}

export function OrdinalBarChart({
  data,
  height = 150,
  medianValue,
  accentColor = "#408AA0",
  highlightedCategory,
}: OrdinalBarChartProps) {
  if (data.length === 0 || data.every((d) => d.value === 0)) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
        No data
      </div>
    );
  }

  const chartData = data.map((d) => ({
    name: d.label,
    value: d.value,
  }));

  const chartConfig: ChartConfig = {
    value: {
      label: "Count",
      color: accentColor,
    },
  };

  return (
    <div className="flex flex-col items-center w-full">
      <ChartContainer config={chartConfig} className="w-full" style={{ height: height - 40 }}>
        <BarChart
          data={chartData}
          margin={{ left: 0, right: 0, top: 8, bottom: 0 }}
        >
          <XAxis 
            dataKey="name" 
            tickLine={false}
            axisLine={false}
            tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
          />
          <YAxis hide />
          <ChartTooltip
            cursor={{ fill: "hsl(var(--muted))", opacity: 0.3 }}
            content={<ChartTooltipContent />}
          />
          <Bar
            dataKey="value"
            radius={[4, 4, 0, 0]}
            fill={accentColor}
            isAnimationActive={false}
          >
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
          </Bar>
        </BarChart>
      </ChartContainer>

      {/* Median indicator */}
      {medianValue && (
        <div className="flex flex-col items-center">
          <div 
            className="w-0 h-0 border-l-[5px] border-r-[5px] border-b-[6px] border-transparent"
            style={{ borderBottomColor: "hsl(var(--muted-foreground))" }}
          />
          <div className="flex flex-col items-center px-2 py-0.5">
            <span className="text-xs text-muted-foreground">Median</span>
            <span className="text-sm font-medium text-foreground">{medianValue}</span>
          </div>
        </div>
      )}
    </div>
  );
}

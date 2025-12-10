/**
 * Table Header Cell
 * 
 * A tall header cell containing:
 * - Column title
 * - Interactive visualization (chart)
 * - Summary statistics
 */

import { ColumnDefinition, CohortSample } from "@/types/cohort";
import {
  calculateCategoryDistribution,
  prepareBarChartData,
  prepareHistogramData,
  prepareOrdinalBarData,
  prepareScaleChartData,
  calculateNumericStats,
  getFieldValue,
} from "@/lib/cohort/column-generator";
import {
  HorizontalBarChart,
  VerticalBarChart,
  OrdinalBarChart,
  DonutChart,
  ScaleChart,
  createDonutData,
} from "./charts";

interface TableHeaderCellProps {
  column: ColumnDefinition;
  samples: CohortSample[];
  height?: number;
  hoveredSampleIndex?: number | null;
  onHoverSample?: (index: number | null) => void;
}

export function TableHeaderCell({
  column,
  samples,
  height = 284,
  hoveredSampleIndex,
  onHoverSample,
}: TableHeaderCellProps) {
  const width = column.width ?? 150;
  
  return (
    <div
      className="flex flex-col gap-4 px-4 py-6"
      style={{ width, height, minWidth: width, backgroundColor: "#212636" }}
    >
      {/* Column title */}
      <h3 className="text-xl font-normal text-foreground">
        {column.label}
      </h3>

      {/* Visualization */}
      <div className="flex-1 min-h-0">
        <VisualizationContent
          column={column}
          samples={samples}
          hoveredSampleIndex={hoveredSampleIndex}
          onHoverSample={onHoverSample}
        />
      </div>
    </div>
  );
}

/**
 * Renders the appropriate visualization based on column type
 */
function VisualizationContent({
  column,
  samples,
  hoveredSampleIndex,
  onHoverSample,
}: {
  column: ColumnDefinition;
  samples: CohortSample[];
  hoveredSampleIndex?: number | null;
  onHoverSample?: (index: number | null) => void;
}) {
  const { visualization, field, dataType, categories, colorMap, scaleMin, scaleMax } = column;

  switch (visualization) {
    case "horizontal-bar": {
      const distribution = calculateCategoryDistribution(samples, field);
      const chartData = prepareBarChartData(distribution, colorMap);
      return <HorizontalBarChart data={chartData} />;
    }

    case "vertical-bar": {
      if (dataType === "ordinal" && categories) {
        // Ordinal data (e.g., Braak stages)
        const distribution = calculateCategoryDistribution(samples, field);
        const chartData = prepareOrdinalBarData(distribution, categories);
        
        // Calculate median for ordinal
        const values = samples
          .map((s) => getFieldValue(s, field))
          .filter((v): v is string => v != null && v !== "");
        const medianValue = values.length > 0 ? calculateOrdinalMedian(values, categories) : undefined;
        
        return <OrdinalBarChart data={chartData} medianValue={medianValue} />;
      } else {
        // Numeric data (histogram)
        const histogramData = prepareHistogramData(samples, field);
        if (!histogramData) {
          return <EmptyState />;
        }
        return <VerticalBarChart data={histogramData} />;
      }
    }

    case "scale": {
      // Bounded continuous data (e.g., RIN 1-10)
      const scaleData = prepareScaleChartData(
        samples,
        field,
        scaleMin ?? 1,
        scaleMax ?? 10
      );
      if (!scaleData) {
        return <EmptyState />;
      }
      return (
        <ScaleChart
          data={scaleData}
          hoveredSampleIndex={hoveredSampleIndex}
          onHoverSample={onHoverSample}
        />
      );
    }

    case "donut": {
      const distribution = calculateCategoryDistribution(samples, field);
      const chartData = createDonutData(distribution, colorMap);
      return <DonutChart data={chartData} size={100} />;
    }

    case "none":
    default: {
      // Text preview for ID columns
      if (dataType === "text") {
        const values = samples
          .map((s) => getFieldValue(s, field))
          .filter((v): v is string => v != null && v !== "");
        
        return (
          <div className="text-sm text-muted-foreground leading-relaxed line-clamp-6">
            {values.join(", ")}
          </div>
        );
      }
      return <EmptyState />;
    }
  }
}

/**
 * Calculate median for ordinal values
 */
function calculateOrdinalMedian(values: string[], orderedCategories: string[]): string | undefined {
  if (values.length === 0) return undefined;
  
  // Convert to numeric indices
  const indices = values
    .map((v) => orderedCategories.indexOf(v))
    .filter((i) => i >= 0)
    .sort((a, b) => a - b);
  
  if (indices.length === 0) return undefined;
  
  const medianIndex =
    indices.length % 2 === 0
      ? Math.round((indices[indices.length / 2 - 1] + indices[indices.length / 2]) / 2)
      : indices[Math.floor(indices.length / 2)];
  
  return orderedCategories[medianIndex];
}

function EmptyState() {
  return (
    <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
      No data
    </div>
  );
}


/**
 * Numeric Cell
 * 
 * Displays numeric values with optional formatting.
 */

interface NumericCellProps {
  value: number | string | null | undefined;
  width: number;
  format?: (value: unknown) => string;
  suffix?: string;
}

export function NumericCell({ value, width, format, suffix }: NumericCellProps) {
  let displayValue = "—";

  if (value != null && value !== "") {
    if (format) {
      displayValue = format(value);
    } else if (typeof value === "number") {
      displayValue = value.toFixed(1);
    } else {
      displayValue = String(value);
    }
    
    if (suffix && displayValue !== "—") {
      displayValue += suffix;
    }
  }

  return (
    <div
      className="flex items-center h-10 px-3 bg-secondary"
      style={{ width, minWidth: width }}
    >
      <span className="text-base text-foreground">
        {displayValue}
      </span>
    </div>
  );
}


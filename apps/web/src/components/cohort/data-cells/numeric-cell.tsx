/**
 * Numeric Cell
 * 
 * Displays numeric values with optional formatting.
 */

interface NumericCellProps {
  value: number | string | null | undefined;
  width?: number;
  format?: (value: unknown) => string;
  suffix?: string;
  isHovered?: boolean;
  onMouseEnter?: () => void;
  onMouseLeave?: () => void;
}

export function NumericCell({
  value,
  width = 150,
  format,
  suffix,
  isHovered = false,
  onMouseEnter,
  onMouseLeave,
}: NumericCellProps) {
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
      className={`flex items-center min-h-10 h-full px-3 py-2 transition-colors cursor-default ${
        isHovered
          ? "bg-muted hover:bg-muted-foreground/20"
          : "bg-secondary hover:bg-muted/70"
      }`}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      <span className="text-base text-foreground">
        {displayValue}
      </span>
    </div>
  );
}


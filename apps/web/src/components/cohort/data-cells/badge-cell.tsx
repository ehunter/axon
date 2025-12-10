/**
 * Badge Cell
 * 
 * Displays values as badges/pills.
 * Supports single and multiple values.
 */

import { cn } from "@/lib/utils";

interface BadgeCellProps {
  value: string | string[] | null | undefined;
  width?: number;
  colorMap?: Record<string, string>;
  isHovered?: boolean;
  onMouseEnter?: () => void;
  onMouseLeave?: () => void;
}

/**
 * Color variants for badges
 */
const BADGE_VARIANTS: Record<string, string> = {
  // Sample types
  case: "bg-teal-900/50 border-teal-700/50 text-teal-100",
  control: "bg-muted border-border text-muted-foreground",
  
  // Default
  default: "bg-muted border-border text-foreground",
};

function getBadgeVariant(value: string): string {
  const lowerValue = value.toLowerCase();
  return BADGE_VARIANTS[lowerValue] || BADGE_VARIANTS.default;
}

export function BadgeCell({
  value,
  width = 150,
  colorMap,
  isHovered = false,
  onMouseEnter,
  onMouseLeave,
}: BadgeCellProps) {
  if (value == null || (Array.isArray(value) && value.length === 0)) {
    return (
      <div
        className={`flex items-center h-10 px-3 transition-colors ${
          isHovered ? "bg-muted" : "bg-secondary"
        }`}
        style={{ width, minWidth: width }}
        onMouseEnter={onMouseEnter}
        onMouseLeave={onMouseLeave}
      >
        <span className="text-muted-foreground">—</span>
      </div>
    );
  }

  const values = Array.isArray(value) ? value : [value];

  return (
    <div
      className={`flex items-center gap-2 h-10 px-3 overflow-hidden transition-colors ${
        isHovered ? "bg-muted" : "bg-secondary"
      }`}
      style={{ width, minWidth: width }}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      {values.slice(0, 3).map((v, i) => (
        <Badge key={i} value={v} />
      ))}
      {values.length > 3 && (
        <span className="text-xs text-muted-foreground">
          +{values.length - 3}
        </span>
      )}
    </div>
  );
}

function Badge({ value }: { value: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border",
        getBadgeVariant(value)
      )}
    >
      {value}
    </span>
  );
}


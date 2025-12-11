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
  control: "bg-muted-foreground/20 border-muted-foreground/30 text-muted-foreground/90",
  
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
        className={`flex items-center min-h-10 h-full py-2 px-3 transition-colors cursor-default ${
          isHovered
            ? "bg-muted hover:bg-muted-foreground/20"
            : "bg-secondary hover:bg-muted/70"
        }`}
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
      className={`flex flex-wrap items-start gap-1.5 min-h-10 h-full py-2 px-3 transition-colors cursor-default ${
        isHovered
          ? "bg-muted hover:bg-muted-foreground/20"
          : "bg-secondary hover:bg-muted/70"
      }`}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      {values.map((v, i) => (
        <Badge key={i} value={v} />
      ))}
    </div>
  );
}

function Badge({ value }: { value: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-1 rounded-md text-xs font-medium border leading-tight",
        getBadgeVariant(value)
      )}
    >
      {value}
    </span>
  );
}


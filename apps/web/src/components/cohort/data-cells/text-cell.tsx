/**
 * Text Cell
 * 
 * Simple text display for Subject ID and similar fields.
 */

interface TextCellProps {
  value: string | null | undefined;
  width?: number;
  isHovered?: boolean;
  onMouseEnter?: () => void;
  onMouseLeave?: () => void;
}

export function TextCell({
  value,
  width = 150,
  isHovered = false,
  onMouseEnter,
  onMouseLeave,
}: TextCellProps) {
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
      <span className="text-base text-foreground truncate">
        {value || "—"}
      </span>
    </div>
  );
}


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
      className={`flex items-center h-10 px-3 transition-colors ${
        isHovered ? "bg-muted" : "bg-secondary"
      }`}
      style={{ width, minWidth: width }}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      <span className="text-base text-foreground truncate">
        {value || "—"}
      </span>
    </div>
  );
}


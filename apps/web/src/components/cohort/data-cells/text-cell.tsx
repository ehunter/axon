/**
 * Text Cell
 * 
 * Simple text display for Subject ID and similar fields.
 */

interface TextCellProps {
  value: string | null | undefined;
  width: number;
}

export function TextCell({ value, width }: TextCellProps) {
  return (
    <div
      className="flex items-center h-10 px-3 bg-secondary"
      style={{ width, minWidth: width }}
    >
      <span className="text-base text-foreground truncate">
        {value || "—"}
      </span>
    </div>
  );
}


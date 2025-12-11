"use client";

import { ChevronDown } from "lucide-react";

interface ChatHeaderProps {
  title: string;
  onDropdownClick?: () => void;
}

export function ChatHeader({ title, onDropdownClick }: ChatHeaderProps) {
  return (
    <div className="w-full flex items-center justify-between px-6 py-4 bg-muted/30 border-b border-muted-foreground/20">
      <button
        type="button"
        onClick={onDropdownClick}
        className="flex items-center gap-2 px-3 py-2 hover:bg-secondary/50 transition-colors"
      >
        <span className="text-base text-foreground">{title}</span>
        <ChevronDown className="h-4 w-4 text-foreground" />
      </button>
      <div>{/* Placeholder for future actions */}</div>
    </div>
  );
}


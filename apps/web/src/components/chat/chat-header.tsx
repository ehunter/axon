"use client";

import { ChevronDown } from "lucide-react";

interface ChatHeaderProps {
  title: string;
  onDropdownClick?: () => void;
}

export function ChatHeader({ title, onDropdownClick }: ChatHeaderProps) {
  return (
    <div className="flex items-center justify-between px-6 py-4 border-b border-border">
      <button
        type="button"
        onClick={onDropdownClick}
        className="flex items-center gap-2 border border-border rounded-lg px-3 py-2 bg-card hover:bg-secondary transition-colors"
      >
        <span className="text-base text-foreground">{title}</span>
        <ChevronDown className="h-4 w-4 text-foreground" />
      </button>
      <div>{/* Placeholder for future actions */}</div>
    </div>
  );
}


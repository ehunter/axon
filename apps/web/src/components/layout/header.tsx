"use client";

import { Menu, Bell, User } from "lucide-react";

export function Header() {
  return (
    <header className="flex h-16 items-center justify-between border-b border-border bg-card px-6">
      {/* Mobile menu button */}
      <button className="lg:hidden p-2 rounded-lg hover:bg-secondary">
        <Menu className="h-5 w-5" />
      </button>

      {/* Search or title area */}
      <div className="flex-1 lg:pl-0">
        {/* Can add search bar here if needed */}
      </div>

      {/* Right side actions */}
      <div className="flex items-center gap-2">
        {/* Notifications */}
        <button className="p-2 rounded-lg text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors">
          <Bell className="h-5 w-5" />
        </button>

        {/* User menu */}
        <button className="flex items-center gap-2 p-2 rounded-lg hover:bg-secondary transition-colors">
          <div className="h-8 w-8 rounded-full bg-brand-500/10 flex items-center justify-center">
            <User className="h-4 w-4 text-brand-500" />
          </div>
        </button>
      </div>
    </header>
  );
}


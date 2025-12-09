"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Brain,
  MessageCircle,
  BookOpen,
  TableCellsSplit,
  Folder,
  MoreHorizontal,
  Settings,
  HelpCircle,
  ChevronsUpDown,
  PanelLeft,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/use-auth";
import { useState } from "react";

// Main navigation items
const mainNavigation = [
  { name: "New Chat", href: "/chat", icon: MessageCircle },
  { name: "Requests", href: "/history", icon: BookOpen },
  { name: "Explore", href: "/samples", icon: TableCellsSplit },
];

// Bottom navigation items
const bottomNavigation = [
  { name: "Settings", href: "/settings", icon: Settings },
  { name: "About", href: "/about", icon: HelpCircle },
];

// Mock cohorts data - will be replaced with API call later
const cohorts = [
  { id: "1", name: "RNA Seq - March 2025" },
  { id: "2", name: "RNA-seq - March 2024" },
  { id: "3", name: "RNA Seq" },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, signOut } = useAuth();
  const [isCollapsed, setIsCollapsed] = useState(false);

  // Determine active route
  const isActive = (href: string) => {
    if (href === "/chat") {
      return pathname === "/chat" || pathname === "/";
    }
    return pathname.startsWith(href);
  };

  if (isCollapsed) {
    return (
      <aside className="hidden lg:flex lg:flex-col lg:w-16 lg:border-r lg:border-sidebar-border lg:bg-sidebar">
        <div className="flex h-16 items-center justify-center border-b border-sidebar-border">
          <button
            onClick={() => setIsCollapsed(false)}
            className="p-2 rounded-lg hover:bg-sidebar-accent transition-colors"
            aria-label="Expand sidebar"
          >
            <PanelLeft className="h-5 w-5 text-sidebar-foreground" />
          </button>
        </div>
        {/* Collapsed menu items would go here */}
      </aside>
    );
  }

  return (
    <aside
      className="hidden lg:flex lg:flex-col lg:w-[270px] lg:border-r lg:border-sidebar-border lg:bg-sidebar"
      role="complementary"
    >
      {/* Header with logo and collapse */}
      <div className="flex h-16 items-center gap-2 px-2 border-b border-sidebar-border">
        <div className="flex items-center gap-2 px-2 flex-1">
          <Brain className="h-5 w-5 text-sidebar-muted" />
          <span className="text-[21px] font-medium text-sidebar-muted tracking-normal">
            Axon
          </span>
        </div>
        <button
          onClick={() => setIsCollapsed(true)}
          className="p-2 rounded-lg hover:bg-sidebar-accent transition-colors"
          aria-label="Collapse sidebar"
        >
          <PanelLeft className="h-5 w-5 text-sidebar-foreground" />
        </button>
      </div>

      {/* Main Navigation */}
      <nav className="flex-1 px-2 py-2 space-y-1 overflow-y-auto scrollbar-thin">
        {mainNavigation.map((item) => {
          const active = isActive(item.href);
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-2 h-10 px-3 py-2 rounded-md text-base transition-all duration-200",
                active
                  ? "bg-sidebar-primary text-sidebar-primary-foreground font-medium"
                  : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground font-normal"
              )}
            >
              <item.icon className="h-4 w-4 shrink-0" />
              <span>{item.name}</span>
            </Link>
          );
        })}

        {/* Cohorts Section */}
        <div className="pt-4">
          <div className="h-8 px-2 flex items-center opacity-70">
            <p className="text-base text-sidebar-foreground">Cohorts</p>
          </div>
          <div className="space-y-1 mt-1">
            {cohorts.map((cohort) => (
              <button
                key={cohort.id}
                className="flex items-center gap-2 h-8 pl-2 pr-8 py-2 rounded-md text-base text-sidebar-foreground hover:bg-sidebar-accent transition-colors w-full text-left"
              >
                <Folder className="h-4 w-4 shrink-0" />
                <span className="truncate">{cohort.name}</span>
              </button>
            ))}
            <button className="flex items-center gap-2 h-8 pl-2 pr-8 py-2 rounded-md text-base text-sidebar-foreground/70 hover:bg-sidebar-accent transition-colors w-full text-left opacity-70">
              <MoreHorizontal className="h-4 w-4 shrink-0" />
              <span>More</span>
            </button>
          </div>
        </div>
      </nav>

      {/* Bottom Section */}
      <div className="border-t border-sidebar-border">
        {/* Settings and About */}
        <div className="px-2 py-2 space-y-1">
          {bottomNavigation.map((item) => (
            <Link
              key={item.name}
              href={item.href}
              className="flex items-center gap-2 h-8 px-2 py-2 rounded-md text-base text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors"
            >
              <item.icon className="h-4 w-4 shrink-0" />
              <span>{item.name}</span>
            </Link>
          ))}
        </div>

        {/* User Profile */}
        {user && (
          <div className="px-2 py-2 border-t border-sidebar-border">
            <div className="flex items-center gap-2 px-2 py-2">
              <div className="h-8 w-8 rounded-lg bg-secondary flex items-center justify-center shrink-0">
                {user.image ? (
                  <img
                    src={user.image}
                    alt={user.name || "User"}
                    className="h-full w-full rounded-lg object-cover"
                  />
                ) : (
                  <Brain className="h-4 w-4 text-sidebar-foreground" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-base font-semibold text-sidebar-foreground truncate">
                  {user.name || "Researcher"}
                </p>
                <p className="text-base text-sidebar-foreground/70 truncate">
                  {user.email}
                </p>
              </div>
              <button
                className="p-1 rounded hover:bg-sidebar-accent transition-colors"
                aria-label="User menu"
              >
                <ChevronsUpDown className="h-4 w-4 text-sidebar-foreground/70" />
              </button>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}

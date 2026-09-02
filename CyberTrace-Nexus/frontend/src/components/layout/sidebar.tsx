/**
 * sidebar.tsx - Main navigation sidebar with permission-gated items.
 */

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Briefcase,
  FileSearch,
  LinkIcon,
  History,
  ClipboardList,
  Users,
  BarChart3,
  Shield,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";

interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  permission?: string;
  roles?: string[];
}

const navItems: NavItem[] = [
  {
    label: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    label: "Cases",
    href: "/cases",
    icon: Briefcase,
    permission: "case.view",
  },
  {
    label: "Evidence",
    href: "/evidence",
    icon: FileSearch,
    permission: "evidence.view",
  },
  {
    label: "Chain of Custody",
    href: "/custody",
    icon: LinkIcon,
    permission: "custody.view",
  },
  {
    label: "Audit Log",
    href: "/audit",
    icon: History,
    permission: "audit.view",
  },
  {
    label: "Reports",
    href: "/reports",
    icon: BarChart3,
    permission: "report.generate",
  },
  {
    label: "Users",
    href: "/users",
    icon: Users,
    permission: "user.view",
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const { hasPermission } = useAuth();

  const visibleItems = navItems.filter((item) => {
    if (!item.permission) return true;
    return hasPermission(item.permission);
  });

  return (
    <aside className="hidden md:flex flex-col w-64 border-r border-[var(--border)] bg-[var(--background-secondary)] h-screen sticky top-0">
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 py-5 border-b border-[var(--border)]">
        <div className="p-2 rounded-lg bg-[var(--accent)]/10">
          <Shield className="h-5 w-5 text-[var(--accent)]" />
        </div>
        <div>
          <h1 className="text-sm font-bold text-[var(--foreground)]">DFEMS</h1>
          <p className="text-xs text-[var(--foreground-muted)]">v1.0.0</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {visibleItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname.startsWith(item.href);

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                isActive
                  ? "bg-[var(--accent)]/10 text-[var(--accent)]"
                  : "text-[var(--foreground-muted)] hover:bg-[var(--background-tertiary)] hover:text-[var(--foreground)]"
              )}
            >
              <Icon className="h-4 w-4" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-[var(--border)]">
        <p className="text-xs text-[var(--foreground-muted)]">
          Chain of Custody Tracking
        </p>
      </div>
    </aside>
  );
}

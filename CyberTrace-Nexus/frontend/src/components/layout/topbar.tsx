/**
 * topbar.tsx - Top navigation bar with user info and logout.
 */

"use client";

import { useRouter } from "next/navigation";
import { LogOut, User, ChevronDown, Bell } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/hooks/useAuth";

export function Topbar() {
  const router = useRouter();
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  const getRoleBadgeVariant = (role: string) => {
    switch (role.toUpperCase()) {
      case "ADMINISTRATOR":
        return "danger";
      case "CASE INVESTIGATOR":
        return "info";
      case "FORENSIC ANALYST":
        return "warning";
      case "EVIDENCE CUSTODIAN":
        return "secondary";
      case "AUDITOR":
        return "secondary";
      default:
        return "default";
    }
  };

  const shortenRole = (role: string) => {
    const map: Record<string, string> = {
      "ADMINISTRATOR": "Admin",
      "CASE INVESTIGATOR": "Investigator",
      "FORENSIC ANALYST": "Analyst",
      "EVIDENCE CUSTODIAN": "Custodian",
      "AUDITOR": "Auditor",
    };
    return map[role.toUpperCase()] || role;
  };

  return (
    <header className="sticky top-0 z-40 flex items-center justify-between h-16 px-6 border-b border-[var(--border)] bg-[var(--background-secondary)] backdrop-blur supports-[backdrop-filter]:bg-[var(--background-secondary)]/95">
      {/* Search placeholder */}
      <div className="flex-1 max-w-md">
        <div className="relative">
          <input
            type="search"
            placeholder="Search cases, evidence, custody..."
            className="w-full h-9 rounded-md border border-[var(--border)] bg-[var(--background)] pl-9 pr-4 text-sm text-[var(--foreground)] placeholder:text-[var(--foreground-subtle)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)]"
          />
          <kbd className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-[var(--foreground-muted)]">
            /
          </kbd>
        </div>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-4">
        {/* Notifications (placeholder) */}
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-4 w-4" />
          <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-[var(--accent)]" />
        </Button>

        {/* User dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              className="flex items-center gap-2 h-auto py-1.5 px-2"
            >
              <div className="flex flex-col items-end">
                <span className="text-sm font-medium text-[var(--foreground)]">
                  {user?.username || "User"}
                </span>
                <div className="flex gap-1">
                  {user?.role_names.map((role) => (
                    <Badge
                      key={role}
                      variant={getRoleBadgeVariant(role) as "danger" | "info" | "warning" | "secondary" | "default"}
                      className="text-[10px] px-1.5 py-0"
                    >
                      {shortenRole(role)}
                    </Badge>
                  ))}
                </div>
              </div>
              <ChevronDown className="h-4 w-4 text-[var(--foreground-muted)]" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel>
              <div className="flex flex-col gap-1">
                <span>{user?.username}</span>
                <span className="text-xs font-normal text-[var(--foreground-muted)]">
                  {user?.role_names.join(", ")}
                </span>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="gap-2">
              <User className="h-4 w-4" />
              <span>Profile</span>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              className="gap-2 text-[var(--danger)] focus:text-[var(--danger)]"
              onClick={handleLogout}
            >
              <LogOut className="h-4 w-4" />
              <span>Log out</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}

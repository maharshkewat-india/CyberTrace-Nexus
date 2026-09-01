/**
 * dashboard/page.tsx - Main dashboard with stats and recent activity.
 */

"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  Briefcase,
  FileSearch,
  Link as LinkIcon,
  History,
  Shield,
  TrendingUp,
  AlertCircle,
  Clock,
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import { formatDateTime } from "@/lib/utils";
import type { DashboardStats, AuditLog, Case } from "@/types";

interface StatCardProps {
  title: string;
  value: number;
  description: string;
  icon: React.ReactNode;
  href: string;
  color: "accent" | "success" | "warning" | "info";
}

function StatCard({ title, value, description, icon, href, color }: StatCardProps) {
  const colorMap = {
    accent: "text-[var(--accent)] bg-[var(--accent)]/10",
    success: "text-[var(--success)] bg-[var(--success)]/10",
    warning: "text-[var(--warning)] bg-[var(--warning)]/10",
    info: "text-[var(--info)] bg-[var(--info)]/10",
  };

  return (
    <Link href={href}>
      <Card className="hover:bg-[var(--background-tertiary)] transition-colors cursor-pointer h-full">
        <CardContent className="p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm font-medium text-[var(--foreground-muted)]">
                {title}
              </p>
              <p className="text-3xl font-bold text-[var(--foreground)] mt-2">
                {value.toLocaleString()}
              </p>
              <p className="text-xs text-[var(--foreground-muted)] mt-1">
                {description}
              </p>
            </div>
            <div className={`p-3 rounded-lg ${colorMap[color]}`}>{icon}</div>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}

function getActionVariant(action: string): "default" | "success" | "warning" | "danger" | "info" {
  if (action.includes("FAIL") || action.includes("DISABLED")) return "danger";
  if (action.includes("CREATED") || action.includes("REGISTERED")) return "success";
  if (action.includes("CLOSED") || action.includes("ARCHIVED")) return "warning";
  if (action.includes("LOGIN") || action.includes("LOGOUT")) return "info";
  return "default";
}

export default function DashboardPage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentLogs, setRecentLogs] = useState<AuditLog[]>([]);
  const [recentCases, setRecentCases] = useState<Case[]>([]);
  const [dataLoaded, setDataLoaded] = useState(false);

  const loadStats = useCallback(async () => {
    try {
      const res = await api.get<DashboardStats>("/dashboard/stats");
      setStats(res.data);
    } catch {
      // Stats are public - ignore errors
    }
  }, []);

  const loadRecentData = useCallback(async () => {
    if (!isAuthenticated) return;
    try {
      const [logsRes, casesRes] = await Promise.all([
        api.get<AuditLog[]>("/audit-logs", { params: { limit: 8 } }),
        api.get<Case[]>("/cases", { params: { limit: 5 } }),
      ]);
      setRecentLogs(logsRes.data);
      setRecentCases(casesRes.data);
    } catch {
      // Auth might not be ready yet — silently fail
    } finally {
      setDataLoaded(true);
    }
  }, [isAuthenticated]);

  // Load stats immediately (public endpoint)
  useEffect(() => {
    loadStats();
  }, [loadStats]);

  // Load recent data once auth is ready
  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      loadRecentData();
    }
  }, [authLoading, isAuthenticated, loadRecentData]);

  // Show loading state while auth is checking
  if (authLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="h-8 w-8 border-2 border-[var(--accent)] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-[var(--foreground)]">Dashboard</h1>
        <p className="text-[var(--foreground-muted)] mt-1">
          Overview of your forensics operations
          {user && <span className="ml-2 text-[var(--foreground-subtle)]">— Welcome, {user.username}</span>}
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <StatCard
          title="Total Cases"
          value={stats?.total_cases || 0}
          description={`${stats?.open_cases || 0} open cases`}
          icon={<Briefcase className="h-5 w-5" />}
          href="/cases"
          color="accent"
        />
        <StatCard
          title="Evidence Items"
          value={stats?.total_evidence || 0}
          description={`${stats?.verified_evidence || 0} verified`}
          icon={<FileSearch className="h-5 w-5" />}
          href="/evidence"
          color="success"
        />
        <StatCard
          title="Custody Events"
          value={stats?.custody_events || 0}
          description="Chain of custody transfers"
          icon={<LinkIcon className="h-5 w-5" />}
          href="/custody"
          color="info"
        />
        <StatCard
          title="Audit Entries"
          value={stats?.audit_entries || 0}
          description="System audit log"
          icon={<History className="h-5 w-5" />}
          href="/audit"
          color="warning"
        />
        <StatCard
          title="Open Cases"
          value={stats?.open_cases || 0}
          description="Active investigations"
          icon={<TrendingUp className="h-5 w-5" />}
          href="/cases"
          color="accent"
        />
        <StatCard
          title="Verified Evidence"
          value={stats?.verified_evidence || 0}
          description="Hash-verified items"
          icon={<Shield className="h-5 w-5" />}
          href="/evidence"
          color="success"
        />
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Cases */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Recent Cases</CardTitle>
            <CardDescription>Latest case activity</CardDescription>
          </CardHeader>
          <CardContent>
            {!isAuthenticated || recentCases.length === 0 ? (
              <p className="text-sm text-[var(--foreground-muted)] text-center py-8">
                {isAuthenticated ? "No cases yet" : "Sign in to view cases"}
              </p>
            ) : (
              <div className="space-y-3">
                {recentCases.map((c) => (
                  <Link
                    key={c.id}
                    href={`/cases/${c.id}`}
                    className="flex items-start justify-between p-3 rounded-lg border border-[var(--border)] hover:bg-[var(--background-tertiary)] transition-colors"
                  >
                    <div className="space-y-1 min-w-0 flex-1">
                      <p className="text-sm font-medium text-[var(--foreground)] truncate">
                        {c.title}
                      </p>
                      <p className="text-xs text-[var(--foreground-muted)] font-mono">
                        {c.case_number}
                      </p>
                    </div>
                    <Badge
                      variant={
                        c.status === "Open"
                          ? "success"
                          : c.status === "Archived"
                            ? "secondary"
                            : "warning"
                      }
                    >
                      {c.status}
                    </Badge>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Audit Log */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Recent Activity</CardTitle>
            <CardDescription>System audit trail</CardDescription>
          </CardHeader>
          <CardContent>
            {!isAuthenticated || recentLogs.length === 0 ? (
              <p className="text-sm text-[var(--foreground-muted)] text-center py-8">
                {isAuthenticated ? "No recent activity" : "Sign in to view activity"}
              </p>
            ) : (
              <div className="space-y-3">
                {recentLogs.map((log) => (
                  <div
                    key={log.id}
                    className="flex items-start gap-3 p-3 rounded-lg border border-[var(--border)]"
                  >
                    <div className="mt-0.5">
                      <Clock className="h-4 w-4 text-[var(--foreground-muted)]" />
                    </div>
                    <div className="flex-1 min-w-0 space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <Badge variant={getActionVariant(log.action)}>
                          {log.action}
                        </Badge>
                        {log.username && (
                          <span className="text-xs text-[var(--foreground-muted)]">
                            by {log.username}
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-[var(--foreground)]">
                        {log.description || "-"}
                      </p>
                      <p className="text-xs text-[var(--foreground-muted)]">
                        {formatDateTime(log.timestamp)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

/**
 * audit/page.tsx - Audit log viewer with filters.
 */

"use client";

import { useEffect, useState } from "react";
import { History, AlertCircle, Filter, RefreshCw } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { api, getErrorMessage } from "@/lib/api";
import { formatDateTime } from "@/lib/utils";
import type { AuditLog } from "@/types";

const actionColors: Record<string, "default" | "success" | "warning" | "danger" | "info"> = {
  LOGIN: "info",
  LOGOUT: "default",
  CASE_CREATED: "success",
  CASE_UPDATED: "info",
  CASE_CLOSED: "warning",
  CASE_ARCHIVED: "warning",
  EVIDENCE_REGISTERED: "success",
  EVIDENCE_UPDATED: "info",
  EVIDENCE_VERIFIED: "success",
  EVIDENCE_HASHED: "info",
  CUSTODY_TRANSFERRED: "info",
  USER_CREATED: "success",
  USER_UPDATED: "info",
  USER_DISABLED: "danger",
  USER_ENABLED: "success",
  PASSWORD_RESET: "warning",
  REPORT_GENERATED: "info",
};

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [userFilter, setUserFilter] = useState("");
  const [actionFilter, setActionFilter] = useState("all");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const loadLogs = async () => {
    try {
      setIsLoading(true);
      const params: Record<string, string> = { limit: "500" };
      if (userFilter) params.user = userFilter;
      if (actionFilter && actionFilter !== "all") params.action = actionFilter;
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;

      const response = await api.get<AuditLog[]>("/audit-logs", { params });
      setLogs(response.data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadLogs();
  }, [actionFilter]);

  const handleApply = (e: React.FormEvent) => {
    e.preventDefault();
    loadLogs();
  };

  const handleReset = () => {
    setUserFilter("");
    setActionFilter("all");
    setDateFrom("");
    setDateTo("");
    loadLogs();
  };

  const actionOptions = [
    "LOGIN",
    "LOGOUT",
    "CASE_CREATED",
    "CASE_UPDATED",
    "CASE_CLOSED",
    "CASE_ARCHIVED",
    "EVIDENCE_REGISTERED",
    "EVIDENCE_UPDATED",
    "EVIDENCE_VERIFIED",
    "EVIDENCE_HASHED",
    "CUSTODY_TRANSFERRED",
    "USER_CREATED",
    "USER_UPDATED",
    "USER_DISABLED",
    "USER_ENABLED",
    "PASSWORD_RESET",
    "REPORT_GENERATED",
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-[var(--foreground)]">Audit Log</h1>
          <p className="text-[var(--foreground-muted)] mt-1">
            Complete history of all system actions
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={loadLogs}
          className="gap-2"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Filters */}
      <Card className="p-4">
        <form onSubmit={handleApply} className="flex flex-wrap items-end gap-3">
          <div className="flex-1 min-w-[200px]">
            <Label htmlFor="user" className="text-xs">User</Label>
            <Input
              id="user"
              placeholder="Filter by username..."
              value={userFilter}
              onChange={(e) => setUserFilter(e.target.value)}
            />
          </div>
          <div className="w-48">
            <Label htmlFor="action" className="text-xs">Action</Label>
            <Select value={actionFilter} onValueChange={setActionFilter}>
              <SelectTrigger id="action">
                <SelectValue placeholder="All actions" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Actions</SelectItem>
                {actionOptions.map((opt) => (
                  <SelectItem key={opt} value={opt}>
                    {opt}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="w-40">
            <Label htmlFor="date_from" className="text-xs">From Date</Label>
            <Input
              id="date_from"
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
            />
          </div>
          <div className="w-40">
            <Label htmlFor="date_to" className="text-xs">To Date</Label>
            <Input
              id="date_to"
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
            />
          </div>
          <Button type="submit" variant="secondary" className="gap-2">
            <Filter className="h-4 w-4" />
            Apply
          </Button>
          <Button type="button" variant="ghost" onClick={handleReset}>
            Reset
          </Button>
        </form>
      </Card>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 p-3 rounded-md bg-[var(--danger)]/10 border border-[var(--danger)]/30 text-[var(--danger)] text-sm">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Log Table */}
      <Card>
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="h-8 w-8 border-2 border-[var(--accent)] border-t-transparent rounded-full animate-spin" />
          </div>
        ) : logs.length === 0 ? (
          <div className="text-center py-12">
            <History className="h-12 w-12 mx-auto text-[var(--foreground-muted)]" />
            <p className="mt-4 text-[var(--foreground-muted)]">No audit logs found</p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-40">Timestamp</TableHead>
                <TableHead className="w-32">Action</TableHead>
                <TableHead className="w-32">User</TableHead>
                <TableHead>Description</TableHead>
                <TableHead className="w-24">Entity</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {logs.map((log) => (
                <TableRow key={log.id}>
                  <TableCell className="text-xs font-mono text-[var(--foreground-muted)]">
                    {formatDateTime(log.timestamp)}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={actionColors[log.action] || "default"}
                    >
                      {log.action}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm">
                    {log.username || "-"}
                  </TableCell>
                  <TableCell className="text-sm">
                    {log.description || "-"}
                  </TableCell>
                  <TableCell className="text-xs text-[var(--foreground-muted)]">
                    {log.entity_type && log.entity_id
                      ? `${log.entity_type} #${log.entity_id}`
                      : "-"}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Card>
    </div>
  );
}

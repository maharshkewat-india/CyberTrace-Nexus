/**
 * cases/page.tsx - Cases list with search, filter, and create.
 */

"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus, Search, AlertCircle, Filter } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api, getErrorMessage } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import { formatDate } from "@/lib/utils";
import type { Case, CaseCreate, CasePriority, CaseStatus } from "@/types";

const priorityColors: Record<CasePriority, "default" | "info" | "warning" | "danger"> = {
  Low: "default",
  Medium: "info",
  High: "warning",
  Critical: "danger",
};

const statusColors: Record<CaseStatus, "success" | "warning" | "secondary" | "info"> = {
  Open: "success",
  "Under Investigation": "info",
  Closed: "secondary",
  Archived: "secondary",
};

export default function CasesPage() {
  const { hasPermission } = useAuth();
  const [cases, setCases] = useState<Case[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [priorityFilter, setPriorityFilter] = useState<string>("all");
  const [createOpen, setCreateOpen] = useState(false);
  const [creating, setCreating] = useState(false);

  // New case form
  const [newTitle, setNewTitle] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [newPriority, setNewPriority] = useState<CasePriority>("Medium");
  const [newIncidentDate, setNewIncidentDate] = useState("");

  const canCreate = hasPermission("case.create");

  const loadCases = async () => {
    try {
      setIsLoading(true);
      const params: Record<string, string> = { limit: "200" };
      if (statusFilter && statusFilter !== "all") params.status = statusFilter;
      if (priorityFilter && priorityFilter !== "all") params.priority = priorityFilter;
      if (search) params.search = search;

      const response = await api.get<Case[]>("/cases", { params });
      setCases(response.data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadCases();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter, priorityFilter]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadCases();
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;

    try {
      setCreating(true);
      const payload: CaseCreate = {
        title: newTitle,
        description: newDescription,
        priority: newPriority,
        incident_date: newIncidentDate || undefined,
      };
      await api.post("/cases", payload);
      setCreateOpen(false);
      setNewTitle("");
      setNewDescription("");
      setNewPriority("Medium");
      setNewIncidentDate("");
      loadCases();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-[var(--foreground)]">Cases</h1>
          <p className="text-[var(--foreground-muted)] mt-1">
            Manage forensic investigation cases
          </p>
        </div>
        {canCreate && (
          <Dialog open={createOpen} onOpenChange={setCreateOpen}>
            <DialogTrigger asChild>
              <Button className="gap-2">
                <Plus className="h-4 w-4" />
                New Case
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New Case</DialogTitle>
                <DialogDescription>
                  Start a new forensic investigation case
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleCreate} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="title">Title</Label>
                  <Input
                    id="title"
                    placeholder="e.g., Phishing investigation #2024-12"
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Input
                    id="description"
                    placeholder="Brief description of the case"
                    value={newDescription}
                    onChange={(e) => setNewDescription(e.target.value)}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="priority">Priority</Label>
                    <Select value={newPriority} onValueChange={(v) => setNewPriority(v as CasePriority)}>
                      <SelectTrigger id="priority">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Low">Low</SelectItem>
                        <SelectItem value="Medium">Medium</SelectItem>
                        <SelectItem value="High">High</SelectItem>
                        <SelectItem value="Critical">Critical</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="incident_date">Incident Date</Label>
                    <Input
                      id="incident_date"
                      type="date"
                      value={newIncidentDate}
                      onChange={(e) => setNewIncidentDate(e.target.value)}
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => setCreateOpen(false)}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" loading={creating}>
                    Create Case
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        )}
      </div>

      {/* Filters */}
      <Card className="p-4">
        <form onSubmit={handleSearch} className="flex flex-wrap items-end gap-3">
          <div className="flex-1 min-w-[200px]">
            <Label htmlFor="search" className="text-xs">Search</Label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--foreground-muted)]" />
              <Input
                id="search"
                placeholder="Search by title, number, or description..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
          </div>
          <div className="w-40">
            <Label htmlFor="status" className="text-xs">Status</Label>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger id="status">
                <SelectValue placeholder="All" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="Open">Open</SelectItem>
                <SelectItem value="Under Investigation">Under Investigation</SelectItem>
                <SelectItem value="Closed">Closed</SelectItem>
                <SelectItem value="Archived">Archived</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="w-40">
            <Label htmlFor="priority" className="text-xs">Priority</Label>
            <Select value={priorityFilter} onValueChange={setPriorityFilter}>
              <SelectTrigger id="priority">
                <SelectValue placeholder="All" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Priorities</SelectItem>
                <SelectItem value="Low">Low</SelectItem>
                <SelectItem value="Medium">Medium</SelectItem>
                <SelectItem value="High">High</SelectItem>
                <SelectItem value="Critical">Critical</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <Button type="submit" variant="secondary" className="gap-2">
            <Filter className="h-4 w-4" />
            Apply
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

      {/* Cases Table */}
      <Card>
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="h-8 w-8 border-2 border-[var(--accent)] border-t-transparent rounded-full animate-spin" />
          </div>
        ) : cases.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-[var(--foreground-muted)]">No cases found</p>
            {canCreate && (
              <Button
                variant="link"
                onClick={() => setCreateOpen(true)}
                className="mt-2"
              >
                Create your first case
              </Button>
            )}
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Case Number</TableHead>
                <TableHead>Title</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Priority</TableHead>
                <TableHead>Created</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {cases.map((c) => (
                <TableRow key={c.id}>
                  <TableCell className="font-mono text-xs">
                    <Link
                      href={`/cases/${c.id}`}
                      className="text-[var(--accent)] hover:underline"
                    >
                      {c.case_number}
                    </Link>
                  </TableCell>
                  <TableCell>
                    <Link
                      href={`/cases/${c.id}`}
                      className="text-[var(--foreground)] hover:text-[var(--accent)] font-medium"
                    >
                      {c.title}
                    </Link>
                  </TableCell>
                  <TableCell>
                    <Badge variant={statusColors[c.status]}>{c.status}</Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={priorityColors[c.priority]}>{c.priority}</Badge>
                  </TableCell>
                  <TableCell className="text-sm text-[var(--foreground-muted)]">
                    {formatDate(c.created_at)}
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

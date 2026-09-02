/**
 * evidence/page.tsx - Evidence list with search, filters, and hash display.
 */

"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Plus,
  Search,
  AlertCircle,
  FileSearch,
  Copy,
  Check,
  Shield,
  AlertTriangle,
} from "lucide-react";
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { api, getErrorMessage } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import { formatDate, truncateHash, formatFileSize } from "@/lib/utils";
import type { Evidence, Case, EvidenceType } from "@/types";

const statusColors = {
  Active: "info",
  Verified: "success",
  Corrupted: "danger",
  Released: "secondary",
} as const;

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button
      onClick={handleCopy}
      className="inline-flex items-center gap-1 text-xs text-[var(--foreground-muted)] hover:text-[var(--foreground)]"
      title="Copy to clipboard"
    >
      {copied ? (
        <Check className="h-3 w-3 text-[var(--success)]" />
      ) : (
        <Copy className="h-3 w-3" />
      )}
    </button>
  );
}

export default function EvidencePage() {
  const { hasPermission } = useAuth();
  const [evidence, setEvidence] = useState<Evidence[]>([]);
  const [cases, setCases] = useState<Case[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [registerOpen, setRegisterOpen] = useState(false);
  const [registering, setRegistering] = useState(false);

  // Register form
  const [selectedCaseId, setSelectedCaseId] = useState<number | null>(null);
  const [filePath, setFilePath] = useState("");
  const [evidenceType, setEvidenceType] = useState<EvidenceType>("Other");
  const [description, setDescription] = useState("");
  const [source, setSource] = useState("");

  const canCreate = hasPermission("evidence.create");

  const loadEvidence = async () => {
    try {
      setIsLoading(true);
      const response = await api.get<Evidence[]>("/evidence", { params: { limit: 200 } });
      setEvidence(response.data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  const loadCases = async () => {
    try {
      const response = await api.get<Case[]>("/cases", { params: { limit: 500 } });
      setCases(response.data);
    } catch (err) {
      console.error("Failed to load cases", err);
    }
  };

  useEffect(() => {
    loadEvidence();
    loadCases();
  }, []);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCaseId || !filePath) return;

    try {
      setRegistering(true);
      await api.post("/evidence", {
        case_id: selectedCaseId,
        file_path: filePath,
        evidence_type: evidenceType,
        description,
        source: source || undefined,
      });
      setRegisterOpen(false);
      setSelectedCaseId(null);
      setFilePath("");
      setEvidenceType("Other");
      setDescription("");
      setSource("");
      loadEvidence();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setRegistering(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-[var(--foreground)]">Evidence</h1>
          <p className="text-[var(--foreground-muted)] mt-1">
            Manage and verify evidence items
          </p>
        </div>
        {canCreate && (
          <Dialog open={registerOpen} onOpenChange={setRegisterOpen}>
            <DialogTrigger asChild>
              <Button className="gap-2">
                <Plus className="h-4 w-4" />
                Register Evidence
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-lg">
              <DialogHeader>
                <DialogTitle>Register New Evidence</DialogTitle>
                <DialogDescription>
                  Register an evidence item with automatic MD5 and SHA-256 hash computation
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleRegister} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="case_id">Case</Label>
                  <Select
                    value={selectedCaseId?.toString() || ""}
                    onValueChange={(v) => setSelectedCaseId(parseInt(v))}
                  >
                    <SelectTrigger id="case_id">
                      <SelectValue placeholder="Select a case" />
                    </SelectTrigger>
                    <SelectContent>
                      {cases.map((c) => (
                        <SelectItem key={c.id} value={c.id.toString()}>
                          {c.case_number} - {c.title}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="file_path">File Path</Label>
                  <Input
                    id="file_path"
                    placeholder="C:\Evidence\file.dd"
                    value={filePath}
                    onChange={(e) => setFilePath(e.target.value)}
                    required
                  />
                  <p className="text-xs text-[var(--foreground-muted)]">
                    Full path to the evidence file on the local system
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="type">Evidence Type</Label>
                    <Select value={evidenceType} onValueChange={(v) => setEvidenceType(v as EvidenceType)}>
                      <SelectTrigger id="type">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Hard Drive">Hard Drive</SelectItem>
                        <SelectItem value="USB Drive">USB Drive</SelectItem>
                        <SelectItem value="Mobile Device">Mobile Device</SelectItem>
                        <SelectItem value="Memory Card">Memory Card</SelectItem>
                        <SelectItem value="Network Capture">Network Capture</SelectItem>
                        <SelectItem value="Screenshot">Screenshot</SelectItem>
                        <SelectItem value="Document">Document</SelectItem>
                        <SelectItem value="Email">Email</SelectItem>
                        <SelectItem value="Log File">Log File</SelectItem>
                        <SelectItem value="Other">Other</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="source">Source</Label>
                    <Input
                      id="source"
                      placeholder="e.g., Seized from suspect"
                      value={source}
                      onChange={(e) => setSource(e.target.value)}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Input
                    id="description"
                    placeholder="Brief description of the evidence"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                  />
                </div>
                <DialogFooter>
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => setRegisterOpen(false)}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" loading={registering}>
                    Register Evidence
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 p-3 rounded-md bg-[var(--danger)]/10 border border-[var(--danger)]/30 text-[var(--danger)] text-sm">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Evidence Table */}
      <Card>
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="h-8 w-8 border-2 border-[var(--accent)] border-t-transparent rounded-full animate-spin" />
          </div>
        ) : evidence.length === 0 ? (
          <div className="text-center py-12">
            <FileSearch className="h-12 w-12 mx-auto text-[var(--foreground-muted)]" />
            <p className="mt-4 text-[var(--foreground-muted)]">No evidence registered</p>
            {canCreate && (
              <Button
                variant="link"
                onClick={() => setRegisterOpen(true)}
                className="mt-2"
              >
                Register your first evidence
              </Button>
            )}
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Evidence ID</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Description</TableHead>
                <TableHead>Size</TableHead>
                <TableHead>MD5</TableHead>
                <TableHead>SHA-256</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Registered</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {evidence.map((ev) => (
                <TableRow key={ev.id}>
                  <TableCell className="font-mono text-xs">
                    {ev.evidence_id}
                  </TableCell>
                  <TableCell>
                    <Badge variant="secondary">{ev.evidence_type}</Badge>
                  </TableCell>
                  <TableCell className="max-w-[200px] truncate">
                    {ev.description || "-"}
                  </TableCell>
                  <TableCell className="text-sm">
                    {formatFileSize(ev.file_size)}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      <span className="font-mono text-xs text-[var(--foreground-muted)]">
                        {truncateHash(ev.md5, 6, 4)}
                      </span>
                      {ev.md5 && <CopyButton text={ev.md5} />}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      <span className="font-mono text-xs text-[var(--foreground-muted)]">
                        {truncateHash(ev.sha256, 6, 4)}
                      </span>
                      {ev.sha256 && <CopyButton text={ev.sha256} />}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      {ev.status === "Verified" ? (
                        <Shield className="h-4 w-4 text-[var(--success)]" />
                      ) : ev.status === "Corrupted" ? (
                        <AlertTriangle className="h-4 w-4 text-[var(--danger)]" />
                      ) : null}
                      <Badge variant={statusColors[ev.status as keyof typeof statusColors] || "default"}>
                        {ev.status}
                      </Badge>
                    </div>
                  </TableCell>
                  <TableCell className="text-sm text-[var(--foreground-muted)]">
                    {formatDate(ev.created_at)}
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

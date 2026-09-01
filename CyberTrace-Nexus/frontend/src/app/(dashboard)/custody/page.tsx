/**
 * custody/page.tsx - Chain of custody timeline view.
 */

"use client";

import { useEffect, useState } from "react";
import { Link as LinkIcon, AlertCircle, ArrowRight, MapPin, User, Clock, Plus } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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
import { api, getErrorMessage } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import { formatDateTime } from "@/lib/utils";
import type { CustodyEvent, Evidence, CustodyAction } from "@/types";

const actionColors: Record<CustodyAction, "info" | "success" | "warning"> = {
  HANDOFF: "info",
  SECURE_STORAGE: "success",
  RELEASED: "warning",
};

export default function CustodyPage() {
  const { hasPermission } = useAuth();
  const [events, setEvents] = useState<CustodyEvent[]>([]);
  const [evidence, setEvidence] = useState<Evidence[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [creating, setCreating] = useState(false);

  // New custody form
  const [action, setAction] = useState<CustodyAction>("HANDOFF");
  const [selectedEvidenceId, setSelectedEvidenceId] = useState<number | null>(null);
  const [fromPerson, setFromPerson] = useState("");
  const [toPerson, setToPerson] = useState("");
  const [location, setLocation] = useState("");
  const [notes, setNotes] = useState("");

  const canCreate = hasPermission("custody.create");

  const loadData = async () => {
    try {
      setIsLoading(true);
      // For demo: get custody from each evidence
      const evRes = await api.get<Evidence[]>("/evidence", { params: { limit: 200 } });
      setEvidence(evRes.data);

      // Get custody events for all evidence
      const allCustody: CustodyEvent[] = [];
      for (const ev of evRes.data.slice(0, 50)) {
        try {
          const c = await api.get<CustodyEvent[]>(`/evidence/${ev.id}/custody`);
          allCustody.push(...c.data);
        } catch {
          // Skip if no custody
        }
      }
      // Sort by date desc
      allCustody.sort((a, b) => new Date(b.event_time).getTime() - new Date(a.event_time).getTime());
      setEvents(allCustody);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEvidenceId) return;

    try {
      setCreating(true);
      await api.post(`/evidence/${selectedEvidenceId}/custody`, {
        action,
        evidence_id: selectedEvidenceId,
        from_person: fromPerson,
        to_person: toPerson,
        location,
        notes: notes || undefined,
      });
      setCreateOpen(false);
      setAction("HANDOFF");
      setSelectedEvidenceId(null);
      setFromPerson("");
      setToPerson("");
      setLocation("");
      setNotes("");
      loadData();
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
          <h1 className="text-3xl font-bold text-[var(--foreground)]">Chain of Custody</h1>
          <p className="text-[var(--foreground-muted)] mt-1">
            Track all evidence transfers and handoffs
          </p>
        </div>
        {canCreate && (
          <Dialog open={createOpen} onOpenChange={setCreateOpen}>
            <DialogTrigger asChild>
              <Button className="gap-2">
                <Plus className="h-4 w-4" />
                Record Custody Event
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Record Custody Event</DialogTitle>
                <DialogDescription>
                  Add a new chain of custody event for evidence
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleCreate} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="evidence_id">Evidence</Label>
                  <Select
                    value={selectedEvidenceId?.toString() || ""}
                    onValueChange={(v) => setSelectedEvidenceId(parseInt(v))}
                  >
                    <SelectTrigger id="evidence_id">
                      <SelectValue placeholder="Select evidence" />
                    </SelectTrigger>
                    <SelectContent>
                      {evidence.map((ev) => (
                        <SelectItem key={ev.id} value={ev.id.toString()}>
                          {ev.evidence_id} - {ev.description || ev.evidence_type}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="action">Action</Label>
                  <Select value={action} onValueChange={(v) => setAction(v as CustodyAction)}>
                    <SelectTrigger id="action">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="HANDOFF">Handoff</SelectItem>
                      <SelectItem value="SECURE_STORAGE">Secure Storage</SelectItem>
                      <SelectItem value="RELEASED">Released</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="from_person">From Person</Label>
                    <Input
                      id="from_person"
                      placeholder="Source custodian"
                      value={fromPerson}
                      onChange={(e) => setFromPerson(e.target.value)}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="to_person">To Person</Label>
                    <Input
                      id="to_person"
                      placeholder="Receiving custodian"
                      value={toPerson}
                      onChange={(e) => setToPerson(e.target.value)}
                      required
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="location">Location</Label>
                  <Input
                    id="location"
                    placeholder="e.g., Evidence Vault A"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="notes">Notes (optional)</Label>
                  <Input
                    id="notes"
                    placeholder="Additional notes"
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                  />
                </div>
                <DialogFooter>
                  <Button type="button" variant="ghost" onClick={() => setCreateOpen(false)}>
                    Cancel
                  </Button>
                  <Button type="submit" loading={creating}>
                    Record Event
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

      {/* Timeline */}
      <Card className="p-6">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="h-8 w-8 border-2 border-[var(--accent)] border-t-transparent rounded-full animate-spin" />
          </div>
        ) : events.length === 0 ? (
          <div className="text-center py-12">
            <LinkIcon className="h-12 w-12 mx-auto text-[var(--foreground-muted)]" />
            <p className="mt-4 text-[var(--foreground-muted)]">No custody events recorded</p>
            {canCreate && (
              <Button variant="link" onClick={() => setCreateOpen(true)} className="mt-2">
                Record your first event
              </Button>
            )}
          </div>
        ) : (
          <div className="relative">
            {/* Vertical line */}
            <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-[var(--border)]" />
            <div className="space-y-6">
              {events.map((event) => (
                <div key={event.id} className="relative pl-12">
                  {/* Dot */}
                  <div className="absolute left-0 top-1 h-9 w-9 rounded-full bg-[var(--card)] border-2 border-[var(--accent)] flex items-center justify-center">
                    <LinkIcon className="h-4 w-4 text-[var(--accent)]" />
                  </div>

                  {/* Content */}
                  <div className="border border-[var(--border)] rounded-lg p-4 bg-[var(--background-secondary)]">
                    <div className="flex items-start justify-between flex-wrap gap-2">
                      <div className="flex items-center gap-2 flex-wrap">
                        <Badge variant={actionColors[event.action]}>
                          {event.action}
                        </Badge>
                        {event.evidence_tag && (
                          <span className="font-mono text-xs text-[var(--foreground-muted)]">
                            {event.evidence_tag}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-1 text-xs text-[var(--foreground-muted)]">
                        <Clock className="h-3 w-3" />
                        {formatDateTime(event.event_time)}
                      </div>
                    </div>

                    <div className="mt-3 flex items-center gap-3 flex-wrap">
                      <div className="flex items-center gap-2">
                        <User className="h-4 w-4 text-[var(--foreground-muted)]" />
                        <span className="text-sm font-medium">{event.from_person}</span>
                      </div>
                      <ArrowRight className="h-4 w-4 text-[var(--foreground-muted)]" />
                      <div className="flex items-center gap-2">
                        <User className="h-4 w-4 text-[var(--foreground-muted)]" />
                        <span className="text-sm font-medium">{event.to_person}</span>
                      </div>
                    </div>

                    {event.location && (
                      <div className="mt-2 flex items-center gap-2 text-sm text-[var(--foreground-muted)]">
                        <MapPin className="h-3.5 w-3.5" />
                        {event.location}
                      </div>
                    )}

                    {event.notes && (
                      <p className="mt-2 text-sm text-[var(--foreground-muted)]">
                        {event.notes}
                      </p>
                    )}

                    {event.recorded_by_username && (
                      <p className="mt-2 text-xs text-[var(--foreground-subtle)]">
                        Recorded by {event.recorded_by_username}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}

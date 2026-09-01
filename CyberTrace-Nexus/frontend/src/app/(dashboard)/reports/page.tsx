/**
 * reports/page.tsx - Report generation.
 */

"use client";

import { useEffect, useState } from "react";
import { BarChart3, AlertCircle, FileText, Download, Loader2 } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { api, getErrorMessage } from "@/lib/api";
import { formatDateTime } from "@/lib/utils";
import type { Case, ReportType } from "@/types";

export default function ReportsPage() {
  const [cases, setCases] = useState<Case[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<number | null>(null);
  const [reportType, setReportType] = useState<ReportType>("summary");
  const [isLoading, setIsLoading] = useState(false);
  const [report, setReport] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadCases() {
      try {
        const res = await api.get<Case[]>("/cases", { params: { limit: 200 } });
        setCases(res.data);
        if (res.data.length > 0) {
          setSelectedCaseId(res.data[0].id);
        }
      } catch (err) {
        setError(getErrorMessage(err));
      }
    }
    loadCases();
  }, []);

  const handleGenerate = async () => {
    if (!selectedCaseId) return;
    try {
      setIsLoading(true);
      setError(null);
      const res = await api.get(`/reports/case/${selectedCaseId}`, {
        params: { report_type: reportType },
      });
      setReport(res.data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownload = () => {
    if (!report) return;
    const json = JSON.stringify(report, null, 2);
    const blob = new Blob([json], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `case-${selectedCaseId}-${reportType}-report.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-[var(--foreground)]">Reports</h1>
        <p className="text-[var(--foreground-muted)] mt-1">
          Generate forensic reports for cases
        </p>
      </div>

      {/* Generation form */}
      <Card>
        <CardHeader>
          <CardTitle>Generate Report</CardTitle>
          <CardDescription>
            Select a case and report type to generate a comprehensive forensic report
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="case">Case</Label>
              <Select
                value={selectedCaseId?.toString() || ""}
                onValueChange={(v) => setSelectedCaseId(parseInt(v))}
              >
                <SelectTrigger id="case">
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
              <Label htmlFor="report_type">Report Type</Label>
              <Select value={reportType} onValueChange={(v) => setReportType(v as ReportType)}>
                <SelectTrigger id="report_type">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="summary">Case Summary</SelectItem>
                  <SelectItem value="evidence">Evidence Report</SelectItem>
                  <SelectItem value="custody">Custody Report</SelectItem>
                  <SelectItem value="audit">Audit Report</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button onClick={handleGenerate} loading={isLoading} disabled={!selectedCaseId}>
              <FileText className="h-4 w-4 mr-2" />
              Generate Report
            </Button>
            {report && (
              <Button variant="outline" onClick={handleDownload}>
                <Download className="h-4 w-4 mr-2" />
                Download JSON
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 p-3 rounded-md bg-[var(--danger)]/10 border border-[var(--danger)]/30 text-[var(--danger)] text-sm">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Report display */}
      {isLoading ? (
        <Card className="p-12">
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="h-8 w-8 animate-spin text-[var(--accent)]" />
            <p className="text-sm text-[var(--foreground-muted)]">Generating report...</p>
          </div>
        </Card>
      ) : report ? (
        <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle>Report</CardTitle>
                <CardDescription>
                  Generated {formatDateTime(report.generated_at as string)}
                </CardDescription>
              </div>
              <Badge variant="info">{report.type as string}</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <pre className="p-4 rounded-md bg-[var(--background-tertiary)] border border-[var(--border)] text-xs font-mono overflow-x-auto max-h-[600px] overflow-y-auto">
              {JSON.stringify(report, null, 2)}
            </pre>
          </CardContent>
        </Card>
      ) : (
        <Card className="p-12">
          <div className="text-center">
            <BarChart3 className="h-12 w-12 mx-auto text-[var(--foreground-muted)]" />
            <p className="mt-4 text-[var(--foreground-muted)]">
              Select a case and report type, then click &quot;Generate Report&quot;
            </p>
          </div>
        </Card>
      )}
    </div>
  );
}

/**
 * types/index.ts - TypeScript type definitions.
 */

// ============================================================
// Auth Types
// ============================================================

// Role names match backend: ADMINISTRATOR, CASE INVESTIGATOR,
// FORENSIC ANALYST, EVIDENCE CUSTODIAN, AUDITOR
export type RoleName =
  | "ADMINISTRATOR"
  | "CASE INVESTIGATOR"
  | "FORENSIC ANALYST"
  | "EVIDENCE CUSTODIAN"
  | "AUDITOR";

export interface User {
  id: number;
  username: string;
  role_names: string[];
  permissions: string[];
  is_active: boolean;
  created_at: string;
  last_login: string | null;
  must_change_password: boolean;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// ============================================================
// Case Types
// ============================================================

export type CaseStatus = "Open" | "Under Investigation" | "Closed" | "Archived";
export type CasePriority = "Low" | "Medium" | "High" | "Critical";

export interface Case {
  id: number;
  case_number: string;
  title: string;
  incident_date: string | null;
  status: CaseStatus;
  priority: CasePriority;
  description: string;
  created_by: number;
  created_at: string;
  closed_at: string | null;
  archived_at: string | null;
}

export interface CaseCreate {
  title: string;
  incident_date?: string;
  priority?: CasePriority;
  description?: string;
}

export interface CaseUpdate {
  title?: string;
  incident_date?: string;
  status?: CaseStatus;
  priority?: CasePriority;
  description?: string;
  closed_at?: string;
  archived_at?: string;
}

// ============================================================
// Evidence Types
// ============================================================

export type EvidenceStatus = "Active" | "Verified" | "Corrupted" | "Released";
export type EvidenceType =
  | "Hard Drive"
  | "USB Drive"
  | "Mobile Device"
  | "Memory Card"
  | "Network Capture"
  | "Screenshot"
  | "Document"
  | "Email"
  | "Log File"
  | "Other";

export interface Evidence {
  id: number;
  evidence_id: string;
  case_id: number;
  evidence_type: EvidenceType;
  description: string;
  source: string | null;
  file_path: string | null;
  file_size: number | null;
  file_extension: string | null;
  acquisition_time: string | null;
  original_modified_time: string | null;
  registered_by: number;
  status: EvidenceStatus;
  created_at: string;
  md5: string | null;
  sha256: string | null;
}

export interface EvidenceCreate {
  case_id: number;
  file_path?: string;
  evidence_type: EvidenceType;
  description: string;
  source?: string;
}

export interface EvidenceUpdate {
  evidence_type?: EvidenceType;
  description?: string;
  source?: string;
  status?: EvidenceStatus;
}

export interface HashVerifyResponse {
  status: "PASS" | "WARNING" | "FAIL";
  evidence_id: number;
  evidence_tag: string;
  original_md5: string | null;
  original_sha256: string | null;
  current_md5: string;
  current_sha256: string;
  md5_match: boolean;
  sha256_match: boolean;
  verified_by: number;
  verified_at: string;
}

// ============================================================
// Custody Types
// ============================================================

export type CustodyAction = "HANDOFF" | "SECURE_STORAGE" | "RELEASED";

export interface CustodyEvent {
  id: number;
  action: CustodyAction;
  evidence_id: number;
  evidence_tag: string | null;
  from_person: string;
  to_person: string;
  location: string;
  event_time: string;
  notes: string | null;
  recorded_by: number;
  recorded_by_username: string | null;
}

export interface CustodyCreate {
  action: CustodyAction;
  evidence_id: number;
  from_person: string;
  to_person: string;
  location: string;
  notes?: string;
}

// ============================================================
// Audit Types
// ============================================================

export type AuditAction =
  | "LOGIN"
  | "LOGOUT"
  | "CASE_CREATED"
  | "CASE_UPDATED"
  | "CASE_CLOSED"
  | "CASE_ARCHIVED"
  | "EVIDENCE_REGISTERED"
  | "EVIDENCE_UPDATED"
  | "EVIDENCE_VERIFIED"
  | "EVIDENCE_HASHED"
  | "CUSTODY_TRANSFERRED"
  | "USER_CREATED"
  | "USER_UPDATED"
  | "USER_DISABLED"
  | "USER_ENABLED"
  | "PASSWORD_RESET"
  | "REPORT_GENERATED";

export interface AuditLog {
  id: number;
  timestamp: string;
  action: AuditAction;
  username: string | null;
  role_name: string | null;
  description: string | null;
  entity_type: string | null;
  entity_id: number | null;
  ip_address: string | null;
  result: "SUCCESS" | "FAIL" | null;
}

// ============================================================
// Dashboard Types
// ============================================================

export interface DashboardStats {
  total_cases: number;
  open_cases: number;
  total_evidence: number;
  verified_evidence: number;
  custody_events: number;
  audit_entries: number;
}

// ============================================================
// Report Types
// ============================================================

export type ReportType = "summary" | "evidence" | "custody" | "audit";

export interface CaseReport {
  type: string;
  case: {
    id: number;
    case_number: string;
    title: string;
    status: CaseStatus;
    priority: CasePriority;
    incident_date: string | null;
    description: string;
    created_by: number;
    created_at: string;
    closed_at: string | null;
    archived_at: string | null;
  };
  generated_at: string;
  generated_by: string;
}

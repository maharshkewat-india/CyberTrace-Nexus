# CyberTrace Nexus

## 1. Project Identity

**Current Repository Name:** Digital Forensics Evidence Management System

**Evolved Project Name:** CyberTrace Nexus

**Full Concept:** AI-Assisted Digital Incident Reconstruction & Evidence Correlation Platform

**Core Thesis:** Turn disconnected digital evidence into an explainable reconstruction of what happened during a cyber incident.

---

## 2. Vision

CyberTrace Nexus is not another SIEM, vulnerability scanner, password checker, generic forensic toolkit, or AI chatbot. It is an **evidence-grounded incident reconstruction platform** that helps investigators answer:

1. What happened?
2. When did it happen?
3. What happened first?
4. What happened next?
5. Which user/device/process/file/network activity is related?
6. Which evidence supports each conclusion?
7. Which indicators are suspicious?
8. How confident is the system?
9. What attack behavior may have occurred?
10. Can the investigator reproduce/replay the incident timeline?
11. Can the complete investigation be converted into a professional report?

---

## 3. Problem Statement

Modern digital investigations suffer from a critical gap: evidence exists, but it is rarely connected into a coherent, explainable story. Investigators must manually correlate logs, files, network activity, and user behavior across disparate tools. There is no structured platform that:

- Preserves evidence integrity from collection to reporting
- Extracts and normalizes forensic artifacts into temporal events
- Correlates those events into a coherent timeline
- Maps relationships between entities (users, IPs, files, processes)
- Constructs an explainable incident reconstruction
- Distinguishes fact from inference from hypothesis
- Supports AI-assisted questioning grounded strictly in evidence
- Replays the incident chronologically
- Generates professional, court-ready investigation reports

---

## 4. Why This Project Exists

The Digital Forensics Evidence Management System already provides a secure, auditable foundation for evidence management. That foundation is **not discarded**. It becomes the first module of CyberTrace Nexus. Every future enhancement is built on top of existing, proven, working code — not in replacement of it.

---

## 5. Originality & Differentiation

The primary differentiation axis is:

**EVIDENCE → CORRELATION → RECONSTRUCTION → EXPLANATION → REPLAY**

This project does **not**:

- Add blockchain without a real requirement
- Add AI without a useful investigation purpose
- Add unnecessary microservices
- Add unnecessary cloud infrastructure
- Add unnecessary complexity

Every technology and feature must answer: **"Why is this needed?"**

---

## 6. Existing Project Foundation

The repository contains a mature, working digital forensics evidence management system with authentication, RBAC, case management, evidence management, chain of custody, audit logging, and reporting capabilities.

**Verification source:** The code was read directly from the repository files listed in Section 7.

---

## 7. What We Are Reusing (Currently Existing)

### 7.1 Backend (FastAPI + SQLite)

| Component | Location | Status |
|-----------|----------|--------|
| Auth & RBAC | `backend/auth/`, `backend/core/` | ✅ Existing |
| Case management API | `backend/api/cases.py` | ✅ Existing |
| Evidence management API | `backend/api/evidence.py` | ✅ Existing |
| Chain of custody API | `backend/api/custody.py` | ✅ Existing |
| Audit logging API | `backend/api/audit.py` | ✅ Existing |
| Report generation API | `backend/api/reports.py` | ✅ Existing |
| User management API | `backend/api/users.py` | ✅ Existing |
| Hashing service | `backend/services/hashing.py` | ✅ Existing |
| Audit service | `backend/services/audit_service.py` | ✅ Existing |
| Custody service | `backend/services/custody_service.py` | ✅ Existing |
| Case service | `backend/services/case_service.py` | ✅ Existing |
| Evidence service | `backend/services/evidence_service.py` | ✅ Existing |
| Data models | `backend/models/models.py` | ✅ Existing |
| Database schema | `backend/database/schema.sql` | ✅ Existing |
| Pydantic schemas | `backend/schemas/` | ✅ Existing |
| Password hashing | `backend/auth/password_manager.py` | ✅ Existing (PBKDF2-HMAC-SHA256) |
| JWT security | `backend/core/security.py` | ✅ Existing |
| Authorization engine | `backend/auth/authorization.py` | ✅ Existing |

### 7.2 Frontend (Next.js 16 + React 19 + Tailwind CSS 4)

| Component | Location | Status |
|-----------|----------|--------|
| Login page | `frontend/src/app/login/page.tsx` | ✅ Existing |
| Dashboard | `frontend/src/app/(dashboard)/dashboard/page.tsx` | ✅ Existing |
| Cases page | `frontend/src/app/(dashboard)/cases/page.tsx` | ✅ Existing |
| Evidence page | `frontend/src/app/(dashboard)/evidence/page.tsx` | ✅ Existing |
| Custody page | `frontend/src/app/(dashboard)/custody/page.tsx` | ✅ Existing |
| Audit page | `frontend/src/app/(dashboard)/audit/page.tsx` | ✅ Existing |
| Users page | `frontend/src/app/(dashboard)/users/page.tsx` | ✅ Existing |
| Reports page | `frontend/src/app/(dashboard)/reports/page.tsx` | ✅ Existing |
| Layout/Sidebar/Topbar | `frontend/src/components/layout/` | ✅ Existing |
| Auth context | `frontend/src/hooks/useAuth.tsx` | ✅ Existing |
| UI components | `frontend/src/components/ui/` | ✅ Existing |

### 7.3 Database Schema (SQLite)

Existing tables (verified from `backend/database/schema.sql`):

- `users`, `roles`, `permissions`, `role_permissions`, `user_roles`, `sessions`
- `system_settings`
- `cases`, `case_users`
- `evidence`, `evidence_hashes`
- `custody_events`
- `analysis_notes`
- `audit_logs`

### 7.4 Tests & Demo

| Component | Location | Status |
|-----------|----------|--------|
| Test suite | `tests/test_basic.py` | ✅ Existing |
| RBAC integration tests | `tests/test_integration_rbac.py` | ✅ Existing |
| UI RBAC tests | `tests/test_ui_rbac.py` | ✅ Existing |
| Demo flow | `demo/demo_flow.py` | ✅ Existing |

---

## 8. What We Are Adding (Planned / Future)

The following modules and capabilities are **planned additions** to be implemented incrementally. They are described here for planning purposes only and have **not yet been implemented**.

- Forensic artifact extraction engine
- Event normalization pipeline
- Timeline engine
- Evidence correlation engine
- Evidence relationship graph
- IOC detection and analysis
- Risk scoring engine
- Attack behavior / MITRE ATT&CK mapping
- Incident reconstruction engine
- Explainable findings engine
- AI investigation assistant
- Incident replay
- Advanced forensic reporting
- System administration module
- Security hardening module
- Investigation notes (as a structured investigation session concept)

---

## 9. Core Architecture (Conceptual)

```
User / Investigator
↓
Authentication & RBAC              ← Existing
↓
Case Management                   ← Existing
↓
Evidence Vault                    ← Existing (Evidence Management)
↓
Evidence Integrity                ← Existing (Hash Verification)
↓
Chain of Custody                  ← Existing
↓
[Planned] Forensic Artifact Extraction
↓
[Planned] Event Normalization
↓
[Planned] Timeline Engine
↓
[Planned] Correlation Engine
↓
[Planned] Evidence Relationship Graph
↓
[Planned] Incident Reconstruction
↓
[Planned] IOC & Risk Intelligence
↓
[Planned] Attack Behavior Mapping (MITRE ATT&CK)
↓
[Planned] Explainable Findings
↓
[Planned] AI Investigation Assistant
↓
[Planned] Incident Replay
↓
[Planned] Professional Investigation Report
```

This is a conceptual architecture only. No implementation has begun. Each module will be built and tested independently.

---

## 10. Core Concepts

### 10.1 Case
An investigative container that groups related evidence, artifacts, events, and findings. Cases have a lifecycle: Open → Under Investigation → Closed → Archived. Cases are **already implemented** in the existing system.

### 10.2 Evidence
A piece of digital material registered for investigative purposes. Evidence has a file path, hashes (MD5/SHA-256), type, description, and chain of custody. Evidence is the foundational unit — it is never modified after registration. Evidence management is **already implemented**.

### 10.3 Artifact
A structured extract derived from evidence. Unlike raw evidence, an artifact represents a parsed, normalized fragment of forensic information (e.g., a parsed log entry, a file metadata record, a network connection record). **Planned / Future.**

### 10.4 Event
A normalized, timestamped occurrence derived from one or more artifacts. Events are the temporal atoms of the timeline. Each event references the entity or entities it involves. **Planned / Future.**

### 10.5 Entity
An actor or object referenced by events: a user, an IP address, a file, a process, a registry key, a domain, etc. Entities are identified and linked across events to form relationships. **Planned / Future.**

### 10.6 Relationship
A structured connection between entities, derived from shared events or explicit forensic linkage (e.g., "user X logged in from IP Y", "file Z was created by process W"). Relationships form the evidence graph. **Planned / Future.**

### 10.7 IOC (Indicator of Compromise)
A observable piece of forensic data that indicates a potential security incident. IOCs are extracted, categorized, and linked to events and evidence. **Planned / Future.**

### 10.8 Timeline Event
A normalized event placed in temporal order within an incident timeline. Timeline events are the primary mechanism for answering "when did what happen?". **Planned / Future.**

### 10.9 Incident
A reconstructed sequence of events that describes what occurred during a cyber incident. An incident is a hypothesis built from correlated evidence, validated by supporting events and relationships. **Planned / Future.**

### 10.10 Finding
A conclusion drawn from evidence and analysis. Findings are explicitly categorized as FACT, INFERENCE, HYPOTHESIS, or UNKNOWN. Findings must reference supporting evidence. **Planned / Future.**

### 10.11 Risk Score
A quantified assessment of the severity or potential impact of an event, entity, or finding. Risk scores are derived from evidence attributes and context, not invented by AI. **Planned / Future.**

### 10.12 Confidence Score
A measure of how strongly the evidence supports a finding or inference. Confidence is derived from the quantity and quality of supporting evidence, not from the AI model itself. **Planned / Future.**

### 10.13 Evidence Integrity
The assurance that evidence has not been altered since registration, verified through cryptographic hashing (MD5 + SHA-256) and chain of custody records. Evidence integrity is **already implemented**.

### 10.14 Chain of Custody
A chronological record of who handled evidence, when, and for what purpose. Chain of custody is **already implemented**.

### 10.15 Correlation
The process of linking events, artifacts, entities, and evidence based on shared attributes, temporal proximity, and known behavioral patterns. Correlation does not prove causation. **Planned / Future.**

### 10.16 Incident Reconstruction
The synthesis of correlated events, relationships, and findings into a coherent, explainable narrative of what occurred during a cyber incident. **Planned / Future.**

### 10.17 Attack Technique
A mapped attack behavior associated with an incident, ideally mapped to MITRE ATT&CK tactics and techniques. **Planned / Future.**

### 10.18 Investigation Session
A temporal workspace that tracks an investigator's active inquiry into a case. An investigation session captures questions asked, findings reviewed, and the current state of reconstruction. **Planned / Future.**

---

## 11. Module Definitions

### Module 1: Authentication & RBAC

| Field | Value |
|-------|-------|
| **Status** | ✅ Existing |
| **Purpose** | Secure user authentication and role-based access control |
| **Inputs** | Username, password, role assignments |
| **Outputs** | JWT tokens, permissions, session management |
| **Dependencies** | PBKDF2-HMAC-SHA256, python-jose, SQLite |
| **Future considerations** | MFA support, session management improvements, role hierarchy |

### Module 2: Case Management

| Field | Value |
|-------|-------|
| **Status** | ✅ Existing |
| **Purpose** | Create, edit, close, archive, and assign cases |
| **Inputs** | Case title, incident date, priority, description |
| **Outputs** | Case objects, case-user assignments |
| **Dependencies** | SQLite, users table |
| **Future considerations** | Case templates, case tagging, case relationships |

### Module 3: Evidence Management / Evidence Vault

| Field | Value |
|-------|-------|
| **Status** | ✅ Existing |
| **Purpose** | Register, view, update, and manage digital evidence |
| **Inputs** | File path, evidence type, description, case ID |
| **Outputs** | Evidence records with computed hashes |
| **Dependencies** | File system, hashing service |
| **Future considerations** | Evidence classification, tagging, bulk import, evidence repository storage |

### Module 4: Evidence Integrity & Hash Verification

| Field | Value |
|-------|-------|
| **Status** | ✅ Existing |
| **Purpose** | Verify evidence integrity via MD5/SHA-256 comparison |
| **Inputs** | Evidence file path, stored hashes |
| **Outputs** | Verification result (match/mismatch), audit event |
| **Dependencies** | Hashing service |
| **Future considerations** | Automated periodic re-verification, integrity alerting |

### Module 5: Chain of Custody

| Field | Value |
|-------|-------|
| **Status** | ✅ Existing |
| **Purpose** | Record and track custody events for each evidence item |
| **Inputs** | Action, from/to person, location, notes |
| **Outputs** | Custody event timeline |
| **Dependencies** | Users table, evidence table |
| **Future considerations** | Automated custody from evidence transfers, custody validation |

### Module 6: Audit Logging

| Field | Value |
|-------|-------|
| **Status** | ✅ Existing |
| **Purpose** | Append-only log of all system operations |
| **Inputs** | Action, entity, user, result |
| **Outputs** | Queryable audit log entries |
| **Dependencies** | SQLite |
| **Future considerations** | Tamper-evident audit logs, log export, anomaly detection in logs |

### Module 7: Forensic Artifact Extraction

| Field | Value |
|-------|-------|
| **Status** | 🔜 Planned / Future |
| **Purpose** | Extract structured forensic artifacts from registered evidence |
| **Inputs** | Evidence file, evidence type |
| **Outputs** | Structured artifacts (parsed log entries, file metadata, network records) |
| **Dependencies** | Evidence management, file parsers |
| **Success criteria** | Artifacts are structured, normalized, and traceable to source evidence |
| **Testing expectations** | Unit tests per artifact type; verify artifact-to-evidence traceability |
| **Risks** | Parser coverage, performance on large files, false positives in extraction |

### Module 8: Event Normalization

| Field | Value |
|-------|-------|
| **Status** | 🔜 Planned / Future |
| **Purpose** | Normalize artifacts into standardized temporal events |
| **Inputs** | Extracted artifacts |
| **Outputs** | Normalized events with timestamps, entities, and metadata |
| **Dependencies** | Artifact extraction engine |
| **Success criteria** | Events have consistent timestamps, entity references, and action types |
| **Testing expectations** | Verify normalization accuracy across diverse artifact formats |
| **Risks** | Ambiguous timestamps, inconsistent artifact formats, timezone handling |

### Module 9: Timeline Engine

| Field | Value |
|-------|-------|
| **Status** | 🔜 Planned / Future |
| **Purpose** | Construct and display a chronological timeline of events |
| **Inputs** | Normalized events |
| **Outputs** | Ordered timeline, temporal queries |
| **Dependencies** | Event normalization |
| **Success criteria** | Events displayed in correct temporal order with gaps identified |
| **Testing expectations** | Verify ordering, gap detection, time-range queries |
| **Risks** | Clock skew across sources, missing timestamps |

### Module 10: Evidence Correlation Engine

| Field | Value |
|-------|-------|
| **Status** | 🔜 Planned / Future |
| **Purpose** | Correlate events, entities, and evidence based on shared attributes |
| **Inputs** | Events, entities, evidence |
| **Outputs** | Correlation clusters, suspicious activity flags |
| **Dependencies** | Timeline engine, entity resolution |
| **Success criteria** | Meaningful correlations identified, false positives minimized |
| **Testing expectations** | Verify known correlation patterns, measure precision/recall |
| **Risks** | Over-correlation, under-correlation, ambiguous links |

### Module 11: Evidence Relationship Graph

| Field | Value |
|-------|-------|
| **Status** | 🔜 Planned / Future |
| **Purpose** | Build and visualize a graph of entity relationships |
| **Inputs** | Entities and relationships |
| **Outputs** | Interactive relationship graph |
| **Dependencies** | Entity identification, relationship discovery |
| **Success criteria** | Graph accurately represents entity connections |
| **Testing expectations** | Verify graph structure, edge cases (isolated nodes, cycles) |
| **Risks** | Graph layout complexity, performance with large graphs |

### Module 12: IOC Detection & Analysis

| Field | Value |
|-------|-------|
| **Status** | 🔜 Planned / Future |
| **Purpose** | Identify, categorize, and track indicators of compromise |
| **Inputs** | Events, artifacts, evidence |
| **Outputs** | IOC list with severity and evidence references |
| **Dependencies** | Artifact extraction, event normalization |
| **Success criteria** | IOCs are accurately identified and categorized |
| **Testing expectations** | Verify IOC detection against known threat patterns |
| **Risks** | IOC false positives, evolving threat patterns |

### Module 13: Risk Scoring Engine

| Field | Value |
|-------|-------|
| **Status** | 🔜 Planned / Future |
| **Purpose** | Calculate risk scores for events, entities, and findings |
| **Inputs** | Events, IOCs, evidence attributes |
| **Outputs** | Risk scores with rationale |
| **Dependencies** | IOC analysis, event correlation |
| **Success criteria** | Risk scores reflect actual threat level with explainable rationale |
| **Testing expectations** | Verify scoring consistency and rationale accuracy |
| **Risks** | Overly aggressive or lenient scoring, opaque scoring logic |

### Module 14: Attack Behavior / MITRE ATT&CK Mapping

| Field | Value |
|-------|-------|
| **Status** | 🔜 Planned / Future |
| **Purpose** | Map detected attack behavior to MITRE ATT&CK framework |
| **Inputs** | Events, IOCs, attack patterns |
| **Outputs** | ATT&CK tactic/technique mappings |
| **Dependencies** | IOC analysis, correlation engine |
| **Success criteria** | Accurate ATT&CK mapping with evidence citations |
| **Testing expectations** | Verify mapping against known attack scenarios |
| **Risks** | Mapping ambiguity, evolving ATT&CK versions |

### Module 15: Incident Reconstruction Engine

| Field | Value |
|-------|-------|
| **Status** | 🔜 Planned / Future |
| **Purpose** | Reconstruct the sequence of events during an incident |
| **Inputs** | Correlated timeline, findings, evidence |
| **Outputs** | Incident reconstruction narrative |
| **Dependencies** | Timeline engine, correlation engine, findings |
| **Success criteria** | Coherent, evidence-supported incident reconstruction |
| **Testing expectations** | Verify reconstruction against known incident scenarios |
| **Risks** | Incomplete evidence, ambiguous event ordering |

### Module 16: Explainable Findings Engine

| Field | Value |
|-------|-------|
| **Status** | 🔜 Planned / Future |
| **Purpose** | Generate findings that distinguish FACT, INFERENCE, HYPOTHESIS, UNKNOWN |
| **Inputs** | Evidence, events, correlations |
| **Outputs** | Categorized findings with evidence citations and confidence scores |
| **Dependencies** | Correlation engine, risk scoring |
| **Success criteria** | Every finding is categorized and traceable to evidence |
| **Testing expectations** | Verify finding categorization accuracy and evidence citations |
| **Risks** | Over-inference, misclassification, insufficient evidence citations |

### Module 17: AI Investigation Assistant

| Field | Value |
|-------|-------|
| **Status** | 🔜 Planned / Future |
| **Purpose** | Answer investigator questions using case evidence as context |
| **Inputs** | Natural language questions, case evidence context |
| **Outputs** | Answers with evidence citations, confidence levels, and fact/inference labels |
| **Dependencies** | Explainable findings engine, evidence corpus |
| **Success criteria** | AI answers grounded strictly in evidence, never fabricates events or IOCs |
| **Testing expectations** | Prompt injection resistance, hallucination detection, answer accuracy |
| **Risks** | AI hallucination, prompt injection, inappropriate confidence claims |

### Module 18: Incident Replay

| Field | Value |
|-------|-------|
| **Status** | 🔜 Planned / Future |
| **Purpose** | Visually step through the reconstructed incident timeline |
| **Inputs** | Incident reconstruction, timeline events |
| **Outputs** | Interactive replay of the incident sequence |
| **Dependencies** | Incident reconstruction engine, timeline engine |
| **Success criteria** | Accurate, evidence-based replay with no fictional events |
| **Testing expectations** | Verify replay accuracy against source events |
| **Risks** | Performance with large event sets, visualization complexity |

### Module 19: Investigation Notes

| Field | Value |
|-------|-------|
| **Status** | 🔜 Planned / Future |
| **Purpose** | Structured notes attached to an investigation session |
| **Inputs** | Investigator notes, tags, confidence levels |
| **Outputs** | Annotated investigation notes |
| **Dependencies** | Case management, audit logging |
| **Success criteria** | Notes are traceable, timestamped, and auditable |
| **Testing expectations** | Verify note integrity and audit trail |
| **Risks** | Note tampering, unauthorized access |

### Module 20: Report Generation

| Field | Value |
|-------|-------|
| **Status** | 🔜 Planned / Future (enhancing existing reports) |
| **Purpose** | Generate professional investigation reports |
| **Inputs** | Case data, findings, timeline, evidence |
| **Outputs** | Professional report (JSON, PDF, or other formats) |
| **Dependencies** | All evidence, timeline, and findings modules |
| **Success criteria** | Reports are comprehensive, evidence-grounded, and professionally formatted |
| **Testing expectations** | Verify report completeness, evidence citations, format correctness |
| **Risks** | Report template complexity, format rendering issues |

### Module 21: System Administration

| Field | Value |
|-------|-------|
| **Status** | 🔜 Planned / Future |
| **Purpose** | Manage users, roles, permissions, and system configuration |
| **Inputs** | Admin actions, configuration changes |
| **Outputs** | System configuration updates, audit events |
| **Dependencies** | Existing user management, RBAC |
| **Success criteria** | Secure, auditable administration |
| **Testing expectations** | Verify permission enforcement and audit coverage |
| **Risks** | Privilege escalation, configuration errors |

### Module 22: Security & Monitoring

| Field | Value |
|-------|-------|
| **Status** | 🔜 Planned / Future |
| **Purpose** | Monitor the platform itself for security issues |
| **Inputs** | System logs, access patterns |
| **Outputs** | Security alerts, monitoring data |
| **Dependencies** | Audit logging, authentication |
| **Success criteria** | Platform security is actively monitored and hardened |
| **Testing expectations** | Security scanning, penetration testing |
| **Risks** | False positives, monitoring gaps |

---

## 12. Evidence Lifecycle

```
Evidence
→ Collection          (Register evidence file, compute hashes)
→ Registration        (Create evidence record in case, initial custody event)
→ Hashing             (Compute MD5 + SHA-256, store in evidence_hashes)
→ Storage             (Original file path preserved, not copied)
→ Artifact Extraction (Planned: Parse evidence into structured artifacts)
→ Event Extraction    (Planned: Extract temporal events from artifacts)
→ Normalization       (Planned: Standardize events)
→ Correlation         (Planned: Link events, entities, evidence)
→ Timeline            (Planned: Build chronological timeline)
→ Graph               (Planned: Build relationship graph)
→ Intelligence        (Planned: IOC detection, risk scoring)
→ Reconstruction      (Planned: Synthesize into incident narrative)
→ Findings            (Planned: Categorized conclusions)
→ AI Explanation      (Planned: AI assistant answers questions)
→ Report              (Planned: Professional investigation report)
```

### What Each Stage Consumes and Produces

| Stage | Consumes | Produces |
|-------|----------|----------|
| Collection | Raw digital material | Evidence file reference |
| Registration | File path, case ID, metadata | Evidence record, custody event |
| Hashing | Evidence file | MD5, SHA-256 hashes |
| Storage | Evidence file | Stored at original path (copy not made) |
| Artifact Extraction | Evidence file, evidence type | Structured artifacts |
| Event Extraction | Artifacts | Normalized events |
| Normalization | Raw events | Standardized events with timestamps, entities |
| Correlation | Events, entities, evidence | Correlation clusters |
| Timeline | Normalized events | Chronological timeline |
| Graph | Entities, relationships | Evidence relationship graph |
| Intelligence | Events, IOCs, artifacts | Risk scores, ATT&CK mappings |
| Reconstruction | Timeline, findings | Incident narrative |
| Findings | Evidence, correlations | Categorized findings with confidence |
| AI Explanation | Findings, evidence | Investigative answers with citations |
| Report | All above | Professional investigation report |

---

## 13. Data Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Evidence     │────▶│  Artifact     │────▶│  Event        │
│  (file, hash) │     │  Extraction   │     │  Extraction   │
└──────────────┘     └──────────────┘     └──────────────┘
                                                │
                                                ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Evidence     │────▶│  Normalization│────▶│  Correlation  │
│  Integrity    │     │               │     │  Engine       │
└──────────────┘     └──────────────┘     └──────────────┘
                                                │
                                                ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Chain of     │────▶│  Timeline     │────▶│  Evidence     │
│  Custody      │     │  Engine       │     │  Relationship │
└──────────────┘     └──────────────┘     │  Graph        │
                                           └──────────────┘
                                                │
                                                ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Audit        │────▶│  Incident     │────▶│  Explainable   │
│  Logging      │     │  Reconstruction│    │  Findings      │
└──────────────┘     └──────────────┘     └──────────────┘
                                                │
                                                ▼
                                           ┌──────────────┐
                                           │  AI Assistant │
                                           │  Incident     │
                                           │  Replay       │
                                           │  Report       │
                                           └──────────────┘
```

---

## 14. Investigation Workflow

```
1. Login                    ← Existing
2. Create/select case       ← Existing
3. Register/import evidence ← Existing
4. Verify evidence integrity← Existing
5. Extract forensic artifacts ← Planned
6. Analyze artifacts        ← Planned
7. Generate events          ← Planned
8. Build timeline           ← Planned
9. Correlate evidence       ← Planned
10. Explore relationship graph ← Planned
11. Identify suspicious activities ← Planned
12. Review IOCs            ← Planned
13. Review risk score       ← Planned
14. Review attack behavior mapping ← Planned
15. Reconstruct incident    ← Planned
16. Ask AI Investigator questions ← Planned
17. Validate findings       ← Planned
18. Replay incident         ← Planned
19. Add investigator notes  ← Planned
20. Generate final report   ← Planned
21. Preserve audit trail    ← Existing + Planned
```

---

## 15. Timeline Engine (Conceptual)

### Purpose
Construct a chronological sequence of normalized events from forensic artifacts within a case.

### Inputs
- Normalized events from the Event Normalization module
- Event timestamps

### Outputs
- Ordered timeline of events
- Temporal gaps and anomalies identified

### Future Implementation Considerations
- Handle timezone conversions and clock skew
- Detect temporal gaps that may indicate missing evidence
- Support filtering by event type, entity, or severity
- Support zoom levels: day → hour → minute

### Success Criteria
- Events are displayed in correct temporal order
- Gaps are identified and flagged
- Timeline is interactive and filterable

---

## 16. Correlation Engine (Conceptual)

### Purpose
Identify relationships between events, entities, and evidence based on shared attributes and temporal proximity.

### Inputs
- Normalized events
- Entities (users, IPs, files, processes)
- Evidence records

### Outputs
- Correlation clusters
- Suspicious activity flags
- Relationship suggestions

### Future Implementation Considerations
- Define correlation rules based on forensic best practices
- Support temporal correlation (events within time windows)
- Support attribute-based correlation (shared IPs, files, users)
- Never claim causation from correlation alone

### Success Criteria
- Known correlation patterns are correctly identified
- False positive rate is acceptable for forensic investigation
- Every correlation is traceable to supporting evidence

---

## 17. Evidence Graph (Conceptual)

### Purpose
Visualize relationships between entities derived from forensic evidence.

### Inputs
- Entities identified from artifacts and events
- Relationships discovered by the correlation engine

### Outputs
- Interactive relationship graph
- Entity profiles with linked events and evidence

### Future Implementation Considerations
- Use graph database or graph library for visualization
- Support zoom, filter, and search
- Color-code by entity type (user, IP, file, process)
- Show evidence citations on each edge

### Success Criteria
- Graph accurately represents entity connections
- Investigator can trace paths between entities and evidence

---

## 18. Incident Reconstruction (Conceptual)

### Purpose
Synthesize correlated events, relationships, and findings into a coherent narrative of what occurred during a cyber incident.

### Inputs
- Correlated timeline
- Findings from the Explainable Findings Engine
- Evidence citations

### Outputs
- Incident reconstruction narrative
- Sequence of events with confidence levels

### Future Implementation Considerations
- Present reconstruction as a step-by-step narrative
- Clearly distinguish fact from inference
- Allow investigators to edit and refine the reconstruction
- Maintain version history of the reconstruction

### Success Criteria
- Reconstruction is evidence-supported
- Each step is traceable to specific evidence
- Language appropriately qualifies uncertainty

---

## 19. Risk & IOC Intelligence (Conceptual)

### Purpose
Identify indicators of compromise, calculate risk scores, and map attack behavior to known frameworks.

### Inputs
- Events and artifacts
- Evidence attributes
- Known threat patterns

### Outputs
- IOC list with severity ratings
- Risk scores with rationale
- MITRE ATT&CK tactic/technique mappings

### Future Implementation Considerations
- Define IOC categories: IP addresses, domains, file hashes, process names, registry keys
- Define risk scoring methodology based on evidence attributes
- Map to MITRE ATT&CK framework for attack behavior classification
- Ensure all IOCs and risk scores are traceable to evidence

### Success Criteria
- IOCs are accurately identified and categorized
- Risk scores reflect actual threat levels
- ATT&CK mappings are accurate and evidence-backed

---

## 20. Explainable Findings (Conceptual)

### Purpose
Generate findings that clearly distinguish between fact, inference, hypothesis, and unknown.

### The FACT / INFERENCE / HYPOTHESIS / UNKNOWN Framework

| Category | Definition | Example |
|----------|------------|---------|
| **FACT** | Verifiable from evidence | "File X was created at 10:32." |
| **INFERENCE** | Likely conclusion supported by evidence | "File X was likely downloaded before execution." |
| **HYPOTHESIS** | Possible explanation requiring more evidence | "File X may be related to the suspected intrusion." |
| **UNKNOWN** | Cannot be determined from available evidence | "The exact initial access mechanism could not be established." |

### Inputs
- Correlated events
- Evidence records
- Risk scores

### Outputs
- Findings categorized as FACT, INFERENCE, HYPOTHESIS, or UNKNOWN
- Evidence citations for each finding
- Confidence levels

### Future Implementation Considerations
- Enforce strict categorization rules
- Require evidence citations for every finding
- Never allow AI to present unsupported inferences as confirmed facts
- Maintain traceability from finding to evidence

### Success Criteria
- Every finding is properly categorized
- Every finding has evidence citations
- Confidence levels are appropriate

---

## 21. AI Investigator (Conceptual)

### Core Principles

The AI Investigator is **NOT** the source of truth. The evidence is the source of truth.

The AI should:
- Work within the selected case
- Use case evidence as context
- Explain conclusions
- Cite supporting evidence internally
- Distinguish facts from inferences
- Provide confidence levels
- Acknowledge uncertainty
- Avoid hallucinating evidence
- Never fabricate events
- Never invent IOCs
- Never claim an attack occurred without supporting evidence

### Example Investigator Questions

- "Show all activity related to invoice.exe."
- "What happened immediately before this process executed?"
- "Which evidence supports the suspected initial access?"
- "Which events have the highest risk?"
- "Show me the chain connecting this user to this external IP."
- "Why was this event marked suspicious?"

### Future Implementation Considerations
- Use the case evidence corpus as grounding context
- Implement strict prompt engineering to prevent hallucination
- Add prompt injection resistance
- Require all AI-generated content to include evidence citations
- Distinguish FACT from INFERENCE in AI responses
- Never allow AI to present conclusions without confidence levels
- Implement human-in-the-loop validation for AI findings

### Success Criteria
- AI responses are grounded strictly in evidence
- Every claim is citeable to evidence
- AI appropriately qualifies uncertainty
- No fabrication of evidence or events

---

## 22. Incident Replay (Conceptual)

### Purpose
Allow an investigator to visually step through the reconstructed incident timeline chronologically.

### Concept

An investigator selects an incident and can visually step through:

```
URL Visit → Download → File Creation → Process Execution → Network Connection → File Access → Other correlated activities
```

### Future Implementation Considerations
- Replay must be based on recorded evidence/events only
- Replay must not create fictional events
- Support play/pause/step forward/step back controls
- Show evidence citations during replay
- Highlight the temporal sequence visually
- Support speed controls and timeline scrubbing

### Success Criteria
- Replay accurately reflects source events
- No events are created during replay
- Investigator can step through at their own pace
- Evidence is cited at each step

---

## 23. Forensic Integrity

### Core Principles

- Original evidence should be preserved
- Evidence should be hashed (MD5 + SHA-256)
- Hashes should be verifiable at any time
- Chain of custody should be maintained
- Analysis should preferably operate on copies
- Every important action should be auditable
- Timestamps should be preserved
- Evidence modifications must be detectable
- Generated findings must maintain traceability to evidence

### Current Implementation
Already implemented via PBKDF2-HMAC-SHA256 hashing, hash verification, and append-only audit logging.

### Future Enhancements
- Tamper-evident hash chaining across evidence operations
- Integrity alerts on hash mismatch detection
- Automated integrity verification scheduling
- Evidence integrity dashboards

---

## 24. Security Requirements

CyberTrace Nexus is a cybersecurity application. Security is a first-class requirement.

### Current Implementation (Existing)
- ✅ PBKDF2-HMAC-SHA256 password hashing (210,000 iterations, 16-byte salt)
- ✅ JWT tokens (HS256, 7-day expiry)
- ✅ RBAC with 20+ granular permissions
- ✅ SQL injection prevention (parameterized queries)
- ✅ Foreign key enforcement
- ✅ Permission checks at service layer
- ✅ Append-only audit log
- ✅ Input validation via Pydantic schemas

### Future Security Requirements (Planned)
- 🔜 Secure file uploads (path traversal protection, file type validation, size limits)
- 🔜 Malware-safe handling considerations
- 🔜 Command execution isolation
- 🔜 API authorization enforcement
- 🔜 CSRF/XSS/SQL injection protection (layered defense)
- 🔜 Secure secrets management
- 🔜 Tamper detection for evidence and audit logs
- 🔜 Secure report generation
- 🔜 Safe AI context handling
- 🔜 Prompt injection resistance
- 🔜 Data privacy and case isolation
- 🔜 Secure error handling (no information leakage)
- 🔜 Rate limiting on authentication endpoints
- 🔜 Session management and revocation
- 🔜 Audit log integrity verification

---

## 25. Database Concept

### Do Not Modify
The database schema is not to be modified without explicit planning and review. Existing tables are the foundation.

### Existing Tables (Verified)
- `users`, `roles`, `permissions`, `role_permissions`, `user_roles`, `sessions`
- `system_settings`
- `cases`, `case_users`
- `evidence`, `evidence_hashes`
- `custody_events`
- `analysis_notes`
- `audit_logs`

### Future Conceptual Entities (Not Yet Implemented)

| Entity | Description | Relationships |
|--------|-------------|---------------|
| `artifacts` | Structured forensic artifacts extracted from evidence | FK → evidence, FK → case |
| `events` | Normalized temporal events derived from artifacts | FK → artifacts, FK → entities |
| `timeline_events` | Events ordered temporally within a case | FK → events, temporal index |
| `entities` | Identified actors/objects (users, IPs, files, processes) | Independent |
| `relationships` | Connections between entities | FK → entity (from), FK → entity (to) |
| `iocs` | Indicators of compromise | FK → evidence, FK → events |
| `findings` | Categorized conclusions | FK → case, FK → evidence |
| `risk_scores` | Quantified risk assessments | FK → events/iocs/findings |
| `attack_techniques` | MITRE ATT&CK mappings | FK → iocs, technique ID |
| `investigation_sessions` | Active investigator inquiry contexts | FK → user, FK → case |
| `ai_queries` | Logged AI assistant interactions | FK → investigation_session |
| `replay_sessions` | Incident replay states | FK → incident, FK → user |

### Entity Relationships

```
Evidence → produces artifacts
Artifacts → produce events
Events → reference entities
Entities → form relationships
Relationships + events → create timeline
Timeline + correlation → incident hypotheses
Evidence → supports findings
Findings → contribute to incident reconstruction
```

---

## 26. Frontend Concept

### Current UI (Existing)
- ✅ Login page with dark theme
- ✅ Dashboard with stats cards and activity feed
- ✅ Cases page (searchable, filterable table)
- ✅ Evidence page (table with hash display)
- ✅ Custody page (vertical timeline)
- ✅ Audit page (filterable log)
- ✅ Users page (management with role badges)
- ✅ Reports page (JSON report generation)
- ✅ shadcn-style UI components
- ✅ Responsive, accessible, dark-themed

### Future UI Areas (Planned)
- Dashboard (enhanced with intelligence views)
- Cases (existing, enhanced)
- Evidence Vault (existing, enhanced)
- Artifact Analysis (new)
- Timeline (new)
- Evidence Graph (new)
- IOC Intelligence (new)
- Incident Investigation (new)
- Incident Replay (new)
- AI Investigator (new)
- Findings (new)
- Chain of Custody (existing, enhanced)
- Audit Logs (existing, enhanced)
- Reports (enhanced with professional formatting)
- Administration (new)
- Settings (new)

### UI Design Principles
- Professional cybersecurity/SOC aesthetic
- Clarity over decoration
- Investigator workflow orientation
- Evidence traceability (every claim cites evidence)
- Visual relationships and connections
- Timeline understanding as primary navigation
- Minimal unnecessary animations
- Accessibility
- Responsive design
- Clear severity indicators (color-coded)

---

## 27. API/Backend Concept

### Current API (Existing — 38 Endpoints)

| Router | Routes | Status |
|--------|--------|--------|
| Auth | login, logout, me, refresh | ✅ Existing |
| Cases | CRUD, close, archive, assign, users/evidence | ✅ Existing |
| Evidence | CRUD, verify, hash, notes, custody | ✅ Existing |
| Custody | list, create | ✅ Existing |
| Audit | logs, count | ✅ Existing |
| Users | CRUD, disable/enable, reset password | ✅ Existing |
| Reports | generate case reports | ✅ Existing |

### Future API Additions (Planned)
- Artifact extraction endpoints
- Event normalization endpoints
- Timeline query endpoints
- Correlation endpoints
- Graph query endpoints
- IOC search endpoints
- Risk score endpoints
- Attack technique mapping endpoints
- Incident reconstruction endpoints
- AI query endpoints
- Replay session endpoints
- Finding endpoints
- Report generation (enhanced)

### Backend Architecture Principles
- Clear separation between API layer, business logic, and forensic processing
- Each module independently testable
- Existing functionality must not be broken
- Prefer incremental evolution over complete rewrites
- Reuse existing components where appropriate
- Avoid unnecessary dependencies

---

## 28. Development Principles

### Workflow
```
PLAN → IMPLEMENT → TEST → VERIFY → DOCUMENT → COMMIT
```

### Core Principles
- Do not implement multiple major modules blindly at once
- Each major module must be independently testable
- Existing functionality must not be broken while adding new functionality
- Prefer incremental evolution over complete rewrites
- Reuse existing components where appropriate
- Avoid unnecessary dependencies
- Maintain clear separation between:
  - UI
  - API
  - Business logic
  - Forensic processing
  - Correlation
  - Intelligence
  - AI
  - Reporting
  - Database

### Testing Requirements
- Minimum 80% test coverage
- Unit tests for each module
- Integration tests for API endpoints
- E2E tests for critical investigator workflows
- Tests must be written first (TDD approach)

---

## 29. Phased Roadmap

### PHASE 0: Repository Audit & Understanding
- **Objective:** Fully understand the existing codebase
- **Why:** Ensure all enhancements build on verified understanding
- **Inputs:** Existing repository
- **Outputs:** This BRAIN.md document
- **Dependencies:** None
- **Success criteria:** Complete understanding of existing architecture
- **Testing:** N/A
- **Risks:** Missing undocumented features

### PHASE 1: Existing System Stabilization
- **Objective:** Verify the existing system is stable and all tests pass
- **Why:** A stable foundation is required before adding features
- **Inputs:** Existing codebase, tests
- **Outputs:** Verified working system with passing tests
- **Dependencies:** None
- **Success criteria:** All existing tests pass
- **Testing:** Run full existing test suite
- **Risks:** Test failures requiring fixes

### PHASE 2: Evidence Intelligence Foundation
- **Objective:** Add tagging, classification, and basic intelligence to evidence
- **Why:** Evidence needs categorization before correlation can begin
- **Inputs:** Evidence records
- **Outputs:** Evidence tags, classifications, metadata enrichment
- **Dependencies:** Evidence management (existing)
- **Success criteria:** Evidence is classified and taggable
- **Testing:** Unit tests for classification, API tests for tagging
- **Risks:** Classification accuracy, metadata overhead

### PHASE 3: Artifact Extraction
- **Objective:** Extract structured forensic artifacts from evidence
- **Why:** Raw evidence must be parsed into structured data for analysis
- **Inputs:** Evidence files, evidence type
- **Outputs:** Structured artifacts
- **Dependencies:** Evidence management
- **Success criteria:** Artifacts are extracted and traceable to source evidence
- **Testing:** Unit tests per artifact type, integration tests
- **Risks:** Parser coverage, performance, false positives

### PHASE 4: Event Normalization
- **Objective:** Normalize artifacts into standardized temporal events
- **Why:** Events must be standardized for timeline construction
- **Inputs:** Artifacts
- **Outputs:** Normalized events
- **Dependencies:** Artifact extraction
- **Success criteria:** Events are consistently formatted with timestamps and entities
- **Testing:** Verify normalization accuracy across formats
- **Risks:** Ambiguous timestamps, inconsistent formats

### PHASE 5: Timeline Engine
- **Objective:** Build chronological timeline from normalized events
- **Why:** Temporal ordering is fundamental to incident reconstruction
- **Inputs:** Normalized events
- **Outputs:** Ordered timeline
- **Dependencies:** Event normalization
- **Success criteria:** Events in correct temporal order, gaps identified
- **Testing:** Verify ordering, gap detection, time-range queries
- **Risks:** Clock skew, missing timestamps

### PHASE 6: Evidence Correlation
- **Objective:** Correlate events, entities, and evidence
- **Why:** Correlation reveals patterns and connections
- **Inputs:** Events, entities, evidence
- **Outputs:** Correlation clusters, suspicious flags
- **Dependencies:** Timeline engine, entity identification
- **Success criteria:** Meaningful correlations identified
- **Testing:** Verify known patterns, measure precision/recall
- **Risks:** Over/under-correlation

### PHASE 7: Evidence Relationship Graph
- **Objective:** Build and visualize entity relationships
- **Why:** Graph visualization reveals hidden connections
- **Inputs:** Entities, relationships
- **Outputs:** Interactive relationship graph
- **Dependencies:** Correlation engine
- **Success criteria:** Graph accurately represents connections
- **Testing:** Verify graph structure
- **Risks:** Layout complexity, performance

### PHASE 8: IOC & Risk Intelligence
- **Objective:** Detect IOCs and calculate risk scores
- **Why:** Quantify threat level and identify indicators
- **Inputs:** Events, artifacts, evidence
- **Outputs:** IOC list, risk scores
- **Dependencies:** Correlation engine
- **Success criteria:** IOCs and risk scores are evidence-backed
- **Testing:** Verify detection accuracy
- **Risks:** False positives, scoring methodology

### PHASE 9: Incident Reconstruction
- **Objective:** Reconstruct incident sequence
- **Why:** Synthesize findings into a coherent narrative
- **Inputs:** Timeline, findings, evidence
- **Outputs:** Incident reconstruction
- **Dependencies:** Timeline, correlation, findings
- **Success criteria:** Coherent, evidence-supported reconstruction
- **Testing:** Verify against known scenarios
- **Risks:** Incomplete evidence, ambiguous ordering

### PHASE 10: Explainable Findings
- **Objective:** Generate FACT/INFERENCE/HYPOTHESIS/UNKNOWN findings
- **Why:** Transparency in conclusions is critical for forensic integrity
- **Inputs:** Evidence, correlations
- **Outputs:** Categorized findings with confidence and citations
- **Dependencies:** Correlation engine
- **Success criteria:** Every finding is categorized and cited
- **Testing:** Verify categorization accuracy
- **Risks:** Over-inference, misclassification

### PHASE 11: AI Investigator
- **Objective:** Add AI assistant grounded in evidence
- **Why:** Enable natural-language investigation queries
- **Inputs:** Case evidence context, natural language questions
- **Outputs:** Answers with citations and confidence levels
- **Dependencies:** Explainable findings, evidence corpus
- **Success criteria:** AI grounded strictly in evidence, no hallucination
- **Testing:** Prompt injection resistance, hallucination detection
- **Risks:** AI hallucination, prompt injection

### PHASE 12: Incident Replay
- **Objective:** Visual chronological replay of incidents
- **Why:** Step-through investigation of incident sequences
- **Inputs:** Incident reconstruction, timeline events
- **Outputs:** Interactive replay
- **Dependencies:** Incident reconstruction engine
- **Success criteria:** Accurate evidence-based replay
- **Testing:** Verify replay accuracy
- **Risks:** Performance, visualization complexity

### PHASE 13: Advanced Reporting
- **Objective:** Generate professional investigation reports
- **Why:** Produce court-ready documentation
- **Inputs:** All evidence, findings, timeline, reconstruction
- **Outputs:** Professional reports
- **Dependencies:** All modules
- **Success criteria:** Reports are comprehensive and professionally formatted
- **Testing:** Verify report completeness
- **Risks:** Template complexity, format rendering

### PHASE 14: Security Hardening
- **Objective:** Harden the platform itself for security
- **Why:** Security application must be secure
- **Inputs:** Platform code, configuration
- **Outputs:** Hardened platform
- **Dependencies:** All modules
- **Success criteria:** Security vulnerabilities addressed
- **Testing:** Security scanning, penetration testing
- **Risks:** Introducing new vulnerabilities

### PHASE 15: Testing, Documentation & Production Readiness
- **Objective:** Comprehensive testing and documentation
- **Why:** Ensure reliability and usability
- **Inputs:** Complete system
- **Outputs:** Test suite, documentation, production configuration
- **Dependencies:** All modules
- **Success criteria:** 80%+ coverage, complete documentation
- **Testing:** Full integration and E2E testing
- **Risks:** Incomplete test coverage, documentation gaps

---

## 30. Testing Strategy

### Test Requirements
- Minimum 80% test coverage
- Test Types: Unit, Integration, E2E
- Test-Driven Development (TDD) approach

### Test Structure (AAA Pattern)
```
Arrange: Set up evidence, case, and context
Act: Execute the operation being tested
Assert: Verify the result matches expectations
```

### Test Coverage by Module
| Module | Unit Tests | Integration Tests | E2E Tests |
|--------|-----------|-------------------|-----------|
| Auth & RBAC | ✅ Existing | ✅ Existing | ✅ Existing |
| Cases | ✅ Existing | ✅ Existing | Planned |
| Evidence | ✅ Existing | ✅ Existing | Planned |
| Artifact Extraction | Planned | Planned | Planned |
| Event Normalization | Planned | Planned | Planned |
| Timeline Engine | Planned | Planned | Planned |
| Correlation Engine | Planned | Planned | Planned |
| IOC & Risk | Planned | Planned | Planned |
| AI Assistant | Planned | Planned | Planned |
| Incident Replay | Planned | Planned | Planned |
| Report Generation | Planned | Planned | Planned |

### Testing Principles
- Write tests first (RED)
- Run test — it should FAIL (RED)
- Write minimal implementation (GREEN)
- Run test — it should PASS (GREEN)
- Refactor (IMPROVE)
- Verify 80%+ coverage

---

## 31. Documentation Strategy

### Documentation Requirements
- Every module must have documentation covering:
  - Purpose and responsibility
  - Inputs and outputs
  - Dependencies
  - Future implementation considerations
  - Success criteria
  - Testing expectations
  - Risks

### Documentation Locations
- `BRAIN.md` — This document (project vision, architecture, concepts)
- Module-level docstrings in source code
- API documentation (auto-generated by FastAPI/Swagger)
- README files for each major module

### Documentation Principles
- Write documentation as you implement
- Keep documentation synchronized with code
- Document decisions and their rationale
- Clearly distinguish existing from planned

---

## 32. Future Expansion

### Potential Future Directions (Not Currently Planned)
- Integration with external threat intelligence feeds
- Support for additional evidence formats (disk images, memory dumps, network captures)
- Distributed analysis across multiple machines
- Automated evidence collection agents
- Collaboration features for multi-investigator cases
- Export to standard forensic formats (AFF4, EWF)
- Chain of custody workflow automation
- Compliance reporting (NIST, ISO 27035)

### These directions are noted for future consideration only. No implementation is planned until the core roadmap is complete.

---

## 33. Project Success Criteria

The CyberTrace Nexus project will be considered successful when:

1. **Evidence-grounded:** Every finding cites supporting evidence
2. **Explainable:** Every conclusion distinguishes fact from inference from hypothesis
3. **Reconstructable:** Incidents can be reconstructed step-by-step from evidence
4. **Replayable:** Incidents can be replayed chronologically based on recorded events only
5. **Correlated:** Evidence is connected into a coherent narrative
6. **Auditable:** Every action is logged and traceable
7. **Secure:** The platform itself follows cybersecurity best practices
8. **Testable:** Each module has ≥80% test coverage
9. **Professional:** The output is suitable for forensic investigation and reporting
10. **Maintainable:** Clean architecture with clear module boundaries
11. **Portfolio-ready:** Suitable for academic demonstration and professional presentation
12. **Academic-quality:** Follows forensic best practices and NIST guidelines

---

## 34. Non-Goals

CyberTrace Nexus will NOT:

- Replace professional forensic disk imaging tools (FTK Imager, dd, etc.)
- Use hardware write blockers
- Provide legal chain-of-custody certification
- Comply with court admissibility standards (Daubert, Frye)
- Support enterprise features (LDAP, multi-tenancy) without explicit planning
- Add blockchain without a clear forensic requirement
- Add AI chatbot features without investigation-grounded purpose
- Add unnecessary microservices or cloud infrastructure
- Add random technologies without justification
- Support unauthorized access, exploitation, credential theft, persistence, malware deployment, or destructive activity
- Present AI inferences as confirmed facts
- Fabricate evidence, events, or IOCs

---

## 35. Final Vision

CyberTrace Nexus is a defensive cybersecurity and digital forensics platform designed to help investigators:

**Turn disconnected digital evidence into an explainable reconstruction of what happened during a cyber incident.**

The system preserves the secure, auditable foundation of the existing Digital Forensics Evidence Management System and extends it with:
- Evidence intelligence (artifact extraction, event normalization)
- Correlation and relationship mapping
- Timeline construction and incident replay
- Explainable findings with fact/inference/hypothesis distinction
- AI-assisted investigation grounded strictly in evidence
- Professional forensic reporting

Every feature, every line of code, and every design decision serves this central purpose. The system prioritizes investigation, detection, analysis, evidence preservation, incident understanding, and reporting.

The AI is an assistant, not the investigator. The evidence is the source of truth. The system ensures that no conclusion is presented without appropriate qualification, and every finding is traceable to supporting evidence.

---

## Appendix: Assumptions & Items Marked "To Be Verified"

### Assumptions
1. The existing system is stable and functional based on code review
2. The default admin credentials (`admin` / `Admin@123`) are for demonstration only
3. SQLite is sufficient for the initial deployment; PostgreSQL may be added later
4. The existing test suite passes (not executed during this analysis)
5. Frontend components are functional based on file structure review
6. The demo flow (`demo/demo_flow.py`) runs successfully (not executed)
7. Python 3.10+ and Node.js 18+ are available in the runtime environment
8. The `data/forensics_framework.db` file is the primary database

### To Be Verified
1. **Test execution:** The existing test suite (`tests/test_basic.py`, `tests/test_integration_rbac.py`, `tests/test_ui_rbac.py`) has not been executed to confirm all tests pass
2. **Demo execution:** The demo flow (`demo/demo_flow.py`) has not been executed
3. **Build verification:** The frontend build (`npm run build`) has not been verified (`.next` directory was removed during cleanup)
4. **Backend startup:** The backend (`python main.py`) has not been started to confirm it runs without errors
5. **Full API coverage:** While 38 endpoints were identified from code review, end-to-end API testing has not been performed
6. **Frontend page completeness:** While pages were identified from file structure, each page's full functionality has not been verified by rendering
7. **Dependencies compatibility:** The specific versions of dependencies (Next.js 16.3.3, React 19.2.8, FastAPI 0.104.1+) have not been verified for compatibility in a live environment
8. **`requirements.txt` location:** The top-level `requirements.txt` was listed but could not be read — verify it exists and is valid
9. **`legacy/` directory:** Mentioned in README as containing the deprecated Tkinter app — existence and contents not verified in this analysis
10. **`data/forensics_framework.db`:** The database file exists but was not queried to confirm schema integrity

### Files Not Modified
- No source code files were modified
- No configuration files were changed
- No database files were altered
- No test files were changed
- No documentation files (other than creating this BRAIN.md) were modified
- No frontend or backend behavior was changed

### Files Removed During Cleanup (Prior to This Task)
- `frontend/node_modules/` (445MB) — generated dependency directory
- `frontend/.next/` (317MB) — build cache directory
- All `__pycache__/` directories — Python bytecode caches

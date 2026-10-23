# System diagrams

These editable Mermaid definitions accompany the architecture and ER diagram in ARCHITECTURE.md. Render in a Mermaid-capable editor or Markdown viewer.

## Use cases

```mermaid
flowchart LR
 C[Citizen] --> Report[Submit complaint and evidence]
 C --> Track[Track case and notifications]
 C --> Confirm[Confirm resolution or reopen]
 O[Office] --> Inbox[Review assigned cases]
 O --> Act[Acknowledge investigate and resolve]
 O --> Esc[Escalate or request information]
 A[Admin] --> Configure[Manage users GIS routing and SLA]
 A --> Audit[Inspect audit records and analytics]
 Report --> System[JANASEVA]
 Act --> System
 Configure --> System
```

## Data flow level 0

```mermaid
flowchart LR
 Citizen -->|complaint location evidence| Platform[JANASEVA]
 Platform -->|case timeline and notifications| Citizen
 Platform -->|assigned work| Office
 Office -->|updates resolution evidence| Platform
 Admin -->|policies and boundary configuration| Platform
 Platform -->|analytics and audit| Admin
 Platform <--> DB[(Case and configuration database)]
 Platform <--> Store[(Evidence object store)]
```

## Data flow level 1

```mermaid
flowchart TB
 Input[Complaint text and coordinates] --> Analyze[Classification severity related reports]
 Analyze --> Locate[Point-in-polygon lookup]
 Locate --> Route[Configured responsibility lookup]
 Route --> Review{Reliable rule and adequate confidence?}
 Review -->|yes| Assign[Office assignment and SLA]
 Review -->|no| Human[Admin routing review]
 Human --> Assign
 Assign --> Work[Office actions and evidence]
 Work --> Confirm[Citizen resolution confirmation]
 Assign --> Monitor[Periodic SLA check]
 Monitor --> Escalate[Configured escalation and notification]
 Work --> Events[(Events audit and notifications)]
 Confirm --> Events
```

## Class diagram

```mermaid
classDiagram
 class Case {+public_case_id +status +priority +sla_deadline}
 class User {+email +role +office_id +session_version}
 class RoutingRule {+category_id +ward_id +office_id +verified}
 class SlaPolicy {+severity +hours +warning_hours +escalation_office_id}
 class AiPrediction {+confidence +model_id +corrected_category_id}
 class Ward {+geometry +source +verified}
 class CaseEvent {+actor_id +action +created_at +internal}
 User "1" --> "many" Case : citizen owns
 Case "1" --> "many" CaseEvent : history
 Case "1" --> "many" AiPrediction : analysis
 RoutingRule --> Ward : jurisdiction
 Case --> SlaPolicy : SLA instance
```

## Sequence diagram

```mermaid
sequenceDiagram
 actor Citizen
 participant UI as React
 participant API as FastAPI
 participant AI as Baseline and GIS
 participant DB as Database
 actor Office
 Citizen->>UI: Submit complaint and location
 UI->>API: POST /api/cases with JWT
 API->>DB: Verify identity and allocate public counter
 API->>AI: Classify score locate and relate
 AI-->>API: Assisted analysis and jurisdiction
 API->>DB: Apply route store SLA events notifications
 API-->>UI: Case ID and status
 Office->>API: Acknowledge and start
 API->>DB: Check office scope and legal transition
 Office->>API: Upload evidence and resolve
 API->>DB: Record resolution and complete SLA
 Citizen->>API: Confirm with feedback
 API->>DB: Close case and record immutable event
```

## Activity diagram

```mermaid
flowchart TB
 Start([Citizen login]) --> Form[Describe issue add location and evidence]
 Form --> Validate{Valid request?}
 Validate -->|no| Error[Show field error]
 Error --> Form
 Validate -->|yes| Create[Create case and analyze]
 Create --> Route{Trusted routing rule?}
 Route -->|no| Review[Admin review]
 Route -->|yes| Assign[Assign office and SLA]
 Review --> Assign
 Assign --> Work[Office acknowledges and starts]
 Work --> Due{Overdue?}
 Due -->|yes| Esc[Record configured escalation]
 Esc --> Work
 Due -->|no| Resolve[Upload repair evidence and resolve]
 Resolve --> Accept{Citizen confirms?}
 Accept -->|no| Reopen[Reopen with reason]
 Reopen --> Work
 Accept -->|yes| Close([Feedback and closed case])
```

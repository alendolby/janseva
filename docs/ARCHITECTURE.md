# Architecture and database design

JANASEVA is a modular monolith. React calls a REST API through Nginx. SQLAlchemy persists normalized records in PostgreSQL. PostGIS covers geometry lookup and distance candidates. Redis supports distributed rate limits and Celery scheduling. MinIO stores evidence objects. Portable local mode substitutes SQLite, Shapely point-in-polygon and local files so the same APIs can be exercised without infrastructure.

```mermaid
flowchart TB
 Browser[React citizen office admin portals] --> Nginx[Nginx frontend and API proxy]
 Nginx --> API[FastAPI modular monolith]
 API --> Auth[JWT sessions and backend permissions]
 API --> Cases[Cases events and evidence]
 Cases --> ML[TF-IDF baseline severity related reports]
 Cases --> GIS[GIS jurisdiction lookup]
 GIS --> Rules[Database routing rules]
 Rules --> SLA[SLA instances and notifications]
 API --> DB[(PostgreSQL and PostGIS)]
 Cases --> S3[(MinIO evidence objects)]
 Beat[Celery beat] --> Redis[(Redis)]
 Redis --> Worker[Celery worker]
 Worker --> SLA
 Worker --> DB
 API --> Metrics[Prometheus and Grafana]
```

## Transaction boundaries

Complaint submission allocates a public counter ID, creates the case, evaluates AI/GIS/routing, starts the SLA and writes events/notifications within one database transaction. The public counter uses atomic INSERT ON CONFLICT UPDATE RETURNING. Internal UUIDs remain separate. PostgreSQL case actions lock the case row to avoid concurrent invalid transitions. SLA rows use skip-locked background processing. Individual citizen reports remain intact when linked to an incident cluster.

Object uploads use a separate object-store transaction. If a database commit fails after storage, an orphan object may remain. A production retention/cleanup worker and malware scanner are recommended; the MVP rejects unsupported and active file formats but does not claim a complete malware scan.

## Controlled states

```mermaid
stateDiagram-v2
 [*] --> SUBMITTED
 SUBMITTED --> UNDER_AI_ANALYSIS
 UNDER_AI_ANALYSIS --> ROUTING
 ROUTING --> ASSIGNED: trusted configuration or admin review
 ASSIGNED --> ACKNOWLEDGED
 ACKNOWLEDGED --> IN_PROGRESS
 ACKNOWLEDGED --> WAITING_FOR_INFORMATION
 IN_PROGRESS --> WAITING_FOR_INFORMATION
 WAITING_FOR_INFORMATION --> IN_PROGRESS: citizen reply or office start
 IN_PROGRESS --> RESOLVED: repair evidence and note
 RESOLVED --> CLOSED: citizen confirmation and feedback
 RESOLVED --> IN_PROGRESS: citizen reopening reason
 ASSIGNED --> ESCALATED
 ACKNOWLEDGED --> ESCALATED
 IN_PROGRESS --> ESCALATED
 WAITING_FOR_INFORMATION --> ESCALATED
 ESCALATED --> IN_PROGRESS
 ESCALATED --> RESOLVED
 ASSIGNED --> REJECTED
 IN_PROGRESS --> REJECTED
```

The exhaustive transition matrix is in `backend/app/services/states.py`. Status changes generate case events and audit records. DRAFT exists in the model for future draft persistence; the citizen UI submits completed forms directly.

## Entity relationships

```mermaid
erDiagram
 users ||--|| user_roles : has
 roles ||--o{ user_roles : grants
 users ||--o| citizen_profiles : profile
 users ||--o| office_users : membership
 offices ||--o{ office_users : authorizes
 departments ||--o{ offices : groups
 districts ||--o{ local_bodies : contains
 local_bodies ||--o{ wards : contains
 local_bodies ||--o{ offices : serves
 categories ||--o{ routing_rules : classifies
 wards ||--o{ routing_rules : locates
 offices ||--o{ routing_rules : receives
 users ||--o{ cases : reports
 categories ||--o{ cases : categorizes
 offices ||--o{ cases : owns
 cases ||--|| case_locations : locates
 cases ||--o{ case_evidence : supports
 cases ||--o{ case_events : records
 cases ||--o{ case_assignments : assigns
 cases ||--o{ ai_predictions : analyzes
 model_versions ||--o{ ai_predictions : produces
 cases ||--|| severity_scores : prioritizes
 cases ||--o| incident_members : groups
 incident_clusters ||--o{ incident_members : relates
 categories ||--o{ sla_policies : configures
 sla_policies ||--o{ sla_instances : schedules
 cases ||--o| sla_instances : tracks
 cases ||--o{ escalations : escalates
 users ||--o{ notifications : receives
 cases ||--o| feedback : evaluates
 cases ||--o{ audit_logs : audits
 users ||--o{ auth_tokens : verifies
```

## Schema details

All identity/entity keys use UUID strings, with foreign keys and domain constraints. Human case IDs have a unique indexed column. The user-role relationship permits exactly one role per user. Case locations constrain coordinate ranges and use SRID 4326 Point geometry. Ward geometry uses MultiPolygon with a spatial index in PostgreSQL. Operational indexes cover citizen, office, status, category, case events, memberships and SLA deadlines. Password hashes never appear in API output. Identity and complaint evidence are separate tables.

Audit/event mutation triggers are installed by Alembic for PostgreSQL and SQLite. They protect normal database actions, while a database superuser can still bypass/drop triggers. Use a separate migration owner and a least-privilege runtime database role for a real deployment.

The initial migration carries an immutable schema snapshot. Runtime model changes must become new reviewed migrations, with downgrade validation on disposable databases.

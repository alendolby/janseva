# Quality gate and requirements traceability

This package is an implemented academic MVP, with the portable local workflow tested end to end. It is not a verified live government or production deployment.

| Requirement group | Implementation | Verification |
|---|---|---|
| Three roles and backend access scope | JWT users/roles/memberships and scoped case repository | Auth/IDOR tests passed |
| Registration/login/logout/profile/reset | FastAPI auth and account portal, demo/SMTP token adapter | Core auth and token tests passed; SMTP not sent |
| Email/mobile architecture | Email verification/reset implemented, mobile remains future | Email demo tested; no SMS service |
| Citizen report/location/evidence/tracking | Integrated report/detail/timeline screens | Browser workflow passed |
| Case IDs and normalized data | Atomic counter, UUIDs, keys/constraints/indexes | Concurrent-ID and migration tests passed |
| Office workflow and evidence | Inbox, actions, notes, request/reply, resolution/rejection | API and browser tests passed |
| Admin management | Users/roles/activation, departments/offices/categories, GIS/rules/SLA | Key API permissions and references tested |
| ML classification/version/evaluation | TF-IDF logistic regression and stored predictions | Synthetic metrics recorded |
| Explainable severity | Stored scoring explanation and factor UI | Policy checks evaluated |
| Related incident detection | Text/category/time/distance clusters retain all cases | Synthetic pair evaluation recorded |
| Human correction loop | Stored correction/reason, requires routing review | Correction test passed |
| GIS and map | Point-in-polygon, geometry import, map points/density/outlines | Portable GIS tested; PostGIS runtime not run |
| Routing | Active category/ward rules and safe review fallback | Assigned/review cases tested |
| SLA and escalation | Deadline/warning snapshots and idempotent hierarchical escalation | Local service tests passed; Celery runtime not run |
| Notification architecture | In-app event notifications and SMTP account adapter | In-app tests passed; case email optional future outbox |
| Analytics | Scoped live aggregates, map limit, trends and charts | API scope and browser checked |
| Audit/security | Immutable audit/event triggers, rate limits, upload validation | SQLite/security tests passed; Redis runtime not run |
| Infrastructure | Compose/Docker/Nginx/MinIO/Redis/Celery/monitoring | Configuration validated, engine unavailable |
| Deployability | Production overlay, bootstrap and operation guide | No remote deployment destination |
| Documentation/presentation | Setup/user/demo/methodology/report/diagrams/API/deck | Included in package |
| Real external services/data | Explicit extension interface and safe demo fixture | No real integration claimed |

## Intentional MVP boundaries

- Exactly one synthetic district fixture and six English categories.
- Uploads accept JPG, PNG and passive PDF. Video/image AI are optional future scope.
- Configured automatic escalation levels follow office parent relationships. No hierarchy is inferred.
- JWT expiry and session revocation are implemented. Browser reload signs out; refresh tokens are not implemented.
- No Aadhaar, SMS, WhatsApp, mobile verification or official government connection.
- No benchmark claiming Kerala-wide scale, external ML generalization, formal WCAG compliance or security certification.

## Before operational use

Run the Docker stack acceptance checks on your machine. Verify official boundary and responsibility provenance. Replace prototype SLA policy with approved policy. Configure least-privilege database roles, TLS, backups, retention, malware scanning, notification delivery and independent security/accessibility reviews. Conduct a privacy-approved field study with broader datasets.

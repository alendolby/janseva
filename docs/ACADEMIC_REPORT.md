# JANASEVA project report

## Abstract

JANASEVA is an academic web application that explores AI-assisted understanding and geographic routing of civic complaints. Citizens describe an issue and provide its location without identifying a department. A supervised text baseline suggests a category, an explainable scoring policy estimates priority, and spatial/configuration services propose a responsible demo office. The application records acknowledgement, investigation, evidence, resolution, feedback, SLA warnings and escalation. Three backend-enforced roles separate citizens, offices and administrators. A modular monolith integrates React, FastAPI, relational data, spatial geometry, background tasks and object storage. A synthetic one-district demonstration and automated tests support the technical evaluation. Small English datasets, unverified geographic fixtures and unavailable government integration limit generalization.

## Introduction

A citizen may describe a pothole or a broken light while lacking knowledge of the responsible office. JANASEVA investigates how a submission can move through assisted classification, geographic lookup, configuration review and an auditable resolution process. The project focuses on a complete, reproducible academic workflow rather than a state-wide operational deployment.

## Problem statement

The engineering problem is to convert complaint text and a coordinate into a tracked case with a defensible configured assignment, while protecting citizen access and recording office accountability. Uncertainty must remain visible. An absent jurisdiction or uncertain classifier output must produce review rather than an invented responsibility.

## Existing system landscape

CPGRAMS is an existing government public-grievance portal with submission and tracking facilities. Kerala also maintains a Chief Minister's public grievance mechanism. Their existence motivates interoperability and complementary research. This report does not claim either system lacks classification, routing, monitoring or analytics. An independent empirical comparison of their internal capabilities was outside this project's scope. Sources [1] and [2] describe the public systems.

## Limitations of the studied approach

The project has no authorized access to official grievance APIs, administrative responsibility data or operational resolution records. Consequently it cannot measure improvements over a government system. Its novelty is the integration and inspectable prototype workflow, not a demonstrated superiority claim.

## Proposed system

JANASEVA combines a text baseline with a separate GIS service and a database-driven routing service. A case remains visible throughout its lifecycle. Office decisions, evidence, feedback and time-based events populate live analytics. An admin can correct configuration and store human category corrections without overwriting the original prediction.

## Objectives

Provide a complete citizen-to-office resolution demonstration. Enforce case ownership and office scope on every protected API. Keep administrative responsibility in trusted configuration. Explain severity and low confidence. Retain individual reports in related-incident clusters. Record status changes and escalation. Produce reproducible model/test evidence with documented limitations.

## Scope

One synthetic district, one local body, one ward fixture, six complaint categories and exactly three primary roles. Web browsers support desktop and mobile layouts. JPEG, PNG and passive PDF evidence are accepted. No real citizen identity, Aadhaar, Malayalam model, video inference or official API connection is included.

## Literature review

Pedregosa et al. [3] describe scikit-learn as a library for supervised and unsupervised learning. It supports a compact reproducible classifier without unnecessary deep-learning infrastructure. Manning, Raghavan and Schütze [4] describe TF-IDF/vector-space similarity, providing the basis for sparse text features and cosine matching. PostGIS documentation [5] defines spatial coverage and distance functions, enabling geography to remain distinct from office responsibility. FastAPI security documentation [6] provides an authentication implementation reference. These sources support technical choices; they do not validate the civic outcomes of this prototype.

## Research gap

This project explores the practical integration of assisted complaint interpretation, configurable spatial responsibility, time-based accountability and citizen confirmation in a controlled synthetic environment. A future study must use authorized datasets, independent annotations and a baseline comparison before claiming improved routing or resolution outcomes.

## Methodology

Requirements were translated into role-specific routes, normalized tables and service modules. Authentication and scope queries formed the foundation. Complaint creation integrated supervised classification, severity rules, similarity candidates, geography, routing and SLA creation. Office actions enforce legal transitions and mandatory evidence for resolution. Automated tests check permissions, negative inputs, transitions, notifications, audit mutation protection and concurrent IDs. A browser test drives the complete case workflow. Model evaluation remains separate from application functional testing.

## System architecture

React/TypeScript runs behind Nginx and consumes FastAPI REST APIs. SQLAlchemy and Alembic define/version the schema. PostgreSQL/PostGIS provide production-shaped persistence and spatial lookup. Redis/Celery schedule SLA checks. MinIO stores evidence. SQLite/Shapely/local-file mode supports portable testing through the same APIs. See ARCHITECTURE.md and DIAGRAMS.md for architecture, DFD, ER, class, sequence, activity and use case diagrams.

## Database design

Identity is separate from complaint records. Role membership permits exactly one primary role. Offices, departments, districts, local bodies, wards, categories, routing rules and SLA policies are normalized. Cases use internal UUIDs and independent public counters. Evidence metadata references object keys. Model versions and predictions retain provenance. Events/audit records have immutable mutation guards. SLA instances retain operational deadlines, and feedback links to a citizen-owned resolved case.

## UI and accessibility

The interface uses a restrained green/neutral design, consistent fields, readable badges, explicit errors and responsive layout. Citizens report and track cases. Office staff use the inbox, permitted maps, evidence and actions. Administrators configure resources and inspect metrics. Form labels, keyboard focus, status alerts and responsive navigation support accessibility. Automated browser checks cover a mobile viewport; formal WCAG conformance and assistive-technology testing remain future evaluation.

## AI and dataset methodology

A 108-row synthetic English corpus splits into 84 training and 24 test examples across six categories. TF-IDF unigrams/bigrams feed logistic regression. The artifact and dataset have explicit versions. The classifier stores prediction/confidence with each case and requests review below 0.4. Held-out evaluation reports accuracy, macro metrics and a confusion matrix. Test rows are distinct, though synthetic wording and domain overlap limit independence. There is no public citizen dataset or visual classifier in this MVP.

## Severity methodology

An explainable text policy counts reported damage, safety terms, sensitive locations, related reports and traffic terms. This is an initial prototype policy. Visual analysis and historical incident inference are absent. Per-factor contributions are shown in the UI. Policy consistency testing does not imply a validated risk model.

## Duplicate methodology

A 30-day, same-category candidate window and 150-metre limit combine with sparse cosine similarity. Individual reports remain separate and link through incident_members. The score is explicitly heuristic. A small pair test showed low recall, which justifies advisory presentation and human review rather than automatic report suppression.

## GIS methodology

PostGIS ST_Covers identifies a ward from a point, with local-body/district relationships derived from normalized data. Coordinates use longitude/latitude order for SRID 4326. The boundary seed is a synthetic rectangle. Verified provenance controls eligibility outside demo mode. Overlap/absence of eligible geometry yields review. Import validation rejects nonpolygon or invalid geometry.

## Routing methodology

The service maps category and ward through active trusted routing rules. ML does not assign administrative responsibility independently. An administrator can make a reasoned assignment when configuration is missing or uncertain. Official boundary/responsibility sources must be obtained before real administrative use.

## SLA methodology

Each assignment establishes a deadline/warning period from category/severity configuration. Celery evaluates active instances every minute. Warnings notify users, overdue checks record an idempotent escalation, and resolution completes the SLA. Prototype policies are illustrative. Continued breaches advance through configured parent offices after another SLA duration. Missing parents end automatic advancement.

## Security and privacy

Argon2 password hashing, expiring JWTs, session-version revocation, role dependencies and scoped queries protect access. Uploads validate content and size. Filenames do not become storage paths. CORS, headers and rate limits add protection. Audit/event triggers reject normal mutation. Synthetic users avoid unnecessary sensitive identity. Security tests cover cross-citizen and unrelated-office access, citizen admin attempts, file spoofing, invalid transitions and revoked sessions. Production validation and independent penetration testing remain necessary.

## Testing and results

24 backend tests passed, including concurrent case-ID generation, authorization, upload validation, state transitions, information reply, reopening, feedback, SLA warning/escalation, admin reassignment, corrections and audit immutability. Seven frontend tests passed. Two browser tests passed, one covering the complete workflow and one mobile layout/form validation. The production bundle compiled and Compose files parsed. TEST_REPORT.md records the precise tested environment and outstanding infrastructure acceptance checks.

## Model performance

On 24 synthetic test examples, classification accuracy was 95.83%, macro precision 96.67%, recall 95.83% and F1 95.77%. Duplicate positive precision was 1.0, recall 0.4 and F1 0.5714 on eight synthetic pairs. Severity policy MAE was 2.5 on four manually specified policy cases. Inference timing and low-confidence rate are recorded in evaluation JSON. These are small local measurements with no claim of operational generalization.

## Performance engineering

API case lists paginate and cap page size at 100. Dashboard maps cap latest locations at 100. Related-report comparisons cap candidates at 500. Relational/spatial indexes support scope, deadlines and geometry. Model loading is cached in-process, while the map is loaded lazily with a separately bundled worker. SQL aggregates produce live metrics. No large-scale load test or field deployment result is claimed.

## Limitations

Official geography/responsibility and external integration are unavailable. Classification is small-data English only. Severity is textual policy, and duplicate recall is weak. Escalation advances only through the administrator-configured office hierarchy. JWT refresh/mobile verification, virus scanning, object cleanup, retention and formal accessibility testing are incomplete operational capabilities. Docker services are configured but were not run on this build host. Existing government-system improvement cannot be inferred from the test results.

## Future scope

Authorized administrative datasets, multilingual/voice reporting, evaluated embeddings, calibrated confidence, image analysis, human-reviewed cluster operations, multilevel escalation policies, notification outbox/email/SMS adapters, field performance testing, interoperable official APIs and mobile applications can extend the prototype. Each integration requires appropriate authorization, privacy design and outcome evaluation.

## Conclusion

JANASEVA demonstrates an integrated, tested academic grievance workflow with backend permissions, inspectable AI assistance, geographic routing configuration, office evidence, citizen feedback and audit records. The source and tests make the prototype reproducible. Operational deployment requires official data, infrastructure acceptance, security review and broader evaluation.

## References

[1] Government of India, CPGRAMS public portal. https://pgportal.gov.in/ Accessed 8 October 2026.

[2] Government of Kerala, Chief Minister's public grievance portal. https://complaints.cmo.kerala.gov.in/cmoportal/login.htm?lang=en Accessed 8 October 2026.

[3] Pedregosa, F., et al. Scikit-learn: Machine Learning in Python. Journal of Machine Learning Research, 12(85), 2825–2830, 2011. https://www.jmlr.org/papers/v12/pedregosa11a.html

[4] Manning, C. D., Raghavan, P., and Schütze, H. Introduction to Information Retrieval. Cambridge University Press, 2008. https://nlp.stanford.edu/IR-book/html/htmledition/irbook.html

[5] PostGIS project. Spatial coverage and distance reference. https://postgis.net/docs/reference.html Accessed 8 October 2026.

[6] FastAPI project. OAuth2 with Password and Bearer JWT tokens. https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/ Accessed 8 October 2026.

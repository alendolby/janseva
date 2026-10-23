# Implementation phase guide

Run root commands from the extracted project folder. Commands prefixed by `cd backend` or `cd frontend` belong to that directory with the Python environment activated or Node installed. A semicolon here separates directory selection from the next command; Windows PowerShell supports it. Source files contain the complete implementation, so the guide references their locations instead of repeating code.

## Phase 0 Requirements

Objective: Match one-district scope and honest prototype data. Implementation: `README.md and QUALITY_GATE.md`. Verification/checkpoint: `Read docs/QUALITY_GATE.md`. Expected behavior and troubleshooting are in SETUP_WINDOWS.md, SETUP_LOCAL.md and DEMO.md. The test report distinguishes executed checks from infrastructure checks awaiting Docker.

## Phase 1 Project setup

Objective: Generate secrets without committing them. Implementation: `scripts/configure.py and environment examples`. Verification/checkpoint: `python scripts/configure.py`. Expected behavior and troubleshooting are in SETUP_WINDOWS.md, SETUP_LOCAL.md and DEMO.md. The test report distinguishes executed checks from infrastructure checks awaiting Docker.

## Phase 2 Repository

Objective: Keep domain and UI responsibilities separate. Implementation: `frontend/src and backend/app modules`. Verification/checkpoint: `Read docs/FILE_MANIFEST.txt`. Expected behavior and troubleshooting are in SETUP_WINDOWS.md, SETUP_LOCAL.md and DEMO.md. The test report distinguishes executed checks from infrastructure checks awaiting Docker.

## Phase 3 Docker

Objective: Provide supporting infrastructure. Implementation: `docker-compose.yml and Dockerfiles`. Verification/checkpoint: `docker compose config --quiet`. Expected behavior and troubleshooting are in SETUP_WINDOWS.md, SETUP_LOCAL.md and DEMO.md. The test report distinguishes executed checks from infrastructure checks awaiting Docker.

## Phase 4 Database

Objective: Establish relational and spatial integrity. Implementation: `models and frozen Alembic migration`. Verification/checkpoint: `cd backend; alembic upgrade head`. Expected behavior and troubleshooting are in SETUP_WINDOWS.md, SETUP_LOCAL.md and DEMO.md. The test report distinguishes executed checks from infrastructure checks awaiting Docker.

## Phase 5 Authentication

Objective: Hash passwords and manage expiring sessions. Implementation: `api/auth.py and core/security.py`. Verification/checkpoint: `cd backend; pytest tests/test_auth_admin_ml.py`. Expected behavior and troubleshooting are in SETUP_WINDOWS.md, SETUP_LOCAL.md and DEMO.md. The test report distinguishes executed checks from infrastructure checks awaiting Docker.

## Phase 6 RBAC

Objective: Protect case ownership and office permissions. Implementation: `core/security.py and repositories/cases.py`. Verification/checkpoint: `cd backend; pytest -k idor`. Expected behavior and troubleshooting are in SETUP_WINDOWS.md, SETUP_LOCAL.md and DEMO.md. The test report distinguishes executed checks from infrastructure checks awaiting Docker.

## Phase 7 Citizen portal

Objective: Submit and track a real case. Implementation: `features/cases/Report.tsx and account`. Verification/checkpoint: `Open /citizen/report after login`. Expected behavior and troubleshooting are in SETUP_WINDOWS.md, SETUP_LOCAL.md and DEMO.md. The test report distinguishes executed checks from infrastructure checks awaiting Docker.

## Phase 8 Complaints

Objective: Allocate IDs and enforce transitions. Implementation: `services/complaints.py and states.py`. Verification/checkpoint: `cd backend; pytest -k status`. Expected behavior and troubleshooting are in SETUP_WINDOWS.md, SETUP_LOCAL.md and DEMO.md. The test report distinguishes executed checks from infrastructure checks awaiting Docker.

## Phase 9 Evidence

Objective: Store safe private evidence objects. Implementation: `services/storage.py and typed API routes`. Verification/checkpoint: `cd backend; pytest -k evidence`. Expected behavior and troubleshooting are in SETUP_WINDOWS.md, SETUP_LOCAL.md and DEMO.md. The test report distinguishes executed checks from infrastructure checks awaiting Docker.

## Phase 10 Office portal

Objective: Acknowledge investigate resolve with evidence. Implementation: `case inbox/detail and actions`. Verification/checkpoint: `Read docs/DEMO.md`. Expected behavior and troubleshooting are in SETUP_WINDOWS.md, SETUP_LOCAL.md and DEMO.md. The test report distinguishes executed checks from infrastructure checks awaiting Docker.

## Phase 11 Admin portal

Objective: Manage configurations with audit records. Implementation: `features/admin and api/system.py`. Verification/checkpoint: `Sign in as generated demo admin`. Expected behavior and troubleshooting are in SETUP_WINDOWS.md, SETUP_LOCAL.md and DEMO.md. The test report distinguishes executed checks from infrastructure checks awaiting Docker.

## Phase 12 GIS

Objective: Identify jurisdiction separately from responsibility. Implementation: `gis/jurisdiction.py and boundary import`. Verification/checkpoint: `cd backend; pytest -k gis`. Expected behavior and troubleshooting are in SETUP_WINDOWS.md, SETUP_LOCAL.md and DEMO.md. The test report distinguishes executed checks from infrastructure checks awaiting Docker.

## Phase 13 Routing

Objective: Assign only from configured trustworthy rules. Implementation: `routing/engine.py and routing_rules`. Verification/checkpoint: `cd backend; pytest -k review`. Expected behavior and troubleshooting are in SETUP_WINDOWS.md, SETUP_LOCAL.md and DEMO.md. The test report distinguishes executed checks from infrastructure checks awaiting Docker.

## Phase 14 Classification

Objective: Learn categories with a measured baseline. Implementation: `ml/baseline.py and synthetic corpus`. Verification/checkpoint: `python ml/training/train.py from root`. Expected behavior and troubleshooting are in SETUP_WINDOWS.md, SETUP_LOCAL.md and DEMO.md. The test report distinguishes executed checks from infrastructure checks awaiting Docker.

## Phase 15 Severity

Objective: Explain every policy factor. Implementation: `ml/severity.py and severity_scores`. Verification/checkpoint: `Read AI_GIS_METHODOLOGY.md`. Expected behavior and troubleshooting are in SETUP_WINDOWS.md, SETUP_LOCAL.md and DEMO.md. The test report distinguishes executed checks from infrastructure checks awaiting Docker.

## Phase 16 Related reports

Objective: Retain individual reports while grouping. Implementation: `ml/duplicates.py and incident membership`. Verification/checkpoint: `cd backend; python ../ml/evaluation/evaluate_auxiliary.py`. Expected behavior and troubleshooting are in SETUP_WINDOWS.md, SETUP_LOCAL.md and DEMO.md. The test report distinguishes executed checks from infrastructure checks awaiting Docker.

## Phase 17 SLA

Objective: Create deadline/warning snapshots. Implementation: `services/sla.py and SLA policies`. Verification/checkpoint: `cd backend; pytest -k sla`. Expected behavior and troubleshooting are in SETUP_WINDOWS.md, SETUP_LOCAL.md and DEMO.md. The test report distinguishes executed checks from infrastructure checks awaiting Docker.

## Phase 18 Escalation

Objective: Record deadline breach without inventing hierarchy. Implementation: `escalation records and configured authority`. Verification/checkpoint: `cd backend; pytest -k escalation`. Expected behavior and troubleshooting are in SETUP_WINDOWS.md, SETUP_LOCAL.md and DEMO.md. The test report distinguishes executed checks from infrastructure checks awaiting Docker.

## Phase 19 Notifications

Objective: Connect events to in-app updates. Implementation: `services/notifications.py and portal`. Verification/checkpoint: `Open portal Notifications`. Expected behavior and troubleshooting are in SETUP_WINDOWS.md, SETUP_LOCAL.md and DEMO.md. The test report distinguishes executed checks from infrastructure checks awaiting Docker.

## Phase 20 Analytics

Objective: Calculate only from permitted real case records. Implementation: `SQL aggregate API and charts/maps`. Verification/checkpoint: `cd backend; pytest -k analytics`. Expected behavior and troubleshooting are in SETUP_WINDOWS.md, SETUP_LOCAL.md and DEMO.md. The test report distinguishes executed checks from infrastructure checks awaiting Docker.

## Phase 21 Security

Objective: Check negative actions and data privacy. Implementation: `middleware, scope, validation, audit triggers`. Verification/checkpoint: `cd backend; pytest -k "idor or immutable or rate"`. Expected behavior and troubleshooting are in SETUP_WINDOWS.md, SETUP_LOCAL.md and DEMO.md. The test report distinguishes executed checks from infrastructure checks awaiting Docker.

## Phase 22 Testing

Objective: Verify complete workflow and failures. Implementation: `backend/tests, frontend/src/test, e2e`. Verification/checkpoint: `Run commands in TEST_REPORT.md and README`. Expected behavior and troubleshooting are in SETUP_WINDOWS.md, SETUP_LOCAL.md and DEMO.md. The test report distinguishes executed checks from infrastructure checks awaiting Docker.

## Phase 23 Performance

Objective: Bound case/map/duplicate work. Implementation: `indexes, pagination, lazy map, model cache`. Verification/checkpoint: `cd frontend; npm run build`. Expected behavior and troubleshooting are in SETUP_WINDOWS.md, SETUP_LOCAL.md and DEMO.md. The test report distinguishes executed checks from infrastructure checks awaiting Docker.

## Phase 24 Production Docker

Objective: Separate demo and deployment configuration. Implementation: `docker-compose.production.yml`. Verification/checkpoint: `docker compose -f docker-compose.yml -f docker-compose.production.yml config --quiet`. Expected behavior and troubleshooting are in SETUP_WINDOWS.md, SETUP_LOCAL.md and DEMO.md. The test report distinguishes executed checks from infrastructure checks awaiting Docker.

## Phase 25 Deployment

Objective: Provide hosting instructions and acceptance checks. Implementation: `DEPLOYMENT.md and admin bootstrap`. Verification/checkpoint: `Run on your Docker host; no remote destination supplied`. Expected behavior and troubleshooting are in SETUP_WINDOWS.md, SETUP_LOCAL.md and DEMO.md. The test report distinguishes executed checks from infrastructure checks awaiting Docker.

## Phase 26 UI polish

Objective: Provide consistent usable role portals. Implementation: `shared components and responsive styles`. Verification/checkpoint: `cd frontend; npm run test:e2e`. Expected behavior and troubleshooting are in SETUP_WINDOWS.md, SETUP_LOCAL.md and DEMO.md. The test report distinguishes executed checks from infrastructure checks awaiting Docker.

## Phase 27 Documentation

Objective: Make architecture and results reproducible. Implementation: `docs report diagrams API and guides`. Verification/checkpoint: `Read docs/ACADEMIC_REPORT.md`. Expected behavior and troubleshooting are in SETUP_WINDOWS.md, SETUP_LOCAL.md and DEMO.md. The test report distinguishes executed checks from infrastructure checks awaiting Docker.

## Phase 28 Presentation and demo

Objective: Explain and demonstrate the integrated prototype. Implementation: `presentation.pptx and DEMO.md`. Verification/checkpoint: `Open the deck and follow DEMO.md`. Expected behavior and troubleshooting are in SETUP_WINDOWS.md, SETUP_LOCAL.md and DEMO.md. The test report distinguishes executed checks from infrastructure checks awaiting Docker.

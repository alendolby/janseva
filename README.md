# JANASEVA

AI-Powered Citizen Grievance Routing and Accountability Platform

A runnable academic prototype with three backend-enforced roles, six complaint categories, one synthetic district fixture, and a tested complaint-to-resolution workflow. JANASEVA explores a complementary orchestration layer. It has no official government integration and does not replace CPGRAMS or Kerala CMO grievance mechanisms.

## Start here

1. Read `docs/SETUP_WINDOWS.md` or `docs/SETUP_LOCAL.md`.
2. Generate environment files using `python scripts/configure.py` from this folder.
3. Start the full stack with `docker compose up -d --build`.
4. Open http://localhost:8080. Read the locally generated `DEMO_ACCOUNTS.txt` for synthetic login accounts and the generated password.
5. Follow `docs/DEMO.md` for the complete demonstration.

The ZIP contains source code, dependency locks, a trained baseline artifact, reproducible training data, evaluation results, tests, a prebuilt frontend, API documentation, diagrams, deployment configuration, and a 26-slide editable PowerPoint. It excludes installed dependencies, databases, uploaded evidence, and environment secrets.

## Structure

```text
frontend/             React TypeScript Vite Tailwind application
  src/api/            Authenticated HTTP client
  src/components/     Accessible shared UI and MapLibre integration
  src/features/       Auth, complaints, dashboards, account, administration
  src/layouts/        Role-specific portal navigation
  src/routes/         Client navigation guards
  src/test/           Component and validation tests
  e2e/                Playwright citizen-office-admin workflow
  dist/               Prebuilt frontend bundle, served through the backend proxy
backend/
  app/api/            Typed FastAPI routes
  app/core/           Configuration, sessions, rate limits and database
  app/models/         Normalized SQLAlchemy schema
  app/schemas/        Input and output contracts
  app/repositories/   Ownership and office-scope queries
  app/services/       Complaints, audit, evidence, notifications, SLA and states
  app/gis/            PostGIS jurisdiction lookup and portable test adapter
  app/routing/        Database-driven responsibility rules
  app/ml/             Baseline inference, explainable severity and related reports
  app/tasks/          Celery periodic SLA job
  migrations/         Alembic migration with frozen initial schema
  tests/              Backend API, integration and security checks
ml/                   Dataset, training, evaluation and trusted model artifacts
gis/                  Boundary provenance and import utility
docker/               Dockerfiles, Nginx, Prometheus and Grafana provisioning
docs/                 Setup, methodology, user guide, academic report and presentation
scripts/              Secret generation and isolated E2E server
```

## Verification performed

24 backend tests and 7 frontend tests passed. Both browser tests passed, including the full case workflow and a mobile public page/form check. The production frontend compiled. Both development and production Compose configurations validated. Detailed evidence is in `docs/TEST_REPORT.md`.

Docker runtime execution, PostGIS queries against a live PostgreSQL server, Redis, Celery, MinIO and monitoring containers could not be exercised on the build host because its Docker engine was unavailable. These services have integrated code and configuration, but their runtime acceptance checks remain explicit. See `docs/QUALITY_GATE.md`.

## Prototype boundaries

The classifier is TF-IDF plus logistic regression trained on 84 authored English examples and evaluated on 24 synthetic held-out examples. The duplicate engine is a heuristic similarity score, not a calibrated probability. Severity follows an explainable text policy. Synthetic geographic rectangles and responsibility rules are labeled DEMO. Production mode ignores unverified boundaries/rules.

Image AI, video, Malayalam, Aadhaar, SMS, WhatsApp and official grievance-system adapters are outside this MVP. Email verification/reset supports opt-in SMTP and a labeled local demo token flow. In-app case notifications are implemented; case-event email delivery is an optional adapter, not enabled in the MVP. Access tokens are kept in browser memory and expire after 30 minutes. Reloading requires sign-in.

## Developer commands

Run backend commands from `backend/` after activating Python 3.12 environment:

```text
pip install -r requirements.lock
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
pytest --cov=app
```

Run frontend commands from `frontend/` with Node 22.12+ or Node 24:

```text
npm ci
npm run dev
npm run build
npm test
npx playwright install chromium
npm run test:e2e
```

The E2E runner starts an isolated synthetic backend using `python`. Set `JNS_PYTHON` to your environment's Python executable if it is not on PATH. Local frontend uses port 5173 and proxies to backend port 8000. Docker uses port 8080. API documentation is at `/docs`; an exported API schema is in `docs/openapi.json`.

## Maintenance

Use `alembic revision --autogenerate -m "description"`, inspect the migration, then `alembic upgrade head`. Never edit the frozen initial schema after release. Admin users configure categories, organizations, GIS, routing rules and SLA policies through the portal. Database audit/event triggers reject update/delete. Production operations and limitations are documented in `docs/DEPLOYMENT.md`.

# Deployment and operations

## Demo infrastructure

From the repository root:

```text
python scripts/configure.py
docker compose config --quiet
docker compose up -d --build
docker compose ps
docker compose exec backend alembic current
docker compose exec backend python -m app.verify_infrastructure
docker compose logs --tail=100 backend worker beat
```

Dependencies start using health conditions. Backend migrates and seeds before it becomes healthy. Storage-init creates a private MinIO bucket. Celery worker and beat start after the API is healthy. Application port is bound to loopback:8080; MinIO console uses loopback:9001. PostgreSQL, Redis, MinIO object API and backend ports remain internal. The PostGIS image is configured amd64 for compatibility with the selected image and may use emulation on ARM.

## Production image build and deployment starting point

```text
docker compose build
docker compose -f docker-compose.yml -f docker-compose.production.yml config --quiet
docker compose -f docker-compose.yml -f docker-compose.production.yml up -d
```

Use a new environment and fresh database rather than a seeded demo volume. Set DEMO_MODE=false, generate fresh secrets, configure HTTPS reverse proxy, exact CORS origins, backups, retention, SMTP if needed, and separate migration/runtime database identities. Configure a strong monitoring password before enabling monitoring. The production overlay turns demo mode off and removes MinIO console publication.

Initialize the first administrator on an empty production user table using environment variables:

```powershell
$env:ADMIN_EMAIL = "your-authorized-admin@example.org"
$env:ADMIN_PASSWORD = Read-Host "Administrator password"
docker compose exec -e ADMIN_EMAIL=$env:ADMIN_EMAIL -e ADMIN_PASSWORD=$env:ADMIN_PASSWORD backend python -m app.bootstrap
Remove-Item Env:ADMIN_PASSWORD
```

Run from project root. Then configure categories, organizations, source-verified GIS polygons, verified routing rules and SLA policies in the admin portal. A real deployment must obtain official authorization/data before presenting configuration as government responsibility. Existing seeded databases remain synthetic even when demo mode is switched off.

## Migrations

From backend with environment configured:

```text
alembic current
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

Review generated changes, test against disposable PostgreSQL, back up production, then apply migrations with a migration owner. Do not modify the frozen 0001 migration. PostgreSQL extension installation requires an authorized privileged database connection during initial migration.

## Monitoring

Set GRAFANA_ADMIN_PASSWORD in `.env`, then:

```text
docker compose --profile monitoring up -d
```

Grafana localhost:3000 receives a provisioned Prometheus datasource and HTTP request/latency dashboard. Metrics do not carry case descriptions or citizen identities. Redis and evidence volumes persist. Maintain only one Celery beat scheduler. SLA task uses locked rows and active escalation checks to reduce duplicate events.

## Backups and recovery

Back up PostgreSQL with your authorized database tooling and separately back up/version the private object bucket. Restoring only one loses relational/object consistency. Verify a restore into a disposable environment and rotate session secrets after a security incident. Never publish `.env`, account-password files, citizen uploads or database dumps in the source ZIP.

## Acceptance still required

The build host lacked a running Docker engine. Compose syntax was checked, but images, startup order, live PostGIS, Redis rate limits, Celery delivery, MinIO integration, Nginx and Grafana require runtime checks on your Docker host. No remote hosting was performed because no deployment destination was supplied. SMTP code needs credentials and a controlled delivery test before use.

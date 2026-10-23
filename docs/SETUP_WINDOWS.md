# Windows setup

Run commands in PowerShell from the extracted `janaseva` project folder. Use Windows 11 with Docker Desktop, Python 3.12 and Node 22.12+ or Node 24. Installers and package availability may vary by organization.

## Environment inspection

```powershell
.\scripts\check-environment.ps1
```

Docker provides containers for PostGIS, Redis, MinIO and the application. Python generates secrets and supports local development. Node builds the React application. Git manages source history.

If missing, download Docker Desktop from https://docs.docker.com/desktop/setup/install/windows-install/, Python 3.12 from https://www.python.org/downloads/, Node 24 from https://nodejs.org/en/download and Git from https://git-scm.com/download/win. Start Docker Desktop and enable its WSL2 backend. Verify `docker info` succeeds before continuing. `docker --version` alone does not verify the engine.

## Recommended full-stack launch

From the project root:

```powershell
py -3.12 scripts/configure.py
docker compose config --quiet
docker compose up -d --build
docker compose ps
docker compose logs --tail=100 backend
Invoke-RestMethod http://localhost:8080/api/health
Get-Content DEMO_ACCOUNTS.txt
Start-Process http://localhost:8080
```

Expected: backend health returns `status: ok`, frontend is reachable, demo accounts exist. Initial package/image downloads require internet access. First start migrates the database, trains the baseline and seeds synthetic data. Later starts preserve the volume contents.

To stop without deleting data:

```powershell
docker compose down
```

Do not add `-v` unless you intentionally want to delete local volumes.

## Local application development

From root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.lock
Set-Location backend
alembic upgrade head
python -m app.seed
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

In another terminal, from root:

```powershell
Set-Location frontend
npm ci
npm run dev
```

Open http://localhost:5173. The generated `backend/.env` uses SQLite and local evidence storage for portable development. PostGIS mode is provided by Compose and has a distinct connection URL.

## Test commands

From root with Python environment activated:

```powershell
Set-Location backend
pytest --cov=app
Set-Location ../frontend
npm test
npm run build
npx playwright install chromium
$env:JNS_PYTHON = (Resolve-Path ../.venv/Scripts/python.exe).Path
npm run test:e2e
```

## Common problems

- `py` is missing: repair Python installation and enable its launcher.
- Activation blocked: use `.venv\Scripts\python.exe` directly, or your organization's permitted PowerShell execution policy.
- Docker cannot connect: start Docker Desktop and verify its WSL2 setup.
- Port 8080 is busy: change the frontend host-port mapping in Compose, then update CORS origins.
- Compose demands secrets: run `scripts/configure.py`. Preserve an existing `.env` rather than overwriting credentials used by persistent volumes.
- Invalid demo login: use the generated password in `DEMO_ACCOUNTS.txt`, not a password shown in test source. Existing seeded volumes retain their original account password.
- JWT configuration error: use the generated `.env` file and run backend commands from `backend/`.
- No assignment: choose the synthetic location 9.965, 76.30 and a recognizable complaint. Low confidence or an unknown jurisdiction correctly enters routing review.
- Resolution blocked: acknowledge, start work, upload RESOLUTION evidence, then supply a resolution note.
- E2E port conflict: stop other servers using 8000 and 5173. The test runner starts fresh servers.

# macOS and Linux setup

From the project root, use Python 3.12 and Node 24 (or Node 22.12+):

```sh
python3.12 scripts/configure.py
python3.12 -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.lock
cd backend
alembic upgrade head
python -m app.seed
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

In another terminal from the project root:

```sh
cd frontend
npm ci
npm run dev
```

Open http://localhost:5173. Read `DEMO_ACCOUNTS.txt` for your generated password.

For the integrated infrastructure, install/start Docker and run from root:

```sh
docker info
docker compose config --quiet
docker compose up -d --build
docker compose ps
curl http://localhost:8080/api/health
```

Run tests from the project root:

```sh
. .venv/bin/activate
cd backend
pytest --cov=app
cd ../frontend
npm test
npm run build
npx playwright install chromium
JNS_PYTHON="$(pwd)/../.venv/bin/python" npm run test:e2e
```

Train/evaluate from root:

```sh
. .venv/bin/activate
python ml/training/train.py
# Auxiliary evaluation imports database-backed duplicate utilities and requires configuration.
cd backend
python ../ml/evaluation/evaluate_auxiliary.py
```

Docker commands from root:

```sh
docker compose exec backend alembic current
docker compose exec backend pytest
docker compose logs --tail=100 backend worker beat
docker compose --profile monitoring up -d
```

Before monitoring, add a strong `GRAFANA_ADMIN_PASSWORD` to `.env`. Grafana opens on localhost:3000. Prometheus is internal. MinIO console opens on localhost:9001; credentials are STORAGE_ACCESS_KEY and STORAGE_SECRET_KEY in `.env`. No paid service is required. OSM tile requests require internet, while manual coordinates remain available offline.

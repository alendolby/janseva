FROM python:3.12-slim
WORKDIR /srv/backend
COPY backend/requirements.lock .
RUN pip install --no-cache-dir -r requirements.lock
COPY backend/ /srv/backend/
COPY ml/ /srv/ml/
RUN useradd -m -u 10001 app && mkdir -p /srv/backend/uploads && chown -R app:app /srv
USER app
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && if [ \"$DEMO_MODE\" = \"true\" ]; then python -m app.seed; fi && uvicorn app.main:app --host 0.0.0.0 --port 8000"]

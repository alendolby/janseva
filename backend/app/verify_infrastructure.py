"""Run inside the healthy Docker backend after worker and beat start."""
from sqlalchemy import text
from redis import Redis
from app.core.config import settings
from app.core.db import engine
from app.services.storage import client
from app.tasks.jobs import celery

def verify():
    cfg=settings()
    if engine.dialect.name!='postgresql':raise RuntimeError('Run this command in the PostgreSQL Docker backend')
    with engine.connect() as db:
        assert db.scalar(text("SELECT ST_Covers(ST_GeomFromText('POLYGON((0 0,0 1,1 1,1 0,0 0))',4326), ST_SetSRID(ST_MakePoint(0.5,0.5),4326))"))
        assert db.scalar(text("SELECT ST_DWithin(ST_SetSRID(ST_MakePoint(0,0),4326)::geography, ST_SetSRID(ST_MakePoint(0,0.0001),4326)::geography,150)"))
        assert db.scalar(text("SELECT count(*) FROM pg_trigger WHERE tgname IN ('immutable_audit_logs','immutable_case_events')"))==2
    assert Redis.from_url(cfg.redis_url).ping()
    client().head_bucket(Bucket=cfg.storage_bucket)
    replies=celery.control.ping(timeout=5)
    if not replies:raise RuntimeError('No Celery worker responded. Inspect worker logs.')
    print('PostGIS geometry/distance, audit triggers, Redis, private MinIO bucket and Celery worker checked.')
if __name__=='__main__':verify()

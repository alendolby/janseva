import json,logging
from celery import Celery
from app.core.config import settings
from app.core.db import SessionLocal
from app.services.sla import check_slas
celery=Celery("janaseva",broker=settings().redis_url)
celery.conf.update(timezone="UTC",beat_schedule={"check-sla":{"task":"app.tasks.jobs.sla_tick","schedule":60.0}})
@celery.task(name="app.tasks.jobs.sla_tick")
def sla_tick():
    with SessionLocal.begin() as db: count=check_slas(db)
    logging.getLogger("janaseva").info(json.dumps({"event":"sla_job","processed":count}))
    return count

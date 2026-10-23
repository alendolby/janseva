from sqlalchemy import select
from app.models.entities import RoutingRule
from app.core.config import settings

def resolve(db,category_id,ward_id):
    if not ward_id: return None
    rules=db.scalars(select(RoutingRule).where(RoutingRule.category_id==category_id,
        RoutingRule.ward_id==ward_id,RoutingRule.active.is_(True))).all()
    valid=[r for r in rules if r.verified or settings().demo_mode]
    return valid[0] if len(valid)==1 else None

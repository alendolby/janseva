from app.models.entities import AuditLog, CaseEvent

def audit(db, actor, action, case=None, previous=None, current=None, reason=""):
    db.add(AuditLog(actor_id=actor.id if actor else None, case_id=case.id if case else None,
        action=action, previous=previous, current=current, reason=reason))
def event(db, case, actor, action, previous=None, current=None, note="", internal=False):
    db.add(CaseEvent(case_id=case.id, actor_id=actor.id if actor else None,
        action=action, previous=previous, current=current, note=note, internal=internal))
    audit(db, actor, action, case, {"status": previous}, {"status": current}, note)

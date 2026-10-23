from sqlalchemy import select, or_
from fastapi import HTTPException
from app.models.entities import Case, Escalation

def scoped_query(user):
    q = select(Case)
    if user.role == "CITIZEN":
        q = q.where(Case.citizen_id == user.id)
    elif user.role == "OFFICE":
        q = q.where(or_(Case.assigned_office_id == user.office_id,
            Case.id.in_(select(Escalation.case_id).where(Escalation.authority_id == user.office_id))))
    return q

def get_case(db, public_id, user, lock=False):
    q = scoped_query(user).where(Case.public_case_id == public_id)
    if lock:
        q = q.with_for_update(of=Case)
    case = db.scalar(q)
    if not case:
        raise HTTPException(404, "The requested complaint could not be found")
    return case

def writable(case, user):
    if user.role == "OFFICE" and case.assigned_office_id != user.office_id:
        raise HTTPException(403, "Escalation oversight is read-only. Request an admin reassignment")

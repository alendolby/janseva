from datetime import timedelta
from sqlalchemy import select
from app.models.entities import SlaPolicy,SlaInstance,Case,Escalation,Notification,OfficeUser,Office,now
from app.services.states import transition
from app.services.audit import event
from app.services.notifications import notify

def start_sla(db,case):
    policy=db.scalar(select(SlaPolicy).where(SlaPolicy.category_id==case.category_id,SlaPolicy.severity==case.priority))
    if not policy: return
    deadline=now()+timedelta(hours=policy.hours);case.sla_deadline=deadline
    instance=db.get(SlaInstance,case.id)
    if not instance:
        instance=SlaInstance(case_id=case.id);db.add(instance)
    instance.policy_id=policy.id;instance.start_time=now();instance.deadline=deadline
    instance.warning_time=deadline-timedelta(hours=policy.warning_hours);instance.status="ON_TRACK"
    instance.completed_at=None

def escalate(db,case,actor,reason,advance=False):
    active=db.scalar(select(Escalation).where(Escalation.case_id==case.id,Escalation.resolved_at.is_(None)).order_by(Escalation.to_level.desc()))
    if active and not advance: return active
    sla=db.get(SlaInstance,case.id)
    policy=db.get(SlaPolicy,sla.policy_id) if sla else None
    level=(db.scalar(select(__import__('sqlalchemy').func.max(Escalation.to_level)).where(Escalation.case_id==case.id)) or 0)+1
    target=policy.escalation_office_id if policy else None
    if active and advance:
        authority=db.get(Office,active.authority_id) if active.authority_id else None
        target=authority.parent_office_id if authority else None
        if not target:return active
    row=Escalation(case_id=case.id,from_level=level-1,to_level=level,authority_id=target,reason=reason);db.add(row)
    if case.status!="ESCALATED": transition(db,case,actor,"ESCALATED",reason,"ESCALATED")
    else:event(db,case,actor,"ESCALATION_ADVANCED",note=reason)
    if sla: sla.status="ESCALATED"
    if target:
        for user_id in db.scalars(select(OfficeUser.user_id).where(OfficeUser.office_id==target)):
            db.add(Notification(user_id=user_id,case_id=case.id,message=f"Escalation: {case.public_case_id}. {reason}"))
    return row

def check_slas(db):
    current=now();count=0
    rows=db.execute(select(SlaInstance,Case).join(Case,Case.id==SlaInstance.case_id)
        .where(SlaInstance.status!="COMPLETED").with_for_update(of=SlaInstance,skip_locked=True)).all()
    for sla,case in rows:
        if case.status in {"RESOLVED","CLOSED","REJECTED"}: continue
        if current>=sla.deadline and sla.status!="ESCALATED":
            sla.status="OVERDUE";notify(db,case,"SLA breached. Escalation recorded.")
            escalate(db,case,None,"Prototype SLA deadline exceeded");count+=1
        elif current>=sla.deadline and sla.status=="ESCALATED":
            latest=db.scalar(select(Escalation).where(Escalation.case_id==case.id).order_by(Escalation.to_level.desc()))
            policy=db.get(SlaPolicy,sla.policy_id)
            if latest and policy and current>=latest.created_at+timedelta(hours=policy.hours):
                result=escalate(db,case,None,"Next configured authority after continued SLA breach",advance=True)
                if result is not latest:count+=1
        elif current>=sla.warning_time and sla.status=="ON_TRACK":
            sla.status="DUE_SOON";notify(db,case,"SLA deadline is approaching")
            event(db,case,None,"SLA_APPROACHING",note="Prototype warning threshold reached");count+=1
    return count

def finish_sla(db,case):
    sla=db.get(SlaInstance,case.id)
    if sla: sla.status="COMPLETED";sla.completed_at=now()
    for row in db.scalars(select(Escalation).where(Escalation.case_id==case.id,Escalation.resolved_at.is_(None))):row.resolved_at=now()

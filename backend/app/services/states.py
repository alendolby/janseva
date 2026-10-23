from fastapi import HTTPException
from app.models.entities import now
from app.services.audit import event
from app.services.notifications import notify
TRANSITIONS = {
"DRAFT":{"SUBMITTED"}, "SUBMITTED":{"UNDER_AI_ANALYSIS"}, "UNDER_AI_ANALYSIS":{"ROUTING"},
"ROUTING":{"ASSIGNED","REJECTED"}, "ASSIGNED":{"ACKNOWLEDGED","REJECTED","ESCALATED"},
"ACKNOWLEDGED":{"IN_PROGRESS","WAITING_FOR_INFORMATION","REJECTED","ESCALATED"},
"IN_PROGRESS":{"WAITING_FOR_INFORMATION","RESOLVED","ESCALATED","REJECTED"},
"WAITING_FOR_INFORMATION":{"IN_PROGRESS","ESCALATED","REJECTED"},
"ESCALATED":{"ACKNOWLEDGED","IN_PROGRESS","WAITING_FOR_INFORMATION","RESOLVED","REJECTED"},
"RESOLVED":{"CLOSED","IN_PROGRESS"},"REJECTED":{"CLOSED","ROUTING"},"CLOSED":set()}

def transition(db,case,actor,target,note="",action="STATUS_CHANGED"):
    if target not in TRANSITIONS.get(case.status,set()):
        raise HTTPException(409,f"Cannot move from {case.status} to {target}")
    previous=case.status;case.status=target;case.updated_at=now()
    event(db,case,actor,action,previous,target,note)
    notify(db,case,f"{target.replace('_',' ').title()}. {note}")

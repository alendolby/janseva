from datetime import date,datetime,time,timedelta
from fastapi import APIRouter,Depends,HTTPException,UploadFile,File,Query,Response
from sqlalchemy import select,func
from app.core.db import get_db
from app.core.security import current_user,require
from app.models.entities import *
from app.schemas.contracts import CaseCreate,CaseOut,CasePage,Action,FeedbackIn,Message
from app.repositories.cases import scoped_query,get_case,writable
from app.services.complaints import create_case,serialize
from app.services.states import transition
from app.services.sla import start_sla,finish_sla,escalate
from app.services.audit import event,audit
from app.services.notifications import notify
from app.services import storage
from app.core.config import settings
router=APIRouter(tags=["Complaints"])
@router.post("/cases",response_model=CaseOut,status_code=201)
def submit(data:CaseCreate,user=Depends(require("CITIZEN")),db=Depends(get_db)):
    return serialize(create_case(db,data,user))
@router.get("/cases",response_model=CasePage)
def list_cases(page:int=Query(1,ge=1),size:int=Query(20,ge=1,le=100),status:str|None=None,
    severity:str|None=None,category_id:str|None=None,q:str=Query("",max_length=100),
    sla:str|None=None,officer_id:str|None=None,ward_id:str|None=None,from_date:date|None=None,to_date:date|None=None,user=Depends(current_user),db=Depends(get_db)):
    query=scoped_query(user)
    if status:query=query.where(Case.status==status)
    if severity:query=query.where(Case.priority==severity)
    if category_id:query=query.where(Case.category_id==category_id)
    if officer_id:query=query.where(Case.assigned_officer_id==officer_id)
    if ward_id:query=query.where(Case.id.in_(select(CaseLocation.case_id).where(CaseLocation.ward_id==ward_id)))
    if from_date:query=query.where(Case.created_at>=datetime.combine(from_date,time.min))
    if to_date:query=query.where(Case.created_at<datetime.combine(to_date+timedelta(days=1),time.min))
    if q:query=query.where(Case.title.ilike(f"%{q}%")|Case.public_case_id.ilike(f"%{q}%"))
    if sla=="overdue":query=query.where(Case.sla_deadline<now(),Case.status.not_in(["RESOLVED","CLOSED","REJECTED"]))
    if sla=="due-soon":query=query.where(Case.sla_deadline.between(now(),now()+timedelta(hours=24)),Case.status.not_in(["RESOLVED","CLOSED","REJECTED"]))
    total=db.scalar(select(func.count()).select_from(query.subquery()))
    rows=db.scalars(query.order_by(Case.created_at.desc()).offset((page-1)*size).limit(size)).unique().all()
    return {"items":[serialize(c) for c in rows],"total":total,"page":page,"size":size}
@router.get("/cases/{public_id}",response_model=dict)
def detail(public_id:str,user=Depends(current_user),db=Depends(get_db)):
    case=get_case(db,public_id,user);data=serialize(case);loc=db.get(CaseLocation,case.id)
    data["location"]={"latitude":loc.latitude,"longitude":loc.longitude,"address":loc.address,"ward_id":loc.ward_id} if loc else None
    pred=db.scalar(select(AiPrediction).where(AiPrediction.case_id==case.id))
    data["ai"]={"confidence":pred.confidence,"model":db.get(ModelVersion,pred.model_id).name,
        "corrected_category_id":pred.corrected_category_id,"baseline":True} if pred else None
    score=db.get(SeverityScore,case.id);data["severity"]=score.explanation if score else None
    data["evidence"]=[{"id":x.id,"filename":x.original_filename,"mime":x.mime_type,"kind":x.kind}
       for x in db.scalars(select(CaseEvidence).where(CaseEvidence.case_id==case.id))]
    data["timeline"]=timeline(public_id,user,db)
    member=db.get(IncidentMember,case.id)
    data["related_reports"]=db.scalar(select(func.count()).select_from(IncidentMember).where(IncidentMember.cluster_id==member.cluster_id))-1 if member else 0
    data["escalations"]=[{"level":e.to_level,"reason":e.reason,"authority_id":e.authority_id,"created_at":e.created_at.isoformat()+"Z"}
       for e in db.scalars(select(Escalation).where(Escalation.case_id==case.id))]
    feedback=db.scalar(select(Feedback).where(Feedback.case_id==case.id))
    data["feedback"]={"rating":feedback.rating,"comment":feedback.comment} if feedback else None
    return data
@router.get("/cases/{public_id}/timeline",response_model=list[dict])
def timeline(public_id:str,user=Depends(current_user),db=Depends(get_db)):
    case=get_case(db,public_id,user)
    q=select(CaseEvent).where(CaseEvent.case_id==case.id)
    if user.role=="CITIZEN":q=q.where(CaseEvent.internal.is_(False))
    return [{"action":e.action,"previous":e.previous,"current":e.current,"note":e.note,"internal":e.internal,
       "created_at":e.created_at.isoformat()+"Z"} for e in db.scalars(q.order_by(CaseEvent.created_at))]
@router.post("/cases/{public_id}/evidence",response_model=dict,status_code=201)
async def upload(public_id:str,kind:str=Query("REPORT",pattern="^(REPORT|RESOLUTION)$"),
    file:UploadFile=File(...),user=Depends(current_user),db=Depends(get_db)):
    case=get_case(db,public_id,user,True)
    if user.role=="CITIZEN" and kind!="REPORT":raise HTTPException(403,"Citizens can upload report evidence only")
    if user.role!="CITIZEN":writable(case,user)
    if case.status in {"CLOSED","REJECTED","RESOLVED"}:raise HTTPException(409,"Evidence cannot be added to a finished case")
    raw=await file.read(settings().max_upload_bytes+1)
    data,mime,ext=storage.validate(raw,file.filename)
    name=__import__('pathlib').Path(file.filename or 'evidence').name[:255]
    key=storage.store(data,ext)
    row=CaseEvidence(case_id=case.id,original_filename=name,storage_key=key,mime_type=mime,size=len(data),uploaded_by=user.id,kind=kind)
    db.add(row);event(db,case,user,"EVIDENCE_UPLOADED",note=kind);db.flush();return {"id":row.id,"filename":name}
@router.get("/cases/{public_id}/evidence/{evidence_id}")
def evidence(public_id:str,evidence_id:str,user=Depends(current_user),db=Depends(get_db)):
    case=get_case(db,public_id,user);row=db.get(CaseEvidence,evidence_id)
    if not row or row.case_id!=case.id:raise HTTPException(404,"Evidence not found")
    return Response(storage.fetch(row.storage_key),media_type=row.mime_type,
      headers={"Content-Disposition":"attachment; filename=evidence"+__import__('pathlib').Path(row.storage_key).suffix,"X-Content-Type-Options":"nosniff"})
@router.post("/cases/{public_id}/feedback",response_model=Message)
def feedback(public_id:str,data:FeedbackIn,user=Depends(require("CITIZEN")),db=Depends(get_db)):
    case=get_case(db,public_id,user,True)
    if case.status!="RESOLVED":raise HTTPException(409,"Feedback is available after resolution")
    if db.scalar(select(Feedback).where(Feedback.case_id==case.id)):raise HTTPException(409,"Feedback already recorded")
    db.add(Feedback(case_id=case.id,citizen_id=user.id,rating=data.rating,comment=data.comment))
    transition(db,case,user,"CLOSED",data.comment,"CASE_CLOSED")
    return {"message":"Resolution confirmed and feedback recorded"}
@router.post("/cases/{public_id}/{action}",response_model=CaseOut)
def case_action(public_id:str,action:str,data:Action,user=Depends(current_user),db=Depends(get_db)):
    case=get_case(db,public_id,user,True)
    if user.role=="CITIZEN":
        if action=="reopen" and case.status=="RESOLVED":
            if len(data.note.strip())<5:raise HTTPException(422,"Explain why the case should reopen")
            transition(db,case,user,"IN_PROGRESS",data.note,"CASE_REOPENED");case.resolved_at=None;start_sla(db,case)
        elif action=="reply" and case.status=="WAITING_FOR_INFORMATION":
            if len(data.note.strip())<5:raise HTTPException(422,"Provide the requested information")
            transition(db,case,user,"IN_PROGRESS",data.note,"INFORMATION_PROVIDED")
        else:raise HTTPException(403,"Action is not permitted")
    else:
        writable(case,user)
        if action in {"reject","resolve","escalate","request-info","note","correct-category","assign"} and len(data.note.strip())<5:
            raise HTTPException(422,"Provide a reason or update of at least five characters")
        targets={"acknowledge":"ACKNOWLEDGED","start":"IN_PROGRESS","request-info":"WAITING_FOR_INFORMATION","resolve":"RESOLVED","reject":"REJECTED"}
        if action in targets:
            if action=="resolve":
                if not db.scalar(select(CaseEvidence.id).where(CaseEvidence.case_id==case.id,CaseEvidence.kind=="RESOLUTION")):
                    raise HTTPException(422,"Upload resolution evidence before resolving")
                case.resolution_note=data.note;case.resolved_at=now()
            transition(db,case,user,targets[action],data.note,"CASE_"+targets[action])
            if action in {"resolve","reject"}:finish_sla(db,case)
        elif action=="escalate":escalate(db,case,user,data.note)
        elif action=="note":event(db,case,user,"INTERNAL_NOTE",note=data.note,internal=True)
        elif action=="assign":
            if user.role=="ADMIN" and data.office_id:
                office=db.get(Office,data.office_id)
                if not office:raise HTTPException(422,"Office does not exist")
                if case.status in {"CLOSED","RESOLVED","REJECTED"}:raise HTTPException(409,"Finished cases cannot be reassigned")
                case.assigned_office_id=office.id;case.routing_review_required=False
                if case.status=="ROUTING":transition(db,case,user,"ASSIGNED",data.note,"CASE_ASSIGNED")
                else:event(db,case,user,"CASE_REASSIGNED",note=data.note)
                start_sla(db,case)
            elif data.office_id and data.office_id!=case.assigned_office_id:raise HTTPException(403,"Only admin may reassign offices")
            if data.officer_id:
                officer=db.get(User,data.officer_id)
                if not officer or officer.role!="OFFICE" or officer.office_id!=case.assigned_office_id or not officer.active:
                    raise HTTPException(422,"Officer must be active and belong to the assigned office")
                case.assigned_officer_id=officer.id
            if not case.assigned_office_id:raise HTTPException(422,"Office is required")
            db.add(CaseAssignment(case_id=case.id,office_id=case.assigned_office_id,officer_id=case.assigned_officer_id,actor_id=user.id))
            event(db,case,user,"ASSIGNMENT_UPDATED",note=data.note);notify(db,case,"Assignment updated")
        elif action=="correct-category":
            category=db.get(Category,data.category_id)
            if not category:raise HTTPException(422,"Category does not exist")
            pred=db.scalar(select(AiPrediction).where(AiPrediction.case_id==case.id))
            pred.corrected_category_id=category.id;pred.corrected_by=user.id;pred.correction_reason=data.note
            case.category_id=category.id;case.routing_review_required=True
            event(db,case,user,"CATEGORY_CORRECTED",note=data.note)
            notify(db,case,"Category corrected. Admin routing review required")
        else:raise HTTPException(404,"Unknown case action")
    db.flush();db.refresh(case);return serialize(case)

from datetime import datetime
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from fastapi import HTTPException
from app.models.entities import *
from app.ml.baseline import classify, VERSION, ROOT
from app.ml.severity import severity
from app.ml.duplicates import related
from app.gis.jurisdiction import jurisdiction,point
from app.routing.engine import resolve
from app.services.states import transition
from app.services.audit import event
from app.services.sla import start_sla
import json

def next_id(db):
    year=datetime.now().year
    insert=pg_insert if db.bind.dialect.name=="postgresql" else sqlite_insert
    statement=insert(CaseCounter).values(year=year,value=1).on_conflict_do_update(
        index_elements=[CaseCounter.year],set_={"value":CaseCounter.value+1}).returning(CaseCounter.value)
    number=db.scalar(statement)
    return f"JNS-KL-{year}-{number:06d}"

def create_case(db,data,user):
    prediction=classify(data.title+" "+data.description)
    category=db.scalar(select(Category).where(Category.name==prediction["category"]))
    if data.category_id:
        category=db.get(Category,data.category_id)
        if not category: raise HTTPException(422,"Unknown category")
    if not category: raise HTTPException(503,"Classification categories have not been configured")
    matches=related(db,data.title+" "+data.description,category.id,data.latitude,data.longitude)
    result=severity(data.description,len(matches))
    case=Case(public_case_id=next_id(db),citizen_id=user.id,title=data.title,description=data.description,
        category_id=category.id,status="SUBMITTED",priority=result["level"],severity_score=result["score"])
    db.add(case);db.flush();event(db,case,user,"CASE_CREATED",current="SUBMITTED")
    transition(db,case,user,"UNDER_AI_ANALYSIS")
    model=db.scalar(select(ModelVersion).where(ModelVersion.name==VERSION))
    if not model:
        model=ModelVersion(name=VERSION,dataset_version="synthetic-v1",metrics=json.loads((ROOT/"ml/evaluation/classification.json").read_text()))
        db.add(model);db.flush()
    predicted_category=db.scalar(select(Category).where(Category.name==prediction["category"]))
    db.add(AiPrediction(case_id=case.id,model_id=model.id,category_id=predicted_category.id,confidence=prediction["confidence"]))
    db.add(SeverityScore(case_id=case.id,score=result["score"],explanation=result))
    event(db,case,user,"AI_ANALYSIS_COMPLETED",note=f"Baseline confidence {prediction['confidence']:.3f}")
    if matches:
        member=db.get(IncidentMember,matches[0]["case"].id)
        if member: cluster_id=member.cluster_id
        else:
            cluster=IncidentCluster();db.add(cluster);db.flush();cluster_id=cluster.id
            db.add(IncidentMember(case_id=matches[0]["case"].id,cluster_id=cluster_id,similarity=1))
        db.add(IncidentMember(case_id=case.id,cluster_id=cluster_id,similarity=matches[0]["score"]))
    transition(db,case,user,"ROUTING")
    geo=jurisdiction(db,data.latitude,data.longitude)
    db.add(CaseLocation(case_id=case.id,latitude=data.latitude,longitude=data.longitude,
       geometry=point(db,data.latitude,data.longitude),ward_id=geo["ward_id"] if geo else None,address=data.address))
    event(db,case,user,"JURISDICTION_IDENTIFIED",note=geo["ward"] if geo else "DATA SOURCE TO BE VERIFIED")
    rule=resolve(db,category.id,geo["ward_id"] if geo else None)
    if rule and (data.category_id or not prediction["review_required"]):
        case.assigned_office_id=rule.office_id
        db.add(CaseAssignment(case_id=case.id,office_id=rule.office_id,actor_id=user.id))
        transition(db,case,user,"ASSIGNED",action="CASE_ASSIGNED");start_sla(db,case)
    else:
        case.routing_review_required=True
        event(db,case,user,"ROUTING_REVIEW_REQUIRED",note="No trusted route or low-confidence classification")
    db.flush();db.refresh(case)
    return case

def serialize(case):
    fields=["public_case_id","title","description","status","priority","severity_score","category_id",
        "assigned_office_id","assigned_officer_id","routing_review_required","resolution_note"]
    result={k:getattr(case,k) for k in fields}
    for k in ["created_at","updated_at","resolved_at","sla_deadline"]:
        value=getattr(case,k);result[k]=value.isoformat()+"Z" if value else None
    result["category"]=case.category.name if case.category else None
    result["office"]=case.office.name if case.office else None
    return result

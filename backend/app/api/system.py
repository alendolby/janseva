from collections import Counter
from datetime import timedelta
from fastapi import APIRouter,Depends,Query,HTTPException
from sqlalchemy import select,func
from app.core.db import get_db
from app.core.security import current_user,require
from app.core.config import settings
from app.models.entities import *
from app.repositories.cases import scoped_query
from app.schemas.contracts import *
from app.services.audit import audit
from app.services.sla import check_slas
from app.ml.baseline import classify
from app.ml.severity import severity
from app.ml.duplicates import related
from app.gis.jurisdiction import jurisdiction,boundary_value
from app.routing.engine import resolve
import json
router=APIRouter(tags=["System and Administration"])

def record(row):
    result={}
    for col in row.__table__.columns:
        if col.name in {"geometry","password_hash","session_version","digest"}:continue
        value=getattr(row,col.name)
        result[col.name]=value.isoformat()+"Z" if isinstance(value,__import__('datetime').datetime) else value
    return result
@router.get("/catalog",response_model=dict)
def catalog(user=Depends(current_user),db=Depends(get_db)):
    out={name:[record(x) for x in db.scalars(select(model).limit(500))]
      for name,model in [("categories",Category),("offices",Office),("departments",Department),("districts",District),("local_bodies",LocalBody),("wards",Ward)]}
    if user.role in {"ADMIN","OFFICE"}:
        q=select(User).where(User.active.is_(True))
        if user.role=="OFFICE":q=q.join(OfficeUser).where(OfficeUser.office_id==user.office_id)
        out["officers"]=[{"id":u.id,"name":u.name,"office_id":u.office_id} for u in db.scalars(q).unique() if u.role=="OFFICE"]
    return out
@router.get("/notifications",response_model=list[dict])
def notifications(user=Depends(current_user),db=Depends(get_db)):
    return [record(x) for x in db.scalars(select(Notification).where(Notification.user_id==user.id).order_by(Notification.created_at.desc()).limit(100))]
@router.patch("/notifications/{notification_id}",response_model=Message)
def read_notification(notification_id:str,user=Depends(current_user),db=Depends(get_db)):
    row=db.get(Notification,notification_id)
    if not row or row.user_id!=user.id:raise HTTPException(404,"Notification not found")
    row.read=True;return {"message":"Marked read"}
@router.get("/analytics",response_model=dict)
def analytics(user=Depends(current_user),db=Depends(get_db)):
    q=scoped_query(user);sub=q.subquery()
    counts=lambda col:dict(db.execute(select(col,func.count()).select_from(sub).group_by(col)).all())
    status=counts(sub.c.status);priorities=counts(sub.c.priority)
    total=sum(status.values());active=total-sum(status.get(x,0) for x in ["RESOLVED","CLOSED","REJECTED"])
    overdue=db.scalar(select(func.count()).select_from(sub).where(sub.c.sla_deadline<now(),sub.c.status.not_in(["RESOLVED","CLOSED","REJECTED"])))
    due=db.scalar(select(func.count()).select_from(sub).where(sub.c.sla_deadline.between(now(),now()+timedelta(hours=24)),sub.c.status.not_in(["RESOLVED","CLOSED","REJECTED"])))
    resolved=db.execute(select(sub.c.resolved_at,sub.c.created_at,sub.c.sla_deadline).where(sub.c.resolved_at.is_not(None))).all()
    duration=sum((a-b).total_seconds()/3600 for a,b,c in resolved)/len(resolved) if resolved else 0
    with_deadline=[x for x in resolved if x[2]]
    compliance=sum(a<=c for a,b,c in with_deadline)/len(with_deadline)*100 if with_deadline else None
    categories=dict(db.execute(select(Category.name,func.count()).join(sub,sub.c.category_id==Category.id).group_by(Category.name)).all())
    trends=dict((str(k),v) for k,v in db.execute(select(func.date(sub.c.created_at),func.count()).group_by(func.date(sub.c.created_at))).all())
    offices=dict(db.execute(select(Office.name,func.count()).join(sub,sub.c.assigned_office_id==Office.id).group_by(Office.name)).all())
    geo=db.execute(select(CaseLocation.latitude,CaseLocation.longitude,sub.c.public_case_id,sub.c.title,sub.c.priority)
      .join(sub,sub.c.id==CaseLocation.case_id).order_by(sub.c.created_at.desc()).limit(100)).all()
    return {"total":total,"active":active,"resolved":status.get("RESOLVED",0)+status.get("CLOSED",0),
        "pending":status.get("ROUTING",0)+status.get("ASSIGNED",0),"overdue":overdue,"due_soon":due,
        "escalated":status.get("ESCALATED",0),"critical":priorities.get("Critical",0),"high":priorities.get("High",0),
        "average_resolution_hours":round(duration,2),"sla_compliance":round(compliance,1) if compliance is not None else None,
        "escalation_rate":round(status.get("ESCALATED",0)/total*100,1) if total else 0,
        "resolution_rate":round((status.get("RESOLVED",0)+status.get("CLOSED",0))/total*100,1) if total else 0,
        "status":status,"categories":categories,"severity":priorities,"trends":trends,"offices":offices,
        "map":[{"latitude":a,"longitude":b,"case_id":c,"title":d,"priority":e} for a,b,c,d,e in geo],
        "map_limit":100,"prototype":True}
@router.get("/gis/jurisdiction",response_model=dict)
def geo(latitude:float=Query(ge=-90,le=90),longitude:float=Query(ge=-180,le=180),user=Depends(current_user),db=Depends(get_db)):
    return jurisdiction(db,latitude,longitude) or {"review_required":True,"message":"DATA SOURCE TO BE VERIFIED"}
@router.get("/routing/resolve",response_model=dict)
def route(category_id:str,ward_id:str,user=Depends(require("ADMIN","OFFICE")),db=Depends(get_db)):
    rule=resolve(db,category_id,ward_id)
    return record(rule) if rule else {"status":"ROUTING_REVIEW_REQUIRED"}
@router.post("/ai/classify",response_model=dict)
def classify_api(data:TextIn,user=Depends(current_user)):return classify(data.text)
@router.post("/ai/severity",response_model=dict)
def severity_api(data:TextIn,user=Depends(current_user)):return severity(data.text)
@router.post("/ai/duplicate-check",response_model=dict)
def duplicate_api(data:DuplicateIn,user=Depends(current_user),db=Depends(get_db)):
    matches=related(db,data.text,data.category_id,data.latitude,data.longitude)
    return {"related_count":len(matches),"method":"Prototype TF-IDF similarity, category, distance and 30 day window"}
ADMIN_MODELS={"users":User,"departments":Department,"offices":Office,"categories":Category,"districts":District,
"local-bodies":LocalBody,"gis":Ward,"routing-rules":RoutingRule,"sla":SlaPolicy,"escalations":Escalation,"audit-logs":AuditLog,"ai":ModelVersion}
@router.get("/admin/settings",response_model=dict)
def config_info(user=Depends(require("ADMIN"))):
    return {"demo_mode":settings().demo_mode,"storage_mode":settings().storage_mode,"token_minutes":settings().token_minutes,
      "max_upload_mb":settings().max_upload_bytes//1024//1024,"email_configured":bool(settings().smtp_host),"version":"1.0.0"}
@router.post("/admin/sla/check",response_model=dict)
def tick(user=Depends(require("ADMIN")),db=Depends(get_db)):
    return {"processed":check_slas(db)}
@router.get("/admin/ai/summary",response_model=dict)
def ai_summary(user=Depends(require("ADMIN")),db=Depends(get_db)):
    predictions=db.scalars(select(AiPrediction).order_by(AiPrediction.created_at.desc()).limit(500)).all()
    return {"models":[record(m) for m in db.scalars(select(ModelVersion))],
        "prediction_count":db.scalar(select(func.count()).select_from(AiPrediction)),
        "low_confidence_count":db.scalar(select(func.count()).select_from(AiPrediction).where(AiPrediction.confidence<0.4)),
        "human_corrections":sum(bool(p.corrected_category_id) for p in predictions),
        "confidence_distribution":{"below_40":sum(p.confidence<0.4 for p in predictions),"40_to_70":sum(0.4<=p.confidence<0.7 for p in predictions),"70_plus":sum(p.confidence>=0.7 for p in predictions)},
        "sample_limit":500}
@router.get("/admin/{resource}",response_model=dict)
def admin_list(resource:str,page:int=Query(1,ge=1),size:int=Query(50,ge=1,le=100),user=Depends(require("ADMIN")),db=Depends(get_db)):
    model=ADMIN_MODELS.get(resource)
    if not model:raise HTTPException(404,"Resource not found")
    rows=db.scalars(select(model).offset((page-1)*size).limit(size)).all()
    items=[UserOut.model_validate(r).model_dump() if model==User else record(r) for r in rows]
    return {"items":items,"total":db.scalar(select(func.count()).select_from(model)),"page":page,"size":size}
@router.post("/admin/users",response_model=UserOut,status_code=201)
def create_staff(data:Register,role:RoleName=Query("OFFICE"),office_id:str|None=None,user=Depends(require("ADMIN")),db=Depends(get_db)):
    from app.core.security import hasher
    if role=="OFFICE" and not db.get(Office,office_id):raise HTTPException(422,"Choose an existing office")
    if db.scalar(select(User).where(User.email==str(data.email).lower())):raise HTTPException(409,"Account exists")
    row=User(email=str(data.email).lower(),name=data.name,password_hash=hasher.hash(data.password));db.add(row);db.flush()
    db.add(UserRole(user_id=row.id,role_name=role))
    if role=="OFFICE":db.add(OfficeUser(user_id=row.id,office_id=office_id))
    elif role=="CITIZEN":db.add(CitizenProfile(user_id=row.id))
    db.flush();db.refresh(row);audit(db,user,"USER_CREATED",current={"user_id":row.id,"role":role});return row
@router.patch("/admin/users/{user_id}",response_model=UserOut)
def edit_user(user_id:str,data:UserEdit,user=Depends(require("ADMIN")),db=Depends(get_db)):
    row=db.get(User,user_id)
    if not row:raise HTTPException(404,"User not found")
    if row.id==user.id:raise HTTPException(409,"Cannot change your own permissions here")
    old=UserOut.model_validate(row).model_dump();role=data.role or row.role
    office_id=data.office_id or row.office_id
    if role=="OFFICE" and not db.get(Office,office_id):raise HTTPException(422,"Office role requires a valid office")
    if data.active is not None:row.active=data.active
    if data.role:
        row.roles.clear();db.flush();row.roles.append(UserRole(role_name=role))
    if role=="OFFICE":
        if row.office_membership:row.office_membership.office_id=office_id
        else:row.office_membership=OfficeUser(office_id=office_id)
    elif row.office_membership:db.delete(row.office_membership)
    row.session_version+=1;db.flush();db.refresh(row)
    audit(db,user,"USER_UPDATED",previous=old,current=UserOut.model_validate(row).model_dump());return row

def validate_refs(db,model,data):
    for col in model.__table__.columns:
        if col.name in data and data[col.name] is not None:
            for fk in col.foreign_keys:
                target=next((m for m in Base.registry.mappers if m.local_table.name==fk.column.table.name),None)
                if target and not db.get(target.class_,data[col.name]):raise HTTPException(422,f"Invalid reference: {col.name}")

def save_resource(db,user,model,data,resource,identifier=None):
    values=data.model_dump();validate_refs(db,model,values)
    if model==SlaPolicy and values["warning_hours"]>=values["hours"]:raise HTTPException(422,"Warning period must be shorter than SLA")
    if model==Ward:
        geom=boundary_value(db,values["boundary"]);values["boundary"]=json.dumps(values["boundary"]);values["geometry"]=geom
    if model==Office:
        parent=values.get("parent_office_id");seen={identifier} if identifier else set()
        while parent:
            if parent in seen:raise HTTPException(422,"Office hierarchy cannot contain cycles")
            seen.add(parent);parent=db.get(Office,parent).parent_office_id
    if identifier:
        row=db.get(model,identifier)
        if not row:raise HTTPException(404,"Record not found")
        previous=record(row)
        for k,v in values.items():setattr(row,k,v)
    else:row=model(**values);db.add(row);previous=None
    db.flush();audit(db,user,"ADMIN_"+resource.upper(),previous=previous,current=record(row));return record(row)

@router.post("/admin/departments",response_model=dict,status_code=201)
def create_departments(data:DepartmentIn,user=Depends(require("ADMIN")),db=Depends(get_db)):
    return save_resource(db,user,Department,data,"departments")
@router.put("/admin/departments/{identifier}",response_model=dict)
def update_departments(identifier:str,data:DepartmentIn,user=Depends(require("ADMIN")),db=Depends(get_db)):
    return save_resource(db,user,Department,data,"departments",identifier)

@router.post("/admin/offices",response_model=dict,status_code=201)
def create_offices(data:OfficeIn,user=Depends(require("ADMIN")),db=Depends(get_db)):
    return save_resource(db,user,Office,data,"offices")
@router.put("/admin/offices/{identifier}",response_model=dict)
def update_offices(identifier:str,data:OfficeIn,user=Depends(require("ADMIN")),db=Depends(get_db)):
    return save_resource(db,user,Office,data,"offices",identifier)

@router.post("/admin/categories",response_model=dict,status_code=201)
def create_categories(data:DepartmentIn,user=Depends(require("ADMIN")),db=Depends(get_db)):
    return save_resource(db,user,Category,data,"categories")
@router.put("/admin/categories/{identifier}",response_model=dict)
def update_categories(identifier:str,data:DepartmentIn,user=Depends(require("ADMIN")),db=Depends(get_db)):
    return save_resource(db,user,Category,data,"categories",identifier)

@router.post("/admin/districts",response_model=dict,status_code=201)
def create_districts(data:DistrictIn,user=Depends(require("ADMIN")),db=Depends(get_db)):
    return save_resource(db,user,District,data,"districts")
@router.put("/admin/districts/{identifier}",response_model=dict)
def update_districts(identifier:str,data:DistrictIn,user=Depends(require("ADMIN")),db=Depends(get_db)):
    return save_resource(db,user,District,data,"districts",identifier)

@router.post("/admin/local-bodies",response_model=dict,status_code=201)
def create_local_bodies(data:LocalBodyIn,user=Depends(require("ADMIN")),db=Depends(get_db)):
    return save_resource(db,user,LocalBody,data,"local-bodies")
@router.put("/admin/local-bodies/{identifier}",response_model=dict)
def update_local_bodies(identifier:str,data:LocalBodyIn,user=Depends(require("ADMIN")),db=Depends(get_db)):
    return save_resource(db,user,LocalBody,data,"local-bodies",identifier)

@router.post("/admin/gis",response_model=dict,status_code=201)
def create_gis(data:WardIn,user=Depends(require("ADMIN")),db=Depends(get_db)):
    return save_resource(db,user,Ward,data,"gis")
@router.put("/admin/gis/{identifier}",response_model=dict)
def update_gis(identifier:str,data:WardIn,user=Depends(require("ADMIN")),db=Depends(get_db)):
    return save_resource(db,user,Ward,data,"gis",identifier)

@router.post("/admin/routing-rules",response_model=dict,status_code=201)
def create_routing_rules(data:RuleIn,user=Depends(require("ADMIN")),db=Depends(get_db)):
    return save_resource(db,user,RoutingRule,data,"routing-rules")
@router.put("/admin/routing-rules/{identifier}",response_model=dict)
def update_routing_rules(identifier:str,data:RuleIn,user=Depends(require("ADMIN")),db=Depends(get_db)):
    return save_resource(db,user,RoutingRule,data,"routing-rules",identifier)

@router.post("/admin/sla",response_model=dict,status_code=201)
def create_sla(data:PolicyIn,user=Depends(require("ADMIN")),db=Depends(get_db)):
    return save_resource(db,user,SlaPolicy,data,"sla")
@router.put("/admin/sla/{identifier}",response_model=dict)
def update_sla(identifier:str,data:PolicyIn,user=Depends(require("ADMIN")),db=Depends(get_db)):
    return save_resource(db,user,SlaPolicy,data,"sla",identifier)

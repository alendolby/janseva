import os,json
from datetime import timedelta
from sqlalchemy import select
from app.core.db import SessionLocal
from app.core.config import settings
from app.core.security import hasher
from app.models.entities import *
from app.gis.jurisdiction import boundary_value
from app.schemas.contracts import CaseCreate,Register
from app.services.complaints import create_case
from app.ml.baseline import train,VERSION

def seed():
    if not settings().demo_mode:raise RuntimeError("Seeding requires DEMO_MODE=true")
    password=os.environ.get("DEMO_PASSWORD")
    if not password:raise RuntimeError("Set DEMO_PASSWORD to a safe synthetic demo password")
    Register(name="Demo Citizen",email="citizen@example.com",password=password)
    _,metrics=train()
    with SessionLocal.begin() as db:
        if db.scalar(select(User).limit(1)):return
        for name in ["CITIZEN","OFFICE","ADMIN"]:db.add(Role(name=name))
        db.flush()
        district=District(name="DEMO District A (synthetic)");department=Department(name="DEMO Civic Services")
        db.add_all([district,department]);db.flush()
        body=LocalBody(name="DEMO Local Body A",district_id=district.id);db.add(body);db.flush()
        coords=[[[76.25,9.90],[76.35,9.90],[76.35,10.03],[76.25,10.03],[76.25,9.90]]]
        boundary={"type":"MultiPolygon","coordinates":[coords]}
        ward=Ward(name="DEMO Ward A",local_body_id=body.id,boundary=json.dumps(boundary),
           geometry=boundary_value(db,boundary),source="Synthetic rectangular fixture, not an administrative boundary",verified=False)
        db.add(ward);db.flush()
        higher=Office(name="DEMO Supervisory Office",department_id=department.id,local_body_id=body.id)
        db.add(higher);db.flush()
        office=Office(name="DEMO Civic Office A",department_id=department.id,local_body_id=body.id,parent_office_id=higher.id)
        other=Office(name="DEMO Civic Office B",department_id=department.id,local_body_id=body.id)
        db.add_all([office,other]);db.flush()
        users={}
        for name,email,role,oid in [("Demo Citizen","citizen@example.com","CITIZEN",None),
         ("Second Citizen","citizen2@example.com","CITIZEN",None),("Demo Officer","office@example.com","OFFICE",office.id),
         ("Other Officer","office2@example.com","OFFICE",other.id),("Demo Supervisor","supervisor@example.com","OFFICE",higher.id),
         ("Demo Administrator","admin@example.com","ADMIN",None)]:
            user=User(name=name,email=email,password_hash=hasher.hash(password),verified=True)
            db.add(user);db.flush();db.add(UserRole(user_id=user.id,role_name=role))
            if oid:db.add(OfficeUser(user_id=user.id,office_id=oid))
            else:db.add(CitizenProfile(user_id=user.id))
            users[email]=user
        for name in ["Pothole","Garbage","Streetlight","Waterlogging","Drainage","Road Damage"]:
            category=Category(name=name);db.add(category);db.flush()
            db.add(RoutingRule(category_id=category.id,ward_id=ward.id,office_id=office.id,source="DEMO responsibility fixture",verified=False))
            for severity,hours in [("Critical",24),("High",72),("Moderate",168),("Low",336)]:
                db.add(SlaPolicy(category_id=category.id,severity=severity,hours=hours,warning_hours=min(12,hours//4),escalation_office_id=higher.id))
        db.add(ModelVersion(name=VERSION,dataset_version="synthetic-v1",metrics=metrics));db.flush()
        for user in users.values():db.refresh(user)
        for title,description in [("Pothole near school","There is a large pothole near the school entrance and vehicles are swerving to avoid it"),
            ("Garbage at market","Garbage is piled up outside the market and waste collection has stopped for a week"),
            ("Broken public streetlight","The streetlight outside my home is broken and does not turn on at night")]:
            create_case(db,CaseCreate(title=title,description=description,latitude=9.965,longitude=76.30,address="DEMO location A"),users["citizen@example.com"])
    print("Synthetic demo data seeded. Accounts use your DEMO_PASSWORD.")
if __name__=="__main__":seed()

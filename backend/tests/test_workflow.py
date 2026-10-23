from io import BytesIO
from datetime import timedelta
from PIL import Image
from sqlalchemy import select,text
from app.core.db import SessionLocal
from app.models.entities import Case,SlaInstance,Escalation,CaseEvent,now

def png():
    b=BytesIO();Image.new("RGB",(32,32),"green").save(b,format="PNG");return b.getvalue()
def test_end_to_end(client,headers,case):
    assert case["status"]=="ASSIGNED"
    path="/api/cases/"+case["public_case_id"]
    assert client.post(path+"/acknowledge",headers=headers["office"],json={}).status_code==200
    assert client.post(path+"/start",headers=headers["office"],json={}).json()["status"]=="IN_PROGRESS"
    assert client.post(path+"/resolve",headers=headers["office"],json={"note":"Repair completed"}).status_code==422
    r=client.post(path+"/evidence?kind=RESOLUTION",headers=headers["office"],files={"file":("repair.png",png(),"image/png")});assert r.status_code==201,r.text
    assert client.post(path+"/resolve",headers=headers["office"],json={"note":"Repair completed and checked"}).json()["status"]=="RESOLVED"
    assert client.post(path+"/feedback",headers=headers["citizen"],json={"rating":5,"comment":"Repair looks good"}).status_code==200
    assert client.get(path,headers=headers["citizen"]).json()["status"]=="CLOSED"
    assert client.get("/api/notifications",headers=headers["citizen"]).json()
    assert client.get("/api/analytics",headers=headers["admin"]).json()["resolved"]>=1

def test_idor(client,headers,case):
    path="/api/cases/"+case["public_case_id"]
    assert client.get(path,headers=headers["other"]).status_code==404
    assert client.get(path,headers=headers["unrelated"]).status_code==404
    assert client.get("/api/admin/users",headers=headers["citizen"]).status_code==403
    assert client.get(path).status_code==401
    assert client.post(path+"/acknowledge",headers=headers["citizen"],json={}).status_code==403

def test_invalid_status(client,headers,case):
    r=client.post("/api/cases/"+case["public_case_id"]+"/start",headers=headers["office"],json={})
    assert r.status_code==409

def test_evidence_access_and_validation(client,headers,case):
    path="/api/cases/"+case["public_case_id"]
    assert client.post(path+"/evidence",headers=headers["citizen"],files={"file":("fake.png",b'<script>alert(1)</script>',"image/png")}).status_code==422
    assert client.post(path+"/evidence",headers=headers["citizen"],files={"file":("wrong.pdf",png(),"application/pdf")}).status_code==422
    r=client.post(path+"/evidence",headers=headers["citizen"],files={"file":("valid.png",png(),"image/png")});assert r.status_code==201
    assert client.get(path+"/evidence/"+r.json()["id"],headers=headers["other"]).status_code==404
    assert client.get(path+"/evidence/"+r.json()["id"],headers=headers["citizen"]).content.startswith(b'\x89PNG')
    assert client.post(path+"/evidence?kind=RESOLUTION",headers=headers["citizen"],files={"file":("valid.png",png(),"image/png")}).status_code==403

def test_sla_escalation_idempotence(client,headers,case):
    with SessionLocal.begin() as db:
        row=db.scalar(select(Case).where(Case.public_case_id==case["public_case_id"]))
        sla=db.get(SlaInstance,row.id);sla.deadline=now()-timedelta(hours=1);row.sla_deadline=sla.deadline
    assert client.post("/api/admin/sla/check",headers=headers["admin"]).json()["processed"]>=1
    client.post("/api/admin/sla/check",headers=headers["admin"])
    with SessionLocal() as db:
        row=db.scalar(select(Case).where(Case.public_case_id==case["public_case_id"]))
        assert row.status=="ESCALATED"
        assert len(db.scalars(select(Escalation).where(Escalation.case_id==row.id)).all())==1

def test_review_when_outside_boundary(client,headers):
    data={"title":"Pothole far outside boundary","description":"A dangerous pothole on the street needs immediate repair","latitude":15,"longitude":75,"address":"Outside synthetic boundary"}
    r=client.post("/api/cases",headers=headers["citizen"],json=data)
    assert r.status_code==201 and r.json()["routing_review_required"] and r.json()["status"]=="ROUTING"

def test_internal_notes_private(client,headers,case):
    path="/api/cases/"+case["public_case_id"]
    assert client.post(path+"/note",headers=headers["office"],json={"note":"Private officer investigation"}).status_code==200
    assert not any(x["internal"] for x in client.get(path+"/timeline",headers=headers["citizen"]).json())
    assert any(x["internal"] for x in client.get(path+"/timeline",headers=headers["office"]).json())

def test_audit_immutable(client,headers,case):
    import pytest
    from sqlalchemy.exc import DatabaseError
    with SessionLocal() as db:
        with pytest.raises(DatabaseError):db.execute(text("UPDATE audit_logs SET action='tamper'"))

def test_information_reply(client,headers,case):
    path="/api/cases/"+case["public_case_id"]
    client.post(path+"/acknowledge",headers=headers["office"],json={})
    assert client.post(path+"/request-info",headers=headers["office"],json={"note":"Please provide exact entrance location"}).status_code==200
    assert client.post(path+"/reply",headers=headers["citizen"],json={"note":"Near the eastern school entrance"}).json()["status"]=="IN_PROGRESS"

def test_unique_case_ids(client,headers):
    data={"title":"Garbage accumulation","description":"Garbage is piled up outside the market and waste has not been collected","latitude":9.965,"longitude":76.30,"address":"Demo market"}
    ids=[client.post('/api/cases',headers=headers['citizen'],json=data).json()['public_case_id'] for _ in range(4)]
    assert len(set(ids))==4

def test_pagination_and_scoped_analytics(client,headers):
    data=client.get('/api/cases?size=1',headers=headers['citizen']).json()
    assert len(data['items'])==1 and data['total']>=1
    assert client.get('/api/analytics',headers=headers['other']).json()['total']==0

def test_reopen(client,headers,case):
    path='/api/cases/'+case['public_case_id']
    client.post(path+'/acknowledge',headers=headers['office'],json={});client.post(path+'/start',headers=headers['office'],json={})
    client.post(path+'/evidence?kind=RESOLUTION',headers=headers['office'],files={'file':('repair.png',png(),'image/png')})
    client.post(path+'/resolve',headers=headers['office'],json={'note':'Repair has been completed'})
    assert client.post(path+'/reopen',headers=headers['citizen'],json={'note':'The surface is still damaged'}).json()['status']=='IN_PROGRESS'

def test_concurrent_case_ids(client,headers):
    from concurrent.futures import ThreadPoolExecutor
    data={"title":"Pothole concurrency test","description":"A large pothole near the school has vehicles swerving","latitude":9.965,"longitude":76.30,"address":"Synthetic location"}
    def submit(_):
        response=client.post('/api/cases',headers=headers['citizen'],json=data)
        assert response.status_code==201,response.text
        return response.json()['public_case_id']
    with ThreadPoolExecutor(max_workers=4) as pool:ids=list(pool.map(submit,range(8)))
    assert len(set(ids))==8

def test_admin_assignment_and_correction(client,headers,case):
    path='/api/cases/'+case['public_case_id'];catalog=client.get('/api/catalog',headers=headers['admin']).json()
    office=next(x for x in catalog['offices'] if x['name']=='DEMO Civic Office B')
    assert client.post(path+'/assign',headers=headers['admin'],json={'office_id':office['id'],'note':'Route to another demo office'}).status_code==200
    assert client.get(path,headers=headers['office']).status_code==404
    assert client.get(path,headers=headers['unrelated']).status_code==200
    category=catalog['categories'][0]
    assert client.post(path+'/correct-category',headers=headers['unrelated'],json={'category_id':category['id'],'note':'Officer reviewed the category'}).status_code==200
    result=client.get(path,headers=headers['citizen']).json()
    assert result['category_id']==category['id'] and result['routing_review_required']

def test_sla_warning_and_notification_idor(client,headers,case):
    with SessionLocal.begin() as db:
        row=db.scalar(select(Case).where(Case.public_case_id==case['public_case_id']))
        sla=db.get(SlaInstance,row.id);sla.warning_time=now()-timedelta(minutes=1)
    client.post('/api/admin/sla/check',headers=headers['admin'])
    with SessionLocal() as db:
        assert db.get(SlaInstance,row.id).status=='DUE_SOON'
    notifications=client.get('/api/notifications',headers=headers['citizen']).json()
    assert client.patch('/api/notifications/'+notifications[0]['id'],headers=headers['other']).status_code==404

def test_multilevel_configured_escalation(client,headers,case):
    from app.models.entities import Office,SlaPolicy
    with SessionLocal.begin() as db:
        row=db.scalar(select(Case).where(Case.public_case_id==case['public_case_id']))
        sla=db.get(SlaInstance,row.id);policy=db.get(SlaPolicy,sla.policy_id)
        first=db.get(Office,policy.escalation_office_id)
        next_office=Office(name='DEMO Next Authority',department_id=first.department_id,local_body_id=first.local_body_id)
        db.add(next_office);db.flush();first.parent_office_id=next_office.id
        sla.deadline=now()-timedelta(hours=1)
    client.post('/api/admin/sla/check',headers=headers['admin'])
    with SessionLocal.begin() as db:
        previous=db.scalar(select(Escalation).where(Escalation.case_id==row.id).order_by(Escalation.to_level.desc()))
        previous.created_at=now()-timedelta(hours=policy.hours+1)
    client.post('/api/admin/sla/check',headers=headers['admin'])
    client.post('/api/admin/sla/check',headers=headers['admin'])
    with SessionLocal() as db:
        levels=db.scalars(select(Escalation).where(Escalation.case_id==row.id).order_by(Escalation.to_level)).all()
        assert [e.to_level for e in levels]==[1,2]
        assert levels[-1].authority_id==next_office.id

from app.ml.baseline import classify
from app.ml.severity import severity
from app.ml.duplicates import distance

def test_passwords_and_register_role(client):
    payload={'name':'New Citizen','email':'newcitizen@example.com','password':'Registration2026Safe'}
    r=client.post('/api/auth/register',json={**payload,'role':'ADMIN'});assert r.status_code==201
    assert r.json()['user']['role']=='CITIZEN'
    assert client.post('/api/auth/register',json={**payload,'password':'short'}).status_code==422
    assert client.post('/api/auth/login',json={**payload,'password':'WrongPassword2026'}).status_code==401

def test_logout_revokes_token(client,headers):
    assert client.post('/api/auth/logout',headers=headers['citizen']).status_code==200
    assert client.get('/api/users/me',headers=headers['citizen']).status_code==401

def test_reset_and_verify_tokens(client,headers):
    r=client.post('/api/auth/verify/request',json={'email':'citizen2@example.com'})
    token=r.json()['demo_token']
    assert client.post('/api/auth/verify/confirm',json={'token':token}).status_code==200
    assert client.post('/api/auth/verify/confirm',json={'token':token}).status_code==400
    reset=client.post('/api/auth/reset/request',json={'email':'citizen2@example.com'}).json()['demo_token']
    assert client.post('/api/auth/reset/confirm',json={'token':reset,'password':'TestCitizen2026Safe'}).status_code==200
    assert client.get('/api/users/me',headers=headers['other']).status_code==401

def test_admin_rules_validation(client,headers):
    catalog=client.get('/api/catalog',headers=headers['admin']).json()
    r=client.post('/api/admin/routing-rules',headers=headers['admin'],json={'category_id':'missing','ward_id':catalog['wards'][0]['id'],'office_id':catalog['offices'][0]['id'],'source':'Demo policy'})
    assert r.status_code==422
    assert client.post('/api/admin/gis',headers=headers['admin'],json={'name':'Invalid geometry','local_body_id':catalog['local_bodies'][0]['id'],'boundary':{'type':'Point','coordinates':[0,0]},'source':'Synthetic fixture'}).status_code==422
    assert client.post('/api/admin/sla',headers=headers['admin'],json={'category_id':catalog['categories'][0]['id'],'severity':'High','hours':4,'warning_hours':5}).status_code==422

def test_baseline_and_severity():
    pred=classify('Large pothole near school entrance and vehicles swerving')
    assert pred['category']=='Pothole' and 0<=pred['confidence']<=1 and pred['baseline']
    score=severity('large pothole near school vehicles swerving')
    assert score['score']==80 and score['level']=='Critical'
    assert distance(9.9,76.3,9.9,76.3)==0

def test_gis(client,headers):
    assert client.get('/api/gis/jurisdiction?latitude=9.965&longitude=76.30',headers=headers['citizen']).json()['ward']=='DEMO Ward A'
    assert client.get('/api/gis/jurisdiction?latitude=0&longitude=0',headers=headers['citizen']).json()['review_required']

def test_rate_limit(client):
    codes=[client.post('/api/auth/login',json={'email':'nobody@example.com','password':'WrongPassword2026'}).status_code for _ in range(22)]
    assert codes[-1]==429 and codes[0]==401

def test_admin_user_deactivation(client,headers):
    r=client.post('/api/admin/users?role=CITIZEN',headers=headers['admin'],json={'name':'Disabled Demo','email':'disabled@example.com','password':'Disabled2026Safe'})
    assert r.status_code==201
    assert client.patch('/api/admin/users/'+r.json()['id'],headers=headers['admin'],json={'active':False}).status_code==200
    assert client.post('/api/auth/login',json={'email':'disabled@example.com','password':'Disabled2026Safe'}).status_code==401

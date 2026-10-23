import os,tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
os.environ["JWT_SECRET"]="test-only-"+"a"*64
os.environ["DEMO_MODE"]="true"
os.environ["DEMO_PASSWORD"]="TestCitizen2026Safe"
os.environ["DATABASE_URL"]="sqlite:///"+str(Path(tempfile.mkdtemp())/"test.db")
os.environ["UPLOAD_DIR"]=tempfile.mkdtemp()
os.environ["RATE_LIMIT_BACKEND"]="memory"
from alembic import command
from alembic.config import Config
from app.seed import seed
command.upgrade(Config("alembic.ini"),"head");seed()
from app.main import app
@pytest.fixture
def client():
    app.middleware_stack=None
    with TestClient(app) as c:yield c
@pytest.fixture
def headers(client):
    result={}
    for role,email in [("citizen","citizen@example.com"),("other","citizen2@example.com"),("office","office@example.com"),("unrelated","office2@example.com"),("admin","admin@example.com")]:
        r=client.post("/api/auth/login",json={"email":email,"password":os.environ["DEMO_PASSWORD"]})
        assert r.status_code==200,r.text
        result[role]={"Authorization":"Bearer "+r.json()["access_token"]}
    return result
@pytest.fixture
def case(client,headers):
    r=client.post("/api/cases",headers=headers["citizen"],json={"title":"Large pothole near school","description":"There is a large pothole near the school entrance and vehicles are swerving to avoid it",
        "latitude":9.965,"longitude":76.30,"address":"Synthetic demo school"})
    assert r.status_code==201,r.text
    return r.json()

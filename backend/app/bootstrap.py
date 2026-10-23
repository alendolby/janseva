"""Initialize an empty deployment without installing synthetic government data."""
import os
from sqlalchemy import select
from app.core.db import SessionLocal
from app.models.entities import User,Role,UserRole
from app.core.security import hasher
from app.schemas.contracts import Register
from app.services.audit import audit

def bootstrap():
    data=Register(name="System Administrator",email=os.environ["ADMIN_EMAIL"],password=os.environ["ADMIN_PASSWORD"])
    with SessionLocal.begin() as db:
        if db.scalar(select(User).limit(1)):raise RuntimeError("Bootstrap is only available on an empty user table")
        for name in ["CITIZEN","OFFICE","ADMIN"]:db.add(Role(name=name))
        db.flush();user=User(name=data.name,email=str(data.email).lower(),password_hash=hasher.hash(data.password))
        db.add(user);db.flush();db.add(UserRole(user_id=user.id,role_name="ADMIN"));audit(db,user,"ADMIN_BOOTSTRAPPED")
    print("Administrator created. Configure categories, boundaries, offices, routing rules and SLA policies.")
if __name__=="__main__":bootstrap()

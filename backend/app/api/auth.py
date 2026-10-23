from datetime import timedelta
import hashlib,secrets
from pydantic import ValidationError
from fastapi import APIRouter,Depends,HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from app.core.db import get_db
from app.core.config import settings
from app.core.security import hasher,token_for,current_user
from app.models.entities import User,UserRole,CitizenProfile,AuthToken,now
from app.schemas.contracts import Register,Login,AuthOut,AuthRequest,TokenUse,Message,UserOut,ProfileEdit
from app.services.audit import audit
from app.services.notifications import deliver_email
router=APIRouter(tags=["Authentication"])

def issue_login(db,email,password):
    user=db.scalar(select(User).where(User.email==str(email).lower()))
    dummy="$argon2id$v=19$m=65536,t=3,p=4$Y0NPYnpsVm9PNStPYnpPdg$RMmaP/K0GSFv3QI2Fuap1uSJjxyhhPFV1JW3mLQ72R0"
    try: valid=hasher.verify(password,user.password_hash if user else dummy)
    except Exception: valid=False
    if not user or not user.active or not valid: raise HTTPException(401,"Email or password is incorrect")
    audit(db,user,"LOGIN")
    return {"access_token":token_for(user),"user":user}
@router.post("/auth/register",response_model=AuthOut,status_code=201)
def register(data:Register,db=Depends(get_db)):
    if db.scalar(select(User.id).where(User.email==str(data.email).lower())):raise HTTPException(409,"Account already exists")
    user=User(email=str(data.email).lower(),name=data.name,password_hash=hasher.hash(data.password))
    db.add(user);db.flush();db.add(UserRole(user_id=user.id,role_name="CITIZEN"));db.add(CitizenProfile(user_id=user.id))
    db.flush();db.refresh(user);audit(db,user,"REGISTER")
    return {"access_token":token_for(user),"user":user}
@router.post("/auth/login",response_model=AuthOut)
def login(data:Login,db=Depends(get_db)):return issue_login(db,data.email,data.password)
@router.post("/auth/token",response_model=AuthOut)
def oauth_token(data:OAuth2PasswordRequestForm=Depends(),db=Depends(get_db)):return issue_login(db,data.username,data.password)
@router.post("/auth/logout",response_model=Message)
def logout(user=Depends(current_user),db=Depends(get_db)):
    user.session_version+=1;audit(db,user,"LOGOUT");return {"message":"All current sessions signed out"}
@router.get("/users/me",response_model=UserOut)
def me(user=Depends(current_user)):return user
@router.patch("/users/me",response_model=UserOut)
def profile(data:ProfileEdit,user=Depends(current_user),db=Depends(get_db)):
    old=user.name;user.name=data.name;audit(db,user,"PROFILE_UPDATED",previous={"name":old},current={"name":data.name});return user
@router.post("/auth/{purpose}/request",response_model=dict)
def request_token(purpose:str,data:AuthRequest,db=Depends(get_db)):
    if purpose not in {"reset","verify"}:raise HTTPException(404,"Not found")
    user=db.scalar(select(User).where(User.email==str(data.email).lower()))
    response={"message":"If the account exists, instructions have been issued"}
    if user and user.active:
        raw=secrets.token_urlsafe(32)
        db.add(AuthToken(user_id=user.id,digest=hashlib.sha256(raw.encode()).hexdigest(),purpose=purpose,expires_at=now()+timedelta(minutes=20)))
        audit(db,user,"AUTH_TOKEN_REQUESTED",current={"purpose":purpose})
        if settings().demo_mode:response["demo_token"]=raw
        else:
            if not settings().smtp_host:raise HTTPException(503,"Email delivery is not configured")
            deliver_email(user.email,"JANASEVA account instructions",f"Use this {purpose} token within 20 minutes: {raw}")
    return response
@router.post("/auth/{purpose}/confirm",response_model=Message)
def confirm(purpose:str,data:TokenUse,db=Depends(get_db)):
    if purpose not in {"reset","verify"}:raise HTTPException(404,"Not found")
    row=db.scalar(select(AuthToken).where(AuthToken.digest==hashlib.sha256(data.token.encode()).hexdigest(),
        AuthToken.purpose==purpose,AuthToken.used.is_(False),AuthToken.expires_at>now()).with_for_update())
    if not row:raise HTTPException(400,"Token is invalid or expired")
    user=db.get(User,row.user_id)
    if purpose=="reset":
        if not data.password:raise HTTPException(422,"New password is required")
        try:Register(name=user.name,email=user.email,password=data.password)
        except ValidationError:raise HTTPException(422,"Use at least 12 characters with upper case, lower case and a number")
        user.password_hash=hasher.hash(data.password);user.session_version+=1
    else:user.verified=True
    row.used=True;audit(db,user,"AUTH_TOKEN_CONFIRMED",current={"purpose":purpose})
    return {"message":"Account updated"}

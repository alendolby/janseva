from datetime import timedelta
import jwt
from pwdlib import PasswordHash
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.db import get_db
from app.models.entities import User, now
hasher = PasswordHash.recommended()
bearer = OAuth2PasswordBearer(tokenUrl="/api/auth/token")
def token_for(user):
    return jwt.encode({"sub": user.id, "v": user.session_version,
        "exp": now() + timedelta(minutes=settings().token_minutes), "iat": now(),
        "iss": "janaseva", "aud": "janaseva-api"}, settings().jwt_secret, algorithm="HS256")
def current_user(token: str = Depends(bearer), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, settings().jwt_secret, algorithms=["HS256"], audience="janaseva-api", issuer="janaseva")
        user = db.get(User, payload["sub"])
        if not user or not user.active or user.session_version != payload["v"]:
            raise ValueError()
        return user
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(401, "Session expired or invalid", headers={"WWW-Authenticate": "Bearer"})
def require(*roles):
    def check(user: User = Depends(current_user)):
        if user.role not in roles:
            raise HTTPException(403, "This action is not permitted for your role")
        return user
    return check

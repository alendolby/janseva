import logging
from fastapi import FastAPI,Request,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse,Response
from sqlalchemy.exc import IntegrityError,SQLAlchemyError
from sqlalchemy import text
from prometheus_client import generate_latest,CONTENT_TYPE_LATEST
from app.core.config import settings
from app.core.db import engine
from app.core.middleware import SecurityMiddleware
from app.api import auth,cases,system
logging.basicConfig(level=logging.INFO,format="%(message)s")
app=FastAPI(title="JANASEVA",version="1.0.0",description="Academic prototype. Demo boundaries, routing and SLA values are not government policy.")
app.add_middleware(SecurityMiddleware)
app.add_middleware(CORSMiddleware,allow_origins=settings().cors_origins.split(","),allow_credentials=False,
    allow_methods=["GET","POST","PATCH","PUT"],allow_headers=["Authorization","Content-Type"])
for router in [auth.router,cases.router,system.router]:app.include_router(router,prefix="/api")
@app.exception_handler(HTTPException)
async def http_error(request:Request,error:HTTPException):
    codes={401:"UNAUTHENTICATED",403:"FORBIDDEN",404:"NOT_FOUND",409:"CONFLICT",422:"VALIDATION_ERROR",413:"FILE_TOO_LARGE",503:"UNAVAILABLE"}
    return JSONResponse({"error":{"code":codes.get(error.status_code,"REQUEST_ERROR"),"message":str(error.detail)}},status_code=error.status_code,headers=error.headers)
@app.exception_handler(RequestValidationError)
async def validation_error(request:Request,error:RequestValidationError):
    return JSONResponse({"error":{"code":"VALIDATION_ERROR","message":"Check your input fields",
       "fields":[{"field":".".join(map(str,e["loc"])),"message":e["msg"]} for e in error.errors()]}},status_code=422)
@app.exception_handler(IntegrityError)
async def conflict(request:Request,error:IntegrityError):
    return JSONResponse({"error":{"code":"CONFLICT","message":"A duplicate record or invalid relationship was supplied"}},status_code=409)
@app.exception_handler(Exception)
async def unexpected(request:Request,error:Exception):
    logging.getLogger("janaseva").error('{"event":"unhandled_error"}')
    return JSONResponse({"error":{"code":"INTERNAL_ERROR","message":"The request could not be completed"}},status_code=500)
@app.get("/api/health",response_model=dict,tags=["Operations"])
def health():
    with engine.connect() as db:db.execute(text("SELECT 1"))
    return {"status":"ok","mode":"demo" if settings().demo_mode else "configured"}
@app.get("/metrics",include_in_schema=False)
def metrics():return Response(generate_latest(),media_type=CONTENT_TYPE_LATEST)

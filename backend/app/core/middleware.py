import time,logging,json,uuid
from collections import OrderedDict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from prometheus_client import Counter,Histogram
from app.core.config import settings
REQUESTS=Counter("janaseva_requests_total","HTTP responses",["method","status"])
LATENCY=Histogram("janaseva_request_seconds","Request duration")
logger=logging.getLogger("janaseva")
class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self,app):
        super().__init__(app);self.buckets=OrderedDict();self.redis=None
        if settings().rate_limit_backend=="redis":
            from redis import Redis
            self.redis=Redis.from_url(settings().redis_url)
    async def dispatch(self,request,call_next):
        begin=time.monotonic();window=int(time.time()//60);ip=request.client.host if request.client else "unknown"
        auth=request.url.path.startswith("/api/auth/");key=f"rl:{ip}:{auth}:{window}"
        maximum=20 if auth else settings().rate_limit
        if self.redis:
            try:
                count=self.redis.incr(key)
                if count==1:self.redis.expire(key,65)
            except Exception:
                return JSONResponse({"error":{"code":"RATE_LIMIT_UNAVAILABLE","message":"Please try again shortly"}},status_code=503)
        else:
            count=self.buckets.get(key,0)+1;self.buckets[key]=count
            if len(self.buckets)>10000:self.buckets.popitem(last=False)
        if count>maximum:return JSONResponse({"error":{"code":"RATE_LIMITED","message":"Too many requests. Try again in one minute"}},status_code=429,headers={"Retry-After":"60"})
        response=await call_next(request)
        response.headers.update({"X-Content-Type-Options":"nosniff","X-Frame-Options":"DENY","Referrer-Policy":"no-referrer","Cache-Control":"no-store","X-Request-ID":uuid.uuid4().hex})
        REQUESTS.labels(request.method,str(response.status_code)).inc();LATENCY.observe(time.monotonic()-begin)
        logger.info(json.dumps({"event":"http","method":request.method,"status":response.status_code,
          "duration_ms":round((time.monotonic()-begin)*1000,1)}))
        return response

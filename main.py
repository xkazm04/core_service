from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import database
import os
import uvicorn
from service_registry import ServiceRegistry
import logging
from prometheus_fastapi_instrumentator import Instrumentator
from contextlib import asynccontextmanager
import time
import json
from routes import api_router  
from fastapi.middleware.cors import CORSMiddleware
import threading
import signal
import sys
from datetime import datetime
import asyncio
from services.sse import background_task

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("core_service")

service_registry = ServiceRegistry()

@asynccontextmanager
async def lifespan(app: FastAPI):
    service_registry.register_service()
    service_registry.start_heartbeat()
    yield
    service_registry.deregister_service()
    
app = FastAPI(
    title="Core service",
    description="Core service",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(api_router, prefix="", tags=["Core"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

Instrumentator().instrument(app).expose(app)

# Global variables for health tracking
last_successful_request = datetime.now()
health_lock = threading.Lock()
RECOVERY_SECRET = os.getenv("RECOVERY_SECRET", "default-recovery-token")

# Modify the middleware to add timeouts
@app.middleware("http")
async def log_requests(request: Request, call_next):
    global last_successful_request
    
    headers = dict(request.headers)
    logger.info(f"Incoming request headers: {json.dumps(headers, default=str)}")
    
    allowed_paths = ["/health", "/metrics"]
    is_allowed_path = any(request.url.path.startswith(path) for path in allowed_paths)
    from_gateway = request.headers.get("X-From-Gateway") == "true"
    
    if not (from_gateway or is_allowed_path):
        logger.warning(f"Direct access attempt to {request.url.path} - Forbidden")
        return JSONResponse(status_code=403, content={"detail": "Direct access forbidden"})
    
    start_time = time.time()
    path = request.url.path
    method = request.method
    
    try:
        # Apply timeout to all requests
        request_timeout = 30.0  # 30 seconds default timeout
        
        # Customize timeout for specific endpoints that may take longer
        if "/generate" in path or "/process" in path:
            request_timeout = 120.0
        
        # Execute request with timeout
        response_task = asyncio.create_task(call_next(request))
        response = await asyncio.wait_for(response_task, timeout=request_timeout)
        
        # Update last successful request time on success
        if response.status_code < 500:
            with health_lock:
                last_successful_request = datetime.now()
        
        log_data = {
            "method": method,
            "path": path,
            "status_code": response.status_code,
            "processing_time_ms": round((time.time() - start_time) * 1000, 2)
        }
        logger.info(f"Request processed: {json.dumps(log_data)}")
        
        return response
    except asyncio.TimeoutError:
        logger.error(f"Request timed out: {method} {path}")
        return JSONResponse(
            status_code=504,
            content={"detail": "Request processing timed out"}
        )
    except Exception as e:
        log_data = {
            "method": method,
            "path": path,
            "error": str(e),
            "processing_time_ms": round((time.time() - start_time) * 1000, 2)
        }
        logger.error(f"Request error: {json.dumps(log_data)}")
        raise

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()
        

@app.get("/health")
def health_check():
    """Enhanced health check endpoint with deep checks"""
    global last_successful_request
    
    health_data = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "checks": {}
    }
    
    try:
        health_data["checks"]["database"] = {"status": "healthy"}
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        health_data["status"] = "unhealthy"
        health_data["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check last successful request
    with health_lock:
        time_since_last_success = (datetime.now() - last_successful_request).total_seconds()
        health_data["checks"]["activity"] = {
            "last_success_seconds_ago": time_since_last_success,
            "status": "healthy" if time_since_last_success < 300 else "warning"
        }
    
    # Check system resources
    import psutil
    try:
        health_data["checks"]["system"] = {
            "memory_percent": psutil.virtual_memory().percent,
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "status": "healthy"
        }
        if health_data["checks"]["system"]["memory_percent"] > 90:
            health_data["checks"]["system"]["status"] = "warning"
    except:
        health_data["checks"]["system"] = {"status": "unknown"}
    
    # Determine overall status
    if any(check["status"] == "unhealthy" for check in health_data["checks"].values()):
        health_data["status"] = "unhealthy"
        return JSONResponse(status_code=503, content=health_data)
    
    return health_data

    
@app.on_event("startup")
def startup_db_client():
    database.Base.metadata.create_all(bind=database.engine)
    logger.info("Database tables created")

# Add a self-recovery endpoint
@app.post("/health/restart")
async def trigger_restart(request: Request):
    # Security check - only accept requests from gateway with proper token
    if (request.headers.get("X-From-Gateway") != "true" or 
        request.headers.get("X-Recovery-Token") != RECOVERY_SECRET):
        raise HTTPException(status_code=403, detail="Unauthorized restart request")
    
    logger.warning("Received restart signal from API Gateway")
    
    import subprocess
    subprocess.Popen([sys.executable] + sys.argv)
    os.kill(os.getpid(), signal.SIGTERM)
    return {"status": "restarting"}

@app.on_event("startup")
async def start_background_tasks():
    # Start SSE background task
    asyncio.create_task(background_task())
    


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
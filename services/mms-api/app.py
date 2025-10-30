from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import redis

# ─────────────────────────────────────────────────────────────
# ✅ Route Imports
# ─────────────────────────────────────────────────────────────
from routes import config, exports, tolerances

# ─────────────────────────────────────────────────────────────
# ✅ FastAPI Initialization
# ─────────────────────────────────────────────────────────────
app = FastAPI()
logging.basicConfig(level=logging.INFO)

# ─────────────────────────────────────────────────────────────
# ✅ CORS Middleware
# ─────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────
# ✅ Redis Connection
# ─────────────────────────────────────────────────────────────
REDIS_HOST = "redis"
REDIS_PORT = 6379
REDIS_DB = 0

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

# ─────────────────────────────────────────────────────────────
# ✅ Route Registration
# ─────────────────────────────────────────────────────────────
app.include_router(config.router)
app.include_router(exports.router)
app.include_router(tolerances.router, prefix="/v1/model")

# ─────────────────────────────────────────────────────────────
# ✅ Health Check
# ─────────────────────────────────────────────────────────────
@app.get("/")
def health_check():
    logging.info("[MMS-API] 🟢 Health check requested")
    return {"status": "MMS API is running"}

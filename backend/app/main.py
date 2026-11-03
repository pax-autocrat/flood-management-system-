from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings, PROJECT_ROOT
from app.database import engine, Base, SessionLocal
from app.seed_data import seed_database
from app.routers import auth, weather, hotspots, fleet, sos, routes

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite tables and seed data on startup
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Real-Time Civic Flood Management & Rescue Platform for Gurugram / NCR",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(weather.router, prefix=settings.API_PREFIX)
app.include_router(hotspots.router, prefix=settings.API_PREFIX)
app.include_router(fleet.router, prefix=settings.API_PREFIX)
app.include_router(sos.router, prefix=settings.API_PREFIX)
app.include_router(routes.router, prefix=settings.API_PREFIX)

@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "api_docs": "/docs"
    }

# Serve root HTML application
HTML_FILE_PATH = PROJECT_ROOT / "index.html"

@app.get("/", tags=["Frontend"])
def serve_index_html():
    if HTML_FILE_PATH.exists():
        return FileResponse(HTML_FILE_PATH)
    return {"message": "index.html not found at project root"}

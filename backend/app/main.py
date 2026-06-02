from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.database import Base
from app.core.database import engine as db_engine

# Create database tables
Base.metadata.create_all(bind=db_engine)

app = FastAPI(
    title="DataWeaver API", description="Low-code Excel automation platform", version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root & Health check
@app.get("/")
@app.get("/health")
def health():
    return {"status": "healthy", "service": "DataWeaver API"}


# Include consolidated router
app.include_router(api_router, prefix="/api/v1")

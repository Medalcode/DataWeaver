from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine as db_engine
from app.routes import auth, workflows, files, executions

# Create database tables
Base.metadata.create_all(bind=db_engine)

app = FastAPI(
    title="Macro Builder API",
    description="Low-code Excel automation platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/")
def root():
    return {"status": "ok", "service": "Macro Builder API"}


@app.get("/health")
def health():
    return {"status": "healthy"}


# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(workflows.router, prefix="/api/v1")
app.include_router(files.router, prefix="/api/v1")
app.include_router(executions.router, prefix="/api/v1")

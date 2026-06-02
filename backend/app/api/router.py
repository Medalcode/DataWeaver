from fastapi import APIRouter

from app.api.endpoints import auth, executions, files, workflows

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(executions.router)
api_router.include_router(files.router)
api_router.include_router(workflows.router)

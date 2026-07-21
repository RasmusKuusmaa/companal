"""Aggregates all v1 domain routers under a single APIRouter."""

from fastapi import APIRouter

from app.api.v1 import health
from app.domains.analysis.router import router as analysis_router
from app.domains.auth.router import router as auth_router
from app.domains.projects.router import router as projects_router

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth_router)
api_router.include_router(projects_router)
api_router.include_router(analysis_router)

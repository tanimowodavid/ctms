from fastapi import APIRouter

from app.api.v1.endpoints import applications, auth, cohorts, health, profiles

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(profiles.router)
api_router.include_router(cohorts.router)
api_router.include_router(applications.router)
api_router.include_router(applications.admin_router)

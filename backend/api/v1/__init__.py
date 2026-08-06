from fastapi import APIRouter

from backend.api.v1 import auth, cases, dashboard, evidence, intelligence, tasks, users, whatsapp

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(dashboard.router)
api_router.include_router(cases.router)
api_router.include_router(tasks.router)
api_router.include_router(whatsapp.router)
api_router.include_router(evidence.router)
api_router.include_router(intelligence.router)

from fastapi import FastAPI
from app.core.config import settings
from app.api.v1 import routes_case, routes_evidence, routes_analytics, routes_investigators, routes_reporting, websockets
from app.core.audit_middleware import AuditMiddleware
from app.models import Base
from app.core.database import engine

# Create database tables automatically
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="WhatsApp Investigation Intelligence Platform API",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json"
)

# Add Security/Audit Middleware
app.add_middleware(AuditMiddleware)

app.include_router(routes_case.router, prefix="/api/v1/cases", tags=["cases"])
app.include_router(routes_investigators.router, prefix="/api/v1/investigators", tags=["investigators"])
app.include_router(routes_evidence.router, prefix="/api/v1", tags=["evidence"])
app.include_router(routes_analytics.router, prefix="/api/v1", tags=["analytics"])
app.include_router(routes_reporting.router, prefix="/api/v1/cases", tags=["reporting"])
app.include_router(websockets.router, tags=["websockets"])

@app.get("/")
def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME} API"}

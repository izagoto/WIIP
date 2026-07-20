import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.audit import AuditLog

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        path = request.url.path
        
        if path.startswith("/api/v1"):
            action = f"{request.method} {path}"

            client_ip = request.client.host if request.client else "unknown"
            
            investigator_id_str = request.headers.get("X-Investigator-ID", "1")
            try:
                investigator_id = int(investigator_id_str)
            except ValueError:
                investigator_id = 1
                
            db: Session = SessionLocal()
            try:
                log_entry = AuditLog(
                    investigator_id=investigator_id,
                    action=action,
                    resource_path=path,
                    details=f"IP: {client_ip} | Status: {response.status_code}"
                )
                db.add(log_entry)
                db.commit()
            except Exception as e:
                print(f"Audit log failed: {str(e)}")
            finally:
                db.close()
                
        return response

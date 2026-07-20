from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@router.websocket("/ws/tracking")
async def websocket_tracking_endpoint(websocket: WebSocket):
    """
    Real-time websocket endpoint.
    Frontend can connect here to receive live updates when a background parsing task
    completes, or when new evidence is fully digested.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive, wait for client messages if any
            data = await websocket.receive_text()
            # For this MVP, we just echo or acknowledge
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        
# A helper function that can be called from Celery tasks or API routes
async def notify_clients(message: str):
    await manager.broadcast(message)

"""WebSocket endpoint for real-time detection streaming."""

import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

connected_clients: set[WebSocket] = set()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_clients.discard(websocket)


async def broadcast(message: dict):
    data = json.dumps(message)
    for client in list(connected_clients):
        try:
            await client.send_text(data)
        except Exception:
            connected_clients.discard(client)

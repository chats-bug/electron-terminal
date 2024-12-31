# main.py
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
from typing import Dict, Optional
import uuid

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConnectionManager:
    def __init__(self) -> None:
        # Replace single connection with dictionary of connections
        self.active_connections: Dict[str, WebSocket] = {}
        self.response_queues: Dict[str, asyncio.Queue] = {}

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def receive_messages(self, client_id: str) -> None:
        try:
            while True:
                if client_id in self.active_connections:
                    response = await self.active_connections[client_id].receive_json()
                    request_id = response.get("id")
                    if request_id and request_id in self.response_queues:
                        await self.response_queues[request_id].put(response)
        except:
            self.disconnect(client_id)

    async def send_command(self, command: str, request_id: str, client_id: str) -> Dict:
        if client_id not in self.active_connections:
            raise Exception(f"No active connection for client {client_id}")

        self.response_queues[request_id] = asyncio.Queue()

        await self.active_connections[client_id].send_json(
            {"command": command, "id": request_id}
        )

        try:
            response = await self.response_queues[request_id].get()
            return response
        finally:
            del self.response_queues[request_id]


manager = ConnectionManager()


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str) -> None:
    await manager.connect(websocket, client_id)
    await manager.receive_messages(client_id)


@app.post("/execute/{client_id}")
async def execute_command(command: dict, client_id: str) -> Dict:
    try:
        request_id = str(uuid.uuid4())
        response = await manager.send_command(command["command"], request_id, client_id)
        return {"result": response}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

# main.py
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
from typing import Dict, Optional
import uuid
import logging

app = FastAPI()
logger = logging.getLogger("uvicorn.error")

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
        logger.info(f"Client {client_id} connected")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} no longer connected")

    async def receive_messages(self, client_id: str) -> None:
        try:
            while True:
                if client_id in self.active_connections:
                    response = await self.active_connections[client_id].receive_json()
                    request_id = response.get("id")
                    if request_id and request_id in self.response_queues:
                        logger.info(
                            f"Received message from client {client_id} for request {request_id}"
                        )
                        await self.response_queues[request_id].put(response)
        except:
            logger.error(f"Client {client_id} no longer connected")
            self.disconnect(client_id)

    async def send_command(self, command: str, request_id: str, client_id: str) -> Dict:
        if client_id not in self.active_connections:
            logger.error(f"No active connection for client {client_id}")
            raise Exception(f"No active connection for client {client_id}")

        logger.info(f"Sending command to client {client_id}: {command}")
        self.response_queues[request_id] = asyncio.Queue()

        await self.active_connections[client_id].send_json(
            {"command": command, "id": request_id}
        )

        try:
            response = await self.response_queues[request_id].get()
            logger.info(
                f"Received response from client {client_id}: {str(response)[:20]}..."
            )
            return response
        finally:
            logger.info(f"Deleting response queue for client {client_id}")
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
        logger.info(f"Executed command: {command['command']}")
        return {"result": response}
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

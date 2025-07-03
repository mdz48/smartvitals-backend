from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import logging

wsRouter = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.main_event_loop = None  # Permite guardar el event loop principal

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logging.info(f"Cliente WebSocket conectado. Total conexiones: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logging.info(f"Cliente WebSocket desconectado. Total conexiones: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        if not self.active_connections:
            logging.info("No hay conexiones WebSocket activas para enviar mensaje")
            return
            
        logging.info(f"Enviando mensaje a {len(self.active_connections)} clientes WebSocket: {message}")
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logging.error(f"Error enviando mensaje a cliente WebSocket: {e}")
                # Remover conexión problemática
                self.active_connections.remove(connection)

manager = ConnectionManager()

@wsRouter.websocket("/ws/sensores")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # Mantén la conexión viva, pero no procesamos mensajes del cliente
    except WebSocketDisconnect:
        manager.disconnect(websocket)
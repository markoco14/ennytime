"""Websocket manager for chat application."""

from fastapi import WebSocket


class WebSocketConnectionManager:
    """Manages WebSocket connections throughout the application."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.chatroom_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

    # chat room related methods
    async def connect_chatroom(
            self,
            websocket: WebSocket,
            room_id: str,
            user_id: int
    ):
        await websocket.accept()
        if room_id not in self.chatroom_connections:
            self.chatroom_connections[room_id] = []
        self.chatroom_connections[room_id].append({
            "user_id": user_id,
            "connection": websocket
        })

    async def disconnect_chatroom(
            self,
            websocket: WebSocket,
            room_id: str
    ):
        self.chatroom_connections[room_id] = [
            connection for connection in self.chatroom_connections[room_id]
            if connection["connection"] != websocket
        ]
        if not self.chatroom_connections[room_id]:
            del self.chatroom_connections[room_id]

    async def broadcast_chatroom(
            self,
            message: str,
            room_id: str
    ):
        if room_id in self.chatroom_connections:
            for connection in self.chatroom_connections[room_id]:
                try:
                    await connection["connection"].send_text(message)
                except RuntimeError as e:
                    # TODO: change to logging
                    print(f"Error sending message to connection: {e}")
                    self.chatroom_connections[room_id].remove(connection)


websocket_manager = WebSocketConnectionManager()

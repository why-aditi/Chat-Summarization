from typing import Dict, Set
from fastapi import WebSocket
from ..models.chat import ChatMessage
from .gemini_service import gemini_service

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, conversation_id: str):
        await websocket.accept()
        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = set()
        self.active_connections[conversation_id].add(websocket)

    def disconnect(self, websocket: WebSocket, conversation_id: str):
        if conversation_id in self.active_connections:
            self.active_connections[conversation_id].remove(websocket)
            if not self.active_connections[conversation_id]:
                del self.active_connections[conversation_id]

    async def broadcast_message(self, message: ChatMessage, conversation_id: str):
        if conversation_id in self.active_connections:
            # Get sentiment and keywords analysis
            sentiment, keywords = await gemini_service.analyze_sentiment_and_keywords([message])
            
            # Prepare the message with insights
            message_data = {
                "message": message.model_dump(),
                "insights": {
                    "sentiment": sentiment,
                    "keywords": keywords
                }
            }
            
            # Broadcast to all connected clients in the conversation
            for connection in self.active_connections[conversation_id]:
                try:
                    await connection.send_json(message_data)
                except:
                    # Remove dead connections
                    self.disconnect(connection, conversation_id)

websocket_manager = WebSocketManager()
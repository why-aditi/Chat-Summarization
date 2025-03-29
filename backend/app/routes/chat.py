from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from typing import List, Optional
from datetime import datetime
from ..models.chat import ChatMessage, ChatSummary, ChatSummarizeRequest, PaginatedResponse
from ..services.chat_service import chat_service

router = APIRouter(prefix="/chats", tags=["chats"])

@router.post("", response_model=ChatMessage)
async def create_chat_message(message: ChatMessage):
    try:
        return await chat_service.create_message(message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{conversation_id}", response_model=List[ChatMessage])
async def get_conversation(
    conversation_id: str,
    search_query: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    try:
        messages = await chat_service.get_message(
            conversation_id,
            search_query=search_query,
            start_date=start_date,
            end_date=end_date
        )
        return messages
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/{user_id}/messages", response_model=PaginatedResponse)
async def get_user_messages(
    user_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    try:
        return await chat_service.get_user_messages(user_id, page, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/summarize", response_model=ChatSummary)
async def summarize_chat(request: ChatSummarizeRequest):
    try:
        return await chat_service.summarize_conversation(
            request.conversation_id,
            request.include_sentiment,
            request.include_keywords
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str):
    try:
        success = await chat_service.delete_message(conversation_id)
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return {"message": "Conversation deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for real-time chat
@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Create chat message
            message = ChatMessage(**data)
            saved_message = await chat_service.create_message(message)
            
            # Send confirmation back to client
            await websocket.send_json(saved_message.model_dump())
    except WebSocketDisconnect:
        await websocket.close()
    except Exception as e:
        await websocket.close(code=1001, reason=str(e))
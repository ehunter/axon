"""Chat API endpoints with SSE streaming."""

import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from axon.agent.chat_with_tools import StreamEventType, ToolBasedChatAgent
from axon.api.dependencies import get_db
from axon.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""
    message: str
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    """Response for non-streaming chat."""
    response: str
    conversation_id: str


async def stream_chat_response(
    agent: ToolBasedChatAgent,
    message: str,
) -> AsyncGenerator[str, None]:
    """Stream chat response as Server-Sent Events."""
    try:
        async for event in agent.chat_stream(message):
            # Format as SSE
            data = {
                "type": event.type.value,
                "content": event.content,
            }
            if event.tool_input:
                data["tool_input"] = event.tool_input
            
            yield f"data: {json.dumps(data)}\n\n"
            
    except Exception as e:
        logger.exception("Error during chat stream")
        error_data = {"type": "error", "content": str(e)}
        yield f"data: {json.dumps(error_data)}\n\n"


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Stream a chat response using Server-Sent Events.
    
    Returns SSE stream with events:
    - type: "text" - Text chunk from response
    - type: "tool_start" - Tool execution starting
    - type: "tool_end" - Tool execution completed  
    - type: "done" - Stream complete
    - type: "error" - Error occurred
    """
    settings = get_settings()
    
    if not settings.anthropic_api_key:
        raise HTTPException(
            status_code=503,
            detail="Chat unavailable: Anthropic API key not configured"
        )
    
    # Create agent
    agent = ToolBasedChatAgent(
        db_session=db,
        anthropic_api_key=settings.anthropic_api_key,
        embedding_api_key=settings.openai_api_key,
    )
    
    # TODO: Load existing conversation if conversation_id provided
    
    return StreamingResponse(
        stream_chat_response(agent, request.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """Send a chat message and get a complete response (non-streaming)."""
    settings = get_settings()
    
    if not settings.anthropic_api_key:
        raise HTTPException(
            status_code=503,
            detail="Chat unavailable: Anthropic API key not configured"
        )
    
    # Create agent
    agent = ToolBasedChatAgent(
        db_session=db,
        anthropic_api_key=settings.anthropic_api_key,
        embedding_api_key=settings.openai_api_key,
    )
    
    # TODO: Load existing conversation if conversation_id provided
    
    try:
        response = await agent.chat(request.message)
        return ChatResponse(
            response=response,
            conversation_id=agent.conversation.id,
        )
    except Exception as e:
        logger.exception("Error during chat")
        raise HTTPException(status_code=500, detail=str(e))


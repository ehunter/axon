"""Chat API endpoints with SSE streaming."""

import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from axon.agent.chat_with_tools import StreamEventType, ToolBasedChatAgent
from axon.agent.persistence import ConversationService
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
    conversation_id: str | None,
) -> AsyncGenerator[str, None]:
    """Stream chat response as Server-Sent Events."""
    try:
        # Track if we've sent conversation_id yet
        sent_conversation_id = False
        
        async for event in agent.chat_stream(message):
            # Send conversation_id on first event (agent creates/loads it before first event)
            if not sent_conversation_id and agent._db_conversation_id:
                yield f"data: {json.dumps({'type': 'conversation_id', 'content': agent._db_conversation_id})}\n\n"
                sent_conversation_id = True
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
    - type: "conversation_id" - The conversation ID (sent first)
    - type: "text" - Text chunk from response
    - type: "tool_start" - Tool execution starting
    - type: "tool_end" - Tool execution completed  
    - type: "done" - Stream complete
    - type: "error" - Error occurred
    """
    settings = get_settings()
    
    logger.info(f"Chat stream request - message: {request.message[:50]}..., conversation_id: {request.conversation_id} (type: {type(request.conversation_id).__name__})")
    
    if not settings.anthropic_api_key:
        raise HTTPException(
            status_code=503,
            detail="Chat unavailable: Anthropic API key not configured"
        )
    
    # Create persistence service for conversation state
    persistence_service = ConversationService(db)
    
    # Create agent with persistence (like CLI does)
    agent = ToolBasedChatAgent(
        db_session=db,
        anthropic_api_key=settings.anthropic_api_key,
        embedding_api_key=settings.openai_api_key,
        persistence_service=persistence_service,
    )
    
    # Load existing conversation if conversation_id provided
    if request.conversation_id:
        try:
            success = await agent.load_conversation(request.conversation_id)
            if success:
                msg_count = len(agent.conversation.messages) if agent.conversation else 0
                logger.info(f"Loaded conversation {request.conversation_id} with {msg_count} messages")
            else:
                logger.warning(f"Failed to load conversation {request.conversation_id}")
        except Exception as e:
            logger.warning(f"Could not load conversation {request.conversation_id}: {e}")
            # Continue with new conversation if load fails
    
    # Get conversation ID - use database ID if available, otherwise will be created during chat_stream
    conversation_id = agent._db_conversation_id
    logger.info(f"Starting chat - conversation_id: {conversation_id} (will be created if new)")
    
    return StreamingResponse(
        stream_chat_response(agent, request.message, conversation_id),
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
    
    # Create persistence service for conversation state
    persistence_service = ConversationService(db)
    
    # Create agent with persistence (like CLI does)
    agent = ToolBasedChatAgent(
        db_session=db,
        anthropic_api_key=settings.anthropic_api_key,
        embedding_api_key=settings.openai_api_key,
        persistence_service=persistence_service,
    )
    
    # Load existing conversation if conversation_id provided
    if request.conversation_id:
        try:
            await agent.load_conversation(request.conversation_id)
            logger.info(f"Loaded conversation: {request.conversation_id}")
        except Exception as e:
            logger.warning(f"Could not load conversation {request.conversation_id}: {e}")
            # Continue with new conversation if load fails
    
    try:
        response = await agent.chat(request.message)
        return ChatResponse(
            response=response,
            conversation_id=agent.conversation.id,
        )
    except Exception as e:
        logger.exception("Error during chat")
        raise HTTPException(status_code=500, detail=str(e))


class ConversationListItem(BaseModel):
    """Single conversation in list response."""
    id: str
    title: str | None
    message_count: int
    created_at: str
    updated_at: str


class ConversationsResponse(BaseModel):
    """Response for list conversations."""
    conversations: list[ConversationListItem]


class MessageItem(BaseModel):
    """Single message in conversation."""
    id: str
    role: str
    content: str
    created_at: str


class ConversationDetailResponse(BaseModel):
    """Response for single conversation with messages."""
    id: str
    title: str | None
    messages: list[MessageItem]
    created_at: str
    updated_at: str


@router.get("/conversations", response_model=ConversationsResponse)
async def list_conversations(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
) -> ConversationsResponse:
    """List recent conversations.
    
    Args:
        limit: Maximum number of conversations to return (default 20)
        
    Returns:
        List of conversations with metadata
    """
    persistence_service = ConversationService(db)
    
    conversations = await persistence_service.list_conversations(limit=limit)
    
    return ConversationsResponse(
        conversations=[
            ConversationListItem(
                id=conv.id,
                title=conv.title,
                message_count=conv.message_count,
                created_at=conv.created_at.isoformat(),
                updated_at=conv.updated_at.isoformat(),
            )
            for conv in conversations
        ]
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
) -> ConversationDetailResponse:
    """Get a specific conversation with its messages.
    
    Args:
        conversation_id: The conversation ID to load
        
    Returns:
        Conversation details with all messages
    """
    persistence_service = ConversationService(db)
    
    conversation = await persistence_service.load_conversation(conversation_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return ConversationDetailResponse(
        id=conversation.id,
        title=conversation.title,
        messages=[
            MessageItem(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at.isoformat(),
            )
            for msg in conversation.messages
        ],
        created_at=conversation.created_at.isoformat(),
        updated_at=conversation.updated_at.isoformat(),
    )

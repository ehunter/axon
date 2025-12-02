"""Conversation persistence service.

Handles saving and loading conversations to/from the database,
enabling users to resume previous sessions.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from axon.db.models import Conversation, Message, ConversationSample
from axon.agent.tools import SampleSelection, SelectedSample


@dataclass
class MessageData:
    """Data class for message information."""
    id: str
    role: str
    content: str
    created_at: datetime


@dataclass
class ConversationData:
    """Data class for conversation information."""
    id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    message_count: int
    messages: list[MessageData] = None
    
    def __post_init__(self):
        if self.messages is None:
            self.messages = []


def generate_title_from_message(message: str, max_length: int = 100) -> str:
    """Generate a conversation title from the first user message.
    
    Args:
        message: The user's message
        max_length: Maximum title length
        
    Returns:
        A title string
    """
    if not message or not message.strip():
        return "New Conversation"
    
    # Clean and truncate
    title = message.strip()
    
    # Take first line only
    if "\n" in title:
        title = title.split("\n")[0]
    
    # Truncate if needed
    if len(title) > max_length:
        # Try to truncate at a word boundary
        truncated = title[:max_length - 3]
        last_space = truncated.rfind(" ")
        if last_space > max_length // 2:
            title = truncated[:last_space] + "..."
        else:
            title = truncated + "..."
    
    return title


class ConversationService:
    """Service for persisting conversations to the database.
    
    Provides methods for creating, loading, and listing conversations,
    as well as adding messages to existing conversations.
    """
    
    def __init__(self, db_session: AsyncSession):
        """Initialize the service with a database session.
        
        Args:
            db_session: SQLAlchemy async session
        """
        self.db_session = db_session
    
    async def create_conversation(self, title: Optional[str] = None) -> str:
        """Create a new conversation.
        
        Args:
            title: Optional title for the conversation
            
        Returns:
            The new conversation's ID
        """
        conversation = Conversation(
            id=str(uuid4()),
            title=title,
        )
        
        self.db_session.add(conversation)
        await self.db_session.commit()
        await self.db_session.refresh(conversation)
        
        return conversation.id
    
    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
    ) -> str:
        """Add a message to a conversation.
        
        Args:
            conversation_id: The conversation ID
            role: Message role ('user' or 'assistant')
            content: Message content
            
        Returns:
            The new message's ID
        """
        message = Message(
            id=str(uuid4()),
            conversation_id=conversation_id,
            role=role,
            content=content,
        )
        
        self.db_session.add(message)
        await self.db_session.commit()
        await self.db_session.refresh(message)
        
        return message.id
    
    async def load_conversation(self, conversation_id: str) -> Optional[ConversationData]:
        """Load a conversation with its messages.
        
        Args:
            conversation_id: The conversation ID to load
            
        Returns:
            ConversationData if found, None otherwise
        """
        query = (
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .options(selectinload(Conversation.messages))
        )
        
        result = await self.db_session.execute(query)
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            return None
        
        # Convert to data class
        messages = [
            MessageData(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at,
            )
            for msg in sorted(conversation.messages, key=lambda m: m.created_at)
        ]
        
        return ConversationData(
            id=conversation.id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            message_count=len(messages),
            messages=messages,
        )
    
    async def list_conversations(self, limit: int = 20) -> list[ConversationData]:
        """List recent conversations.
        
        Args:
            limit: Maximum number of conversations to return
            
        Returns:
            List of ConversationData objects (without full messages)
        """
        query = (
            select(Conversation)
            .order_by(desc(Conversation.updated_at))
            .limit(limit)
        )
        
        result = await self.db_session.execute(query)
        conversations = result.scalars().all()
        
        # Get message counts efficiently
        data_list = []
        for conv in conversations:
            # Count messages for this conversation
            count_query = (
                select(Message.id)
                .where(Message.conversation_id == conv.id)
            )
            count_result = await self.db_session.execute(count_query)
            message_count = len(count_result.scalars().all())
            
            data_list.append(ConversationData(
                id=conv.id,
                title=conv.title,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                message_count=message_count,
            ))
        
        return data_list
    
    async def update_title(self, conversation_id: str, title: str) -> bool:
        """Update a conversation's title.
        
        Args:
            conversation_id: The conversation ID
            title: New title
            
        Returns:
            True if successful, False if conversation not found
        """
        query = select(Conversation).where(Conversation.id == conversation_id)
        result = await self.db_session.execute(query)
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            return False
        
        conversation.title = title
        await self.db_session.commit()
        
        return True
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and its messages.
        
        Args:
            conversation_id: The conversation ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        query = select(Conversation).where(Conversation.id == conversation_id)
        result = await self.db_session.execute(query)
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            return False
        
        await self.db_session.delete(conversation)
        await self.db_session.commit()
        
        return True
    
    # === Sample Selection Persistence Methods ===
    
    async def save_sample_to_selection(
        self,
        conversation_id: str,
        sample_external_id: str,
        sample_group: str,
        diagnosis: Optional[str] = None,
        age: Optional[int] = None,
        sex: Optional[str] = None,
        source_bank: Optional[str] = None,
    ) -> bool:
        """Save a sample to the conversation's selection.
        
        Args:
            conversation_id: The conversation ID
            sample_external_id: The sample's external ID
            sample_group: 'case' or 'control'
            diagnosis: Optional diagnosis to cache
            age: Optional age to cache
            sex: Optional sex to cache
            source_bank: Optional source bank to cache
            
        Returns:
            True if saved, False if already exists or error
        """
        try:
            # Check if sample already exists in this conversation
            existing = await self.db_session.execute(
                select(ConversationSample).where(
                    ConversationSample.conversation_id == conversation_id,
                    ConversationSample.sample_external_id == sample_external_id,
                )
            )
            if existing.scalar_one_or_none():
                return False
            
            sample = ConversationSample(
                id=str(uuid4()),
                conversation_id=conversation_id,
                sample_external_id=sample_external_id,
                sample_group=sample_group,
                diagnosis=diagnosis,
                age=age,
                sex=sex,
                source_bank=source_bank,
            )
            
            self.db_session.add(sample)
            await self.db_session.commit()
            
            return True
        except Exception:
            # Table might not exist - rollback and return False
            await self.db_session.rollback()
            return False
    
    async def remove_sample_from_selection(
        self,
        conversation_id: str,
        sample_external_id: str,
    ) -> bool:
        """Remove a sample from the conversation's selection.
        
        Args:
            conversation_id: The conversation ID
            sample_external_id: The sample's external ID to remove
            
        Returns:
            True if removed, False if not found or error
        """
        try:
            result = await self.db_session.execute(
                select(ConversationSample).where(
                    ConversationSample.conversation_id == conversation_id,
                    ConversationSample.sample_external_id == sample_external_id,
                )
            )
            sample = result.scalar_one_or_none()
            
            if not sample:
                return False
            
            await self.db_session.delete(sample)
            await self.db_session.commit()
            return True
        except Exception:
            await self.db_session.rollback()
            return False
    
    async def load_selection(self, conversation_id: str) -> SampleSelection:
        """Load the sample selection for a conversation.
        
        Args:
            conversation_id: The conversation ID
            
        Returns:
            SampleSelection with restored cases and controls (empty if error)
        """
        selection = SampleSelection()
        
        try:
            result = await self.db_session.execute(
                select(ConversationSample).where(
                    ConversationSample.conversation_id == conversation_id
                )
            )
            samples = result.scalars().all()
            
            for sample in samples:
                selected = SelectedSample(
                    id=sample.id,
                    external_id=sample.sample_external_id,
                    diagnosis=sample.diagnosis,
                    age=sample.age,
                    sex=sample.sex,
                    rin=None,  # Not cached
                    pmi=None,  # Not cached
                    brain_region=None,  # Not cached
                    source_bank=sample.source_bank,
                    braak_stage=None,  # Not cached
                )
                
                if sample.sample_group == "case":
                    selection.cases.append(selected)
                elif sample.sample_group == "control":
                    selection.controls.append(selected)
        except Exception:
            # Table might not exist - return empty selection
            await self.db_session.rollback()
        
        return selection
    
    async def clear_selection(self, conversation_id: str) -> bool:
        """Clear all samples from the conversation's selection.
        
        Args:
            conversation_id: The conversation ID
            
        Returns:
            True if successful, False on error
        """
        try:
            result = await self.db_session.execute(
                select(ConversationSample).where(
                    ConversationSample.conversation_id == conversation_id
                )
            )
            samples = result.scalars().all()
            
            for sample in samples:
                await self.db_session.delete(sample)
            
            await self.db_session.commit()
            
            return True
        except Exception:
            await self.db_session.rollback()
            return False
    
    async def get_selection_summary(self, conversation_id: str) -> dict:
        """Get a summary of the sample selection counts.
        
        Args:
            conversation_id: The conversation ID
            
        Returns:
            Dict with case_count, control_count, and total (zeros on error)
        """
        try:
            result = await self.db_session.execute(
                select(ConversationSample).where(
                    ConversationSample.conversation_id == conversation_id
                )
            )
            samples = result.scalars().all()
            
            case_count = sum(1 for s in samples if s.sample_group == "case")
            control_count = sum(1 for s in samples if s.sample_group == "control")
            
            return {
                "case_count": case_count,
                "control_count": control_count,
                "total": case_count + control_count,
            }
        except Exception:
            await self.db_session.rollback()
            return {
                "case_count": 0,
                "control_count": 0,
                "total": 0,
            }


"""SQLAlchemy database models for Axon.

This module defines all database models for the brain bank discovery system.
Models support multi-source data integration with flexible schema design.
"""

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

try:
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False
    Vector = None  # type: ignore


class Base(DeclarativeBase):
    """Base class for all models."""

    type_annotation_map = {
        dict[str, Any]: JSON,
        list[dict[str, Any]]: JSON,
        list[str]: JSON,
    }


class DataSource(Base):
    """Track data source configurations and sync status."""

    __tablename__ = "data_sources"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)

    # Source metadata
    website_url: Mapped[str | None] = mapped_column(String(500))
    contact_email: Mapped[str | None] = mapped_column(String(255))
    data_format: Mapped[str | None] = mapped_column(String(50))

    # Sync tracking
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime)
    last_sync_status: Mapped[str | None] = mapped_column(String(50))
    total_samples: Mapped[int] = mapped_column(Integer, default=0)

    # Configuration
    adapter_class: Mapped[str | None] = mapped_column(String(200))
    config: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    characteristics: Mapped[list["SourceCharacteristic"]] = relationship(
        "SourceCharacteristic", back_populates="source", cascade="all, delete-orphan"
    )


class SourceCharacteristic(Base):
    """Source characteristics for agent intelligence."""

    __tablename__ = "source_characteristics"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False
    )

    category: Mapped[str] = mapped_column(String(100), nullable=False)
    characteristic: Mapped[str] = mapped_column(Text, nullable=False)
    agent_guidance: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    source: Mapped["DataSource"] = relationship(
        "DataSource", back_populates="characteristics"
    )


class Sample(Base):
    """Brain tissue samples from all sources."""

    __tablename__ = "samples"
    __table_args__ = (
        UniqueConstraint("source_bank", "external_id", name="uq_sample_source_external"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )

    # Source tracking
    source_bank: Mapped[str] = mapped_column(String(100), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(500))

    # Donor Demographics
    donor_age: Mapped[int | None] = mapped_column(Integer)
    donor_age_range: Mapped[str | None] = mapped_column(String(50))
    donor_sex: Mapped[str | None] = mapped_column(String(20))
    donor_race: Mapped[str | None] = mapped_column(String(100))
    donor_ethnicity: Mapped[str | None] = mapped_column(String(100))

    # Clinical Information (using Text for potentially long values)
    primary_diagnosis: Mapped[str | None] = mapped_column(Text)
    primary_diagnosis_code: Mapped[str | None] = mapped_column(Text)  # Can have multiple ICD codes
    secondary_diagnoses: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)
    cause_of_death: Mapped[str | None] = mapped_column(Text)
    manner_of_death: Mapped[str | None] = mapped_column(String(100))

    # Tissue Details
    brain_region: Mapped[str | None] = mapped_column(Text)  # Can be very long (50+ regions)
    brain_region_code: Mapped[str | None] = mapped_column(String(50))
    tissue_type: Mapped[str | None] = mapped_column(String(100))
    hemisphere: Mapped[str | None] = mapped_column(String(20))
    preservation_method: Mapped[str | None] = mapped_column(String(200))

    # Quality Metrics
    postmortem_interval_hours: Mapped[float | None] = mapped_column(Numeric(10, 2))
    ph_level: Mapped[float | None] = mapped_column(Numeric(4, 2))
    rin_score: Mapped[float | None] = mapped_column(Numeric(4, 2))
    quality_metrics: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    # Availability
    quantity_available: Mapped[str | None] = mapped_column(String(100))
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)

    # Flexible storage
    raw_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    extended_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    # Computed fields
    searchable_text: Mapped[str | None] = mapped_column(Text)
    
    # Vector embedding for semantic search (1536 dimensions for text-embedding-3-small)
    # Only available when using PostgreSQL with pgvector extension
    if HAS_PGVECTOR:
        embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)

    # Metadata
    imported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class Conversation(Base):
    """Conversation history."""

    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    user_id: Mapped[str | None] = mapped_column(String(255))
    title: Mapped[str | None] = mapped_column(String(500))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )
    samples: Mapped[list["ConversationSample"]] = relationship(
        "ConversationSample", back_populates="conversation", cascade="all, delete-orphan"
    )


class Message(Base):
    """Individual messages in conversations."""

    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )

    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # RAG context
    retrieved_sample_ids: Mapped[list[str] | None] = mapped_column(JSON)
    retrieved_chunk_ids: Mapped[list[str] | None] = mapped_column(JSON)

    # Metadata
    tokens_used: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="messages"
    )


class ConversationSample(Base):
    """Samples selected/recommended in a conversation.
    
    Persists the sample selection so users can resume sessions
    with their previously selected cases and controls.
    """

    __tablename__ = "conversation_samples"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    sample_external_id: Mapped[str] = mapped_column(String(100), nullable=False)
    sample_group: Mapped[str] = mapped_column(String(20), nullable=False)  # 'case' or 'control'
    
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Cached sample info for display without re-querying samples table
    diagnosis: Mapped[str | None] = mapped_column(String(500))
    age: Mapped[int | None] = mapped_column(Integer)
    sex: Mapped[str | None] = mapped_column(String(20))
    source_bank: Mapped[str | None] = mapped_column(String(100))
    
    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="samples"
    )
    
    # Unique constraint: same sample can't be added twice to same conversation
    __table_args__ = (
        UniqueConstraint('conversation_id', 'sample_external_id', name='uq_conversation_sample'),
    )


class Paper(Base):
    """Research papers for RAG."""

    __tablename__ = "papers"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    authors: Mapped[list[str] | None] = mapped_column(JSON)
    abstract: Mapped[str | None] = mapped_column(Text)
    publication_date: Mapped[datetime | None] = mapped_column(DateTime)
    journal: Mapped[str | None] = mapped_column(String(500))
    doi: Mapped[str | None] = mapped_column(String(255), unique=True)
    pmid: Mapped[str | None] = mapped_column(String(50))

    # Processing
    pdf_path: Mapped[str | None] = mapped_column(String(500))
    full_text: Mapped[str | None] = mapped_column(Text)
    processing_status: Mapped[str] = mapped_column(String(50), default="pending")

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    chunks: Mapped[list["PaperChunk"]] = relationship(
        "PaperChunk", back_populates="paper", cascade="all, delete-orphan"
    )


class PaperChunk(Base):
    """Chunked paper content for RAG."""

    __tablename__ = "paper_chunks"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    paper_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False
    )

    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Chunk metadata
    section_title: Mapped[str | None] = mapped_column(String(500))
    page_number: Mapped[int | None] = mapped_column(Integer)

    # Vector embedding for semantic search
    if HAS_PGVECTOR:
        embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    paper: Mapped["Paper"] = relationship("Paper", back_populates="chunks")


class KnowledgeDocument(Base):
    """Web-scraped documents for the knowledge base."""

    __tablename__ = "knowledge_documents"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    
    # Source information
    url: Mapped[str] = mapped_column(String(2000), nullable=False, unique=True)
    title: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    
    # Content
    markdown_content: Mapped[str | None] = mapped_column(Text)
    html_content: Mapped[str | None] = mapped_column(Text)
    
    # Categorization
    source_name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "NIH NeuroBioBank"
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "best_practices", "definitions"
    tags: Mapped[list[str] | None] = mapped_column(JSON)
    
    # Metadata
    last_scraped_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    scrape_status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, success, error
    processing_status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, chunked, embedded
    
    # Firecrawl metadata
    scrape_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    chunks: Mapped[list["KnowledgeChunk"]] = relationship(
        "KnowledgeChunk", back_populates="document", cascade="all, delete-orphan"
    )


class KnowledgeChunk(Base):
    """Chunked knowledge document content for RAG."""

    __tablename__ = "knowledge_chunks"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False
    )

    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Chunk metadata
    section_title: Mapped[str | None] = mapped_column(String(500))
    heading_hierarchy: Mapped[list[str] | None] = mapped_column(JSON)  # e.g., ["Best Practices", "Brain Collection"]
    
    # Token count for context management
    token_count: Mapped[int | None] = mapped_column(Integer)

    # Vector embedding for semantic search
    if HAS_PGVECTOR:
        embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    document: Mapped["KnowledgeDocument"] = relationship("KnowledgeDocument", back_populates="chunks")

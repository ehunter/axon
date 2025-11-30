"""Add knowledge documents tables

Revision ID: add_knowledge_docs
Revises: 64d85d628cf0
Create Date: 2024-11-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_knowledge_docs'
down_revision: Union[str, None] = '64d85d628cf0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create knowledge documents tables."""
    
    # Knowledge Documents table
    op.create_table(
        'knowledge_documents',
        sa.Column('id', sa.String(36), primary_key=True),
        # Source information
        sa.Column('url', sa.String(2000), nullable=False, unique=True),
        sa.Column('title', sa.Text),
        sa.Column('description', sa.Text),
        # Content
        sa.Column('markdown_content', sa.Text),
        sa.Column('html_content', sa.Text),
        # Categorization
        sa.Column('source_name', sa.String(100), nullable=False),
        sa.Column('content_type', sa.String(50), nullable=False),
        sa.Column('tags', sa.JSON),
        # Metadata
        sa.Column('last_scraped_at', sa.DateTime, nullable=False),
        sa.Column('scrape_status', sa.String(50), default='pending'),
        sa.Column('processing_status', sa.String(50), default='pending'),
        sa.Column('scrape_metadata', sa.JSON),
        # Timestamps
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )
    
    # Knowledge Chunks table
    op.create_table(
        'knowledge_chunks',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('document_id', sa.String(36), sa.ForeignKey('knowledge_documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_index', sa.Integer, nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('section_title', sa.String(500)),
        sa.Column('heading_hierarchy', sa.JSON),
        sa.Column('token_count', sa.Integer),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )
    
    # Add vector column for knowledge chunk embeddings
    op.execute('ALTER TABLE knowledge_chunks ADD COLUMN embedding vector(1536)')
    
    # Create HNSW index for vector similarity search
    op.execute('''
        CREATE INDEX idx_knowledge_chunks_embedding 
        ON knowledge_chunks USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    ''')
    
    # Create indexes for common queries
    op.create_index('idx_knowledge_documents_source_name', 'knowledge_documents', ['source_name'])
    op.create_index('idx_knowledge_documents_content_type', 'knowledge_documents', ['content_type'])
    op.create_index('idx_knowledge_chunks_document_id', 'knowledge_chunks', ['document_id'])


def downgrade() -> None:
    """Drop knowledge documents tables."""
    # Drop indexes
    op.drop_index('idx_knowledge_chunks_document_id')
    op.drop_index('idx_knowledge_documents_content_type')
    op.drop_index('idx_knowledge_documents_source_name')
    
    # Drop vector index
    op.execute('DROP INDEX IF EXISTS idx_knowledge_chunks_embedding')
    
    # Drop tables
    op.drop_table('knowledge_chunks')
    op.drop_table('knowledge_documents')


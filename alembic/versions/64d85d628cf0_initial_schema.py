"""Initial schema

Revision ID: 64d85d628cf0
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '64d85d628cf0'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial database schema."""
    
    # Enable pgvector extension (PostgreSQL only)
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Data Sources table
    op.create_table(
        'data_sources',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('display_name', sa.String(200)),
        sa.Column('description', sa.Text),
        sa.Column('website_url', sa.String(500)),
        sa.Column('contact_email', sa.String(255)),
        sa.Column('data_format', sa.String(50)),
        sa.Column('last_sync_at', sa.DateTime),
        sa.Column('last_sync_status', sa.String(50)),
        sa.Column('total_samples', sa.Integer, default=0),
        sa.Column('adapter_class', sa.String(200)),
        sa.Column('config', sa.JSON),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )
    
    # Source Characteristics table
    op.create_table(
        'source_characteristics',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('source_id', sa.String(36), sa.ForeignKey('data_sources.id', ondelete='CASCADE'), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('characteristic', sa.Text, nullable=False),
        sa.Column('agent_guidance', sa.Text),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )
    
    # Samples table
    op.create_table(
        'samples',
        sa.Column('id', sa.String(36), primary_key=True),
        # Source tracking
        sa.Column('source_bank', sa.String(100), nullable=False),
        sa.Column('external_id', sa.String(255), nullable=False),
        sa.Column('source_url', sa.String(500)),
        # Donor Demographics
        sa.Column('donor_age', sa.Integer),
        sa.Column('donor_age_range', sa.String(50)),
        sa.Column('donor_sex', sa.String(20)),
        sa.Column('donor_race', sa.String(100)),
        sa.Column('donor_ethnicity', sa.String(100)),
        # Clinical Information
        sa.Column('primary_diagnosis', sa.String(500)),
        sa.Column('primary_diagnosis_code', sa.String(50)),
        sa.Column('secondary_diagnoses', sa.JSON),
        sa.Column('cause_of_death', sa.String(500)),
        sa.Column('manner_of_death', sa.String(100)),
        # Tissue Details
        sa.Column('brain_region', sa.String(200)),
        sa.Column('brain_region_code', sa.String(50)),
        sa.Column('tissue_type', sa.String(100)),
        sa.Column('hemisphere', sa.String(20)),
        sa.Column('preservation_method', sa.String(200)),
        # Quality Metrics
        sa.Column('postmortem_interval_hours', sa.Numeric(10, 2)),
        sa.Column('ph_level', sa.Numeric(4, 2)),
        sa.Column('rin_score', sa.Numeric(4, 2)),
        sa.Column('quality_metrics', sa.JSON),
        # Availability
        sa.Column('quantity_available', sa.String(100)),
        sa.Column('is_available', sa.Boolean, default=True),
        # Flexible storage
        sa.Column('raw_data', sa.JSON, nullable=False),
        sa.Column('extended_data', sa.JSON),
        # Computed fields
        sa.Column('searchable_text', sa.Text),
        # Metadata
        sa.Column('imported_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        # Unique constraint
        sa.UniqueConstraint('source_bank', 'external_id', name='uq_sample_source_external'),
    )
    
    # Add vector column for embeddings (PostgreSQL with pgvector)
    op.execute('ALTER TABLE samples ADD COLUMN embedding vector(3072)')
    
    # Conversations table
    op.create_table(
        'conversations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(255)),
        sa.Column('title', sa.String(500)),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )
    
    # Messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('conversation_id', sa.String(36), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('retrieved_sample_ids', sa.JSON),
        sa.Column('retrieved_chunk_ids', sa.JSON),
        sa.Column('tokens_used', sa.Integer),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )
    
    # Papers table
    op.create_table(
        'papers',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('title', sa.Text, nullable=False),
        sa.Column('authors', sa.JSON),
        sa.Column('abstract', sa.Text),
        sa.Column('publication_date', sa.DateTime),
        sa.Column('journal', sa.String(500)),
        sa.Column('doi', sa.String(255), unique=True),
        sa.Column('pmid', sa.String(50)),
        sa.Column('pdf_path', sa.String(500)),
        sa.Column('full_text', sa.Text),
        sa.Column('processing_status', sa.String(50), default='pending'),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )
    
    # Paper Chunks table
    op.create_table(
        'paper_chunks',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('paper_id', sa.String(36), sa.ForeignKey('papers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_index', sa.Integer, nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('section_title', sa.String(500)),
        sa.Column('page_number', sa.Integer),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )
    
    # Add vector column for paper chunk embeddings
    op.execute('ALTER TABLE paper_chunks ADD COLUMN embedding vector(3072)')
    
    # Create indexes for vector similarity search
    op.execute('''
        CREATE INDEX idx_samples_embedding 
        ON samples USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    ''')
    
    op.execute('''
        CREATE INDEX idx_paper_chunks_embedding 
        ON paper_chunks USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    ''')
    
    # Create indexes for common query patterns
    op.create_index('idx_samples_source_bank', 'samples', ['source_bank'])
    op.create_index('idx_samples_primary_diagnosis', 'samples', ['primary_diagnosis'])
    op.create_index('idx_samples_brain_region', 'samples', ['brain_region'])
    op.create_index('idx_samples_tissue_type', 'samples', ['tissue_type'])
    op.create_index('idx_samples_is_available', 'samples', ['is_available'])
    
    op.create_index('idx_messages_conversation_id', 'messages', ['conversation_id'])
    op.create_index('idx_paper_chunks_paper_id', 'paper_chunks', ['paper_id'])


def downgrade() -> None:
    """Drop all tables."""
    # Drop indexes
    op.drop_index('idx_paper_chunks_paper_id')
    op.drop_index('idx_messages_conversation_id')
    op.drop_index('idx_samples_is_available')
    op.drop_index('idx_samples_tissue_type')
    op.drop_index('idx_samples_brain_region')
    op.drop_index('idx_samples_primary_diagnosis')
    op.drop_index('idx_samples_source_bank')
    
    # Drop vector indexes
    op.execute('DROP INDEX IF EXISTS idx_paper_chunks_embedding')
    op.execute('DROP INDEX IF EXISTS idx_samples_embedding')
    
    # Drop tables in reverse order of creation (respecting foreign keys)
    op.drop_table('paper_chunks')
    op.drop_table('papers')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('samples')
    op.drop_table('source_characteristics')
    op.drop_table('data_sources')
    
    # Drop extension
    op.execute('DROP EXTENSION IF EXISTS vector')

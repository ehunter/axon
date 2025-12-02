"""Add conversation_samples table for persisting sample selections

Revision ID: add_conversation_samples
Revises: add_knowledge_documents
Create Date: 2024-01-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_conversation_samples'
down_revision: Union[str, None] = 'add_knowledge_docs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create conversation_samples table for persisting sample selections."""
    
    op.create_table(
        'conversation_samples',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('conversation_id', sa.String(36), 
                  sa.ForeignKey('conversations.id', ondelete='CASCADE'), 
                  nullable=False),
        sa.Column('sample_external_id', sa.String(100), nullable=False),
        sa.Column('sample_group', sa.String(20), nullable=False),  # 'case' or 'control'
        sa.Column('added_at', sa.DateTime, nullable=False),
        
        # Cached sample info for display
        sa.Column('diagnosis', sa.String(500)),
        sa.Column('age', sa.Integer),
        sa.Column('sex', sa.String(20)),
        sa.Column('source_bank', sa.String(100)),
        
        # Unique constraint: same sample can't be added twice to same conversation
        sa.UniqueConstraint('conversation_id', 'sample_external_id', 
                           name='uq_conversation_sample'),
    )
    
    # Index for efficient queries by conversation
    op.create_index(
        'ix_conversation_samples_conversation_id',
        'conversation_samples',
        ['conversation_id']
    )


def downgrade() -> None:
    """Drop conversation_samples table."""
    op.drop_index('ix_conversation_samples_conversation_id', 'conversation_samples')
    op.drop_table('conversation_samples')


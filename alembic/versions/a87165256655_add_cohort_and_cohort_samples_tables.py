"""Add cohort and cohort_samples tables

Revision ID: a87165256655
Revises: add_conversation_samples
Create Date: 2025-12-10 23:15:58.042944

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a87165256655'
down_revision: Union[str, Sequence[str], None] = 'add_conversation_samples'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create cohorts table
    op.create_table('cohorts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('source_conversation_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['source_conversation_id'], ['conversations.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create cohort_samples table
    op.create_table('cohort_samples',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('cohort_id', sa.String(length=36), nullable=False),
        sa.Column('sample_external_id', sa.String(length=100), nullable=False),
        sa.Column('sample_group', sa.String(length=20), nullable=False),
        sa.Column('added_at', sa.DateTime(), nullable=False),
        sa.Column('diagnosis', sa.String(length=500), nullable=True),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('sex', sa.String(length=20), nullable=True),
        sa.Column('source_bank', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['cohort_id'], ['cohorts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cohort_id', 'sample_external_id', name='uq_cohort_sample')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('cohort_samples')
    op.drop_table('cohorts')

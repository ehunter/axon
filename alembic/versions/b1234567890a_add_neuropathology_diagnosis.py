"""Add neuropathology_diagnosis column to samples

This migration adds:
- neuropathology_diagnosis: The pathologically confirmed diagnosis (PRIMARY for recommendations)
- neuropathology_diagnosis_code: ICD code for neuropathology diagnosis

The neuropathology_diagnosis field should be used for sample recommendations,
not primary_diagnosis (which contains Clinical Brain Diagnosis).

Revision ID: b1234567890a
Revises: a87165256655
Create Date: 2025-12-11

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b1234567890a"
down_revision: Union[str, None] = "a87165256655"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns
    op.add_column(
        "samples",
        sa.Column("neuropathology_diagnosis", sa.Text(), nullable=True),
    )
    op.add_column(
        "samples",
        sa.Column("neuropathology_diagnosis_code", sa.Text(), nullable=True),
    )
    
    # Backfill neuropathology_diagnosis from raw_data JSON
    # Uses PostgreSQL JSON extraction: raw_data->>'Neuropathology Diagnosis'
    op.execute("""
        UPDATE samples 
        SET 
            neuropathology_diagnosis = raw_data->>'Neuropathology Diagnosis',
            neuropathology_diagnosis_code = raw_data->>'ICD for Neuropathology Diagnosis'
        WHERE raw_data IS NOT NULL
        AND raw_data->>'Neuropathology Diagnosis' IS NOT NULL
        AND raw_data->>'Neuropathology Diagnosis' != ''
    """)
    
    # Create index for efficient filtering by neuropathology diagnosis
    op.create_index(
        "ix_samples_neuropathology_diagnosis",
        "samples",
        ["neuropathology_diagnosis"],
    )


def downgrade() -> None:
    op.drop_index("ix_samples_neuropathology_diagnosis", table_name="samples")
    op.drop_column("samples", "neuropathology_diagnosis_code")
    op.drop_column("samples", "neuropathology_diagnosis")


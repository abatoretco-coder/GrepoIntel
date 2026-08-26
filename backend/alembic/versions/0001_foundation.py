"""foundation schema

Revision ID: 0001_foundation
Revises:
Create Date: 2026-08-26
"""
from alembic import op
from app.db.base import Base
from app.models import all_models  # noqa: F401

revision = "0001_foundation"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    Base.metadata.create_all(op.get_bind())

def downgrade() -> None:
    Base.metadata.drop_all(op.get_bind())

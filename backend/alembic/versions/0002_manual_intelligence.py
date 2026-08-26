"""manual intelligence storage

Revision ID: 0002_manual_intelligence
Revises: 0001_foundation
"""
from alembic import op
from app.models.all_models import AllianceRelation, SpyReport

revision = "0002_manual_intelligence"
down_revision = "0001_foundation"
branch_labels = None
depends_on = None

def upgrade() -> None:
    AllianceRelation.__table__.create(op.get_bind(), checkfirst=True)
    SpyReport.__table__.create(op.get_bind(), checkfirst=True)

def downgrade() -> None:
    SpyReport.__table__.drop(op.get_bind(), checkfirst=True)
    AllianceRelation.__table__.drop(op.get_bind(), checkfirst=True)

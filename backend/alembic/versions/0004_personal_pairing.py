"""local companion pairing

Revision ID: 0004_personal_pairing
Revises: 0003_personal_state
"""
from alembic import op
from app.models.all_models import PersonalStatePairing
revision="0004_personal_pairing"; down_revision="0003_personal_state"; branch_labels=None; depends_on=None
def upgrade(): PersonalStatePairing.__table__.create(op.get_bind(),checkfirst=True)
def downgrade(): PersonalStatePairing.__table__.drop(op.get_bind(),checkfirst=True)

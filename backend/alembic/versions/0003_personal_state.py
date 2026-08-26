"""personal empire state

Revision ID: 0003_personal_state
Revises: 0002_manual_intelligence
"""
from alembic import op
from app.models.all_models import PersonalCityState, PersonalEmpireSnapshot
revision="0003_personal_state"; down_revision="0002_manual_intelligence"; branch_labels=None; depends_on=None
def upgrade():
    PersonalEmpireSnapshot.__table__.create(op.get_bind(),checkfirst=True); PersonalCityState.__table__.create(op.get_bind(),checkfirst=True)
def downgrade():
    PersonalCityState.__table__.drop(op.get_bind(),checkfirst=True); PersonalEmpireSnapshot.__table__.drop(op.get_bind(),checkfirst=True)

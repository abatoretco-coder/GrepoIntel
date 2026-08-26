"""personal global companion state

Revision ID: 0005_personal_global_state
Revises: 0004_personal_pairing
"""
from alembic import op
import sqlalchemy as sa
revision="0005_personal_global_state"; down_revision="0004_personal_pairing"; branch_labels=None; depends_on=None
def upgrade(): op.add_column("personal_empire_snapshots",sa.Column("global_state",sa.JSON(),nullable=False,server_default=sa.text("'{}'")))
def downgrade(): op.drop_column("personal_empire_snapshots","global_state")

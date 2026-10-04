"""add users.avatar_code, seeded from the username

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-10-04

Hand-written. `avatar_code` is the string the client generates a user's
profile picture from. Every existing account starts on its username, which
is what the avatars were derived from before this column existed — so
nobody's picture changes on upgrade.

Added nullable, backfilled, then tightened to NOT NULL: `users` may already
hold rows and there is no constant default that would be right for them.
New rows get the username from the model-level default.
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("avatar_code", sa.String(length=64), nullable=True))
    op.execute("UPDATE users SET avatar_code = username")
    op.alter_column("users", "avatar_code", nullable=False)


def downgrade():
    op.drop_column("users", "avatar_code")

"""add users.is_admin and promote the first account

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-07-27

Hand-written. Adds a NOT NULL `users.is_admin` defaulting to false, then
promotes the lowest-id account so an existing deployment comes out of the
upgrade with exactly one administrator and no manual SQL step.

`server_default` is mandatory: the column is NOT NULL and `users` may
already hold rows. It is deliberately left in place afterwards so inserts
made outside SQLAlchemy (psql, fixtures) also default to false.

CAVEAT: if `users` is EMPTY when this runs — e.g. straight after a
`docker compose down -v` — the UPDATE matches nothing and nobody ends up
an admin. Register the first account, then promote it by hand:

    docker compose exec db psql -U postgres -d workout_app \\
      -c "UPDATE users SET is_admin = true WHERE id = (SELECT MIN(id) FROM users);"
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    # MIN(id) rather than a literal 1 — id 1 may have been deleted.
    # No-op on an empty table; see the caveat above.
    op.execute("UPDATE users SET is_admin = true WHERE id = (SELECT MIN(id) FROM users)")


def downgrade():
    op.drop_column("users", "is_admin")

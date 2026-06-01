"""add users table and workout ownership

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-01

Hand-written. Adds the `users` table and a NOT NULL `workouts.user_id`
column. The migration assumes the `workouts` table is empty — Phase 4
ships with a `docker compose down -v` wipe; if you run this against a
populated DB it will fail at the NOT NULL alter, which is the expected
loud error rather than silent data loss.
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(64), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("username", name="uq_users_username"),
    )
    op.create_index("ix_users_username", "users", ["username"])

    op.add_column(
        "workouts",
        sa.Column("user_id", sa.Integer(), nullable=False),
    )
    op.create_foreign_key(
        "fk_workouts_user_id_users",
        "workouts", "users",
        ["user_id"], ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_workouts_user_id", "workouts", ["user_id"])


def downgrade():
    op.drop_index("ix_workouts_user_id", table_name="workouts")
    op.drop_constraint("fk_workouts_user_id_users", "workouts", type_="foreignkey")
    op.drop_column("workouts", "user_id")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")

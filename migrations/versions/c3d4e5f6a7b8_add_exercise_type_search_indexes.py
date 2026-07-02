"""add search indexes for exercise_types

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-07-02

Hand-written: enables pg_trgm and adds the indexes that back the
exercise-catalog search:

- GIN trigram indexes on name and muscle_group serve the
  `ILIKE '%q%'` substring search (a btree cannot serve a
  leading-wildcard pattern).
- A btree on lower(muscle_group) serves the exact group filter
  and the distinct muscle-groups listing.
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute(
        "CREATE INDEX ix_exercise_types_name_trgm "
        "ON exercise_types USING gin (name gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX ix_exercise_types_muscle_group_trgm "
        "ON exercise_types USING gin (muscle_group gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX ix_exercise_types_muscle_group_lower "
        "ON exercise_types (lower(muscle_group))"
    )


def downgrade():
    op.execute("DROP INDEX ix_exercise_types_muscle_group_lower")
    op.execute("DROP INDEX ix_exercise_types_muscle_group_trgm")
    op.execute("DROP INDEX ix_exercise_types_name_trgm")
    # pg_trgm is left installed: dropping a shared extension could break
    # objects created outside this migration.

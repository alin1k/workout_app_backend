"""add check constraints for numeric invariants

Revision ID: a1b2c3d4e5f6
Revises: 85d4f206bbad
Create Date: 2026-05-31

Hand-written: Alembic autogenerate does not detect new CheckConstraints,
so the constraints are explicitly defined here.
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "85d4f206bbad"
branch_labels = None
depends_on = None


def upgrade():
    op.create_check_constraint(
        "ck_exercises_order_positive",
        "exercises",
        '"order" > 0',
    )
    op.create_check_constraint(
        "ck_sets_reps_positive",
        "sets",
        "reps > 0",
    )
    op.create_check_constraint(
        "ck_sets_set_number_positive",
        "sets",
        "set_number > 0",
    )
    op.create_check_constraint(
        "ck_sets_weight_non_negative",
        "sets",
        "weight IS NULL OR weight >= 0",
    )


def downgrade():
    op.drop_constraint("ck_sets_weight_non_negative", "sets", type_="check")
    op.drop_constraint("ck_sets_set_number_positive", "sets", type_="check")
    op.drop_constraint("ck_sets_reps_positive", "sets", type_="check")
    op.drop_constraint("ck_exercises_order_positive", "exercises", type_="check")

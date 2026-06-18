"""create registrations table

Revision ID: 0004_create_registrations
Revises: 0003_create_event_sessions
Create Date: 2026-06-18 00:00:01

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_create_registrations"
down_revision: str | None = "0003_create_event_sessions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

REGISTRATION_STATUS_VALUES = ("CONFIRMED", "CANCELLED")


def upgrade() -> None:
    registration_status_enum = postgresql.ENUM(
        *REGISTRATION_STATUS_VALUES, name="registration_status", create_type=False
    )
    postgresql.ENUM(*REGISTRATION_STATUS_VALUES, name="registration_status").create(
        op.get_bind(), checkfirst=True
    )

    op.create_table(
        "registrations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("status", registration_status_enum, nullable=False, server_default="CONFIRMED"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            name="fk_registrations_user_id_users",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["event_id"], ["events.id"],
            name="fk_registrations_event_id_events",
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_registrations_user_id", "registrations", ["user_id"])
    op.create_index("ix_registrations_event_id", "registrations", ["event_id"])
    op.create_index("ix_registrations_status", "registrations", ["status"])
    op.create_index(
        "ix_registrations_event_status", "registrations", ["event_id", "status"]
    )
    # Unique parcial sobre activas: una sola inscripción CONFIRMED por (user, event).
    # Las filas CANCELLED no consumen el unique, lo que habilita re-inscripción.
    op.create_index(
        "uq_registrations_active",
        "registrations",
        ["user_id", "event_id"],
        unique=True,
        postgresql_where=sa.text("status = 'CONFIRMED'"),
        sqlite_where=sa.text("status = 'CONFIRMED'"),
    )


def downgrade() -> None:
    op.drop_index("uq_registrations_active", table_name="registrations")
    op.drop_index("ix_registrations_event_status", table_name="registrations")
    op.drop_index("ix_registrations_status", table_name="registrations")
    op.drop_index("ix_registrations_event_id", table_name="registrations")
    op.drop_index("ix_registrations_user_id", table_name="registrations")
    op.drop_table("registrations")
    postgresql.ENUM(name="registration_status").drop(op.get_bind(), checkfirst=True)

"""create events table

Revision ID: 0002_create_events
Revises: 0001_create_users
Create Date: 2026-06-17 00:00:01

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_create_events"
down_revision: str | None = "0001_create_users"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

EVENT_STATUS_VALUES = ("DRAFT", "PUBLISHED", "IN_PROGRESS", "FINISHED", "CANCELLED")


def upgrade() -> None:
    event_status_enum = postgresql.ENUM(*EVENT_STATUS_VALUES, name="event_status", create_type=False)
    postgresql.ENUM(*EVENT_STATUS_VALUES, name="event_status").create(op.get_bind(), checkfirst=True)

    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(length=5000), nullable=True),
        sa.Column("location", sa.String(length=200), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", event_status_enum, nullable=False, server_default="DRAFT"),
        sa.Column("owner_id", sa.Integer(), nullable=False),
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
            ["owner_id"], ["users.id"], name="fk_events_owner_id_users", ondelete="RESTRICT"
        ),
        sa.CheckConstraint("capacity > 0", name="ck_events_capacity_positive"),
        sa.CheckConstraint("start_at < end_at", name="ck_events_start_before_end"),
    )
    op.create_index("ix_events_title", "events", ["title"])
    op.create_index("ix_events_owner_id", "events", ["owner_id"])
    op.create_index("ix_events_status_start_at", "events", ["status", "start_at"])
    op.create_index(
        "ix_events_owner_created",
        "events",
        ["owner_id", sa.text("created_at DESC")],
    )


def downgrade() -> None:
    op.drop_index("ix_events_owner_created", table_name="events")
    op.drop_index("ix_events_status_start_at", table_name="events")
    op.drop_index("ix_events_owner_id", table_name="events")
    op.drop_index("ix_events_title", table_name="events")
    op.drop_table("events")
    postgresql.ENUM(name="event_status").drop(op.get_bind(), checkfirst=True)

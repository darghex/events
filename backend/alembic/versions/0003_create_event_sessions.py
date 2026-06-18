"""create event_sessions table

Revision ID: 0003_create_event_sessions
Revises: 0002_create_events
Create Date: 2026-06-18 00:00:01

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_create_event_sessions"
down_revision: str | None = "0002_create_events"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "event_sessions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("speaker_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(length=2000), nullable=True),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=True),
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
            ["event_id"], ["events.id"],
            name="fk_event_sessions_event_id_events",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["speaker_id"], ["users.id"],
            name="fk_event_sessions_speaker_id_users",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint("start_at < end_at", name="ck_event_sessions_start_before_end"),
        sa.CheckConstraint(
            "capacity IS NULL OR capacity > 0",
            name="ck_event_sessions_capacity_positive_or_null",
        ),
    )
    op.create_index("ix_event_sessions_event_id", "event_sessions", ["event_id"])
    op.create_index("ix_event_sessions_speaker_id", "event_sessions", ["speaker_id"])
    op.create_index(
        "ix_event_sessions_event_start", "event_sessions", ["event_id", "start_at"]
    )
    op.create_index(
        "ix_event_sessions_speaker_start", "event_sessions", ["speaker_id", "start_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_event_sessions_speaker_start", table_name="event_sessions")
    op.drop_index("ix_event_sessions_event_start", table_name="event_sessions")
    op.drop_index("ix_event_sessions_speaker_id", table_name="event_sessions")
    op.drop_index("ix_event_sessions_event_id", table_name="event_sessions")
    op.drop_table("event_sessions")

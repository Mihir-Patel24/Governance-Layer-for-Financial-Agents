"""Initial schema - all Person 2 tables

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-27

Creates:
  - agents
  - spend_state
  - kill_switch_state
  - fleet_kill_switch_state
  - audit_log
  - idempotency_keys
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── agents ──────────────────────────────────────────────────────────────
    op.create_table(
        "agents",
        sa.Column("agent_id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )

    # ── spend_state ──────────────────────────────────────────────────────────
    op.create_table(
        "spend_state",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("agent_id", sa.String(64),
                  sa.ForeignKey("agents.agent_id", ondelete="CASCADE"), nullable=False),
        sa.Column("period_type", sa.String(16), nullable=False, server_default="DAILY"),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("limit_amount", sa.Float, nullable=False),
        sa.Column("currency", sa.String(8), nullable=False, server_default="INR"),
        sa.Column("spent_amount", sa.Float, nullable=False, server_default="0"),
        sa.Column("rollover_amount", sa.Float, nullable=False, server_default="0"),
        sa.Column("reset_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("agent_id", "period_type", name="uq_spend_agent_period"),
    )

    # ── kill_switch_state ────────────────────────────────────────────────────
    op.create_table(
        "kill_switch_state",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("agent_id", sa.String(64),
                  sa.ForeignKey("agents.agent_id", ondelete="CASCADE"),
                  nullable=False, unique=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="RUNNING"),
        sa.Column("reason", sa.String(512), nullable=True),
        sa.Column("updated_by", sa.String(64), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )

    # ── fleet_kill_switch_state ──────────────────────────────────────────────
    op.create_table(
        "fleet_kill_switch_state",
        sa.Column("id", sa.Integer, primary_key=True, default=1),
        sa.Column("status", sa.String(16), nullable=False, server_default="RUNNING"),
        sa.Column("reason", sa.String(512), nullable=True),
        sa.Column("updated_by", sa.String(64), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    # Seed the singleton fleet row
    op.execute(
        "INSERT INTO fleet_kill_switch_state (id, status) VALUES (1, 'RUNNING') "
        "ON CONFLICT (id) DO NOTHING"
    )

    # ── audit_log ────────────────────────────────────────────────────────────
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("sequence_num", sa.Integer, nullable=False, unique=True),
        sa.Column("event_id", sa.String(64), nullable=False, unique=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("agent_id", sa.String(64), nullable=True),
        sa.Column("action_id", sa.String(128), nullable=True),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("action", sa.String(128), nullable=True),
        sa.Column("amount", sa.Float, nullable=True),
        sa.Column("currency", sa.String(8), nullable=True),
        sa.Column("decision", sa.String(16), nullable=True),
        sa.Column("reason_code", sa.String(64), nullable=True),
        sa.Column("metadata_json", sa.Text, nullable=True),
        sa.Column("previous_hash", sa.String(128), nullable=False),
        sa.Column("current_hash", sa.String(128), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_agent_id", "audit_log", ["agent_id"])
    op.create_index("ix_audit_event_type", "audit_log", ["event_type"])
    op.create_index("ix_audit_decision", "audit_log", ["decision"])
    op.create_index("ix_audit_timestamp", "audit_log", ["timestamp"])
    op.create_index("ix_audit_sequence", "audit_log", ["sequence_num"])

    # ── idempotency_keys ─────────────────────────────────────────────────────
    op.create_table(
        "idempotency_keys",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("agent_id", sa.String(64), nullable=False),
        sa.Column("action_id", sa.String(128), nullable=False),
        sa.Column("cached_result_json", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("agent_id", "action_id", name="uq_idempotency_agent_action"),
    )


def downgrade() -> None:
    op.drop_table("idempotency_keys")
    op.drop_index("ix_audit_sequence", "audit_log")
    op.drop_index("ix_audit_timestamp", "audit_log")
    op.drop_index("ix_audit_decision", "audit_log")
    op.drop_index("ix_audit_event_type", "audit_log")
    op.drop_index("ix_audit_agent_id", "audit_log")
    op.drop_table("audit_log")
    op.drop_table("fleet_kill_switch_state")
    op.drop_table("kill_switch_state")
    op.drop_table("spend_state")
    op.drop_table("agents")

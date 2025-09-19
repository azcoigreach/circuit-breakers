"""initial schema"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "world",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("tick", sa.Integer, nullable=False, default=0),
        sa.Column("seed", sa.Integer, nullable=False, default=1337),
        sa.Column("ruleset_version", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "player",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("handle", sa.String(length=64), nullable=False, unique=True),
        sa.Column("token_hash", sa.String(length=128), nullable=False, unique=True),
        sa.Column("balance_mamp", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "entity",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column("owner_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("pos", sa.JSON(), nullable=True),
        sa.Column("attrs", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(["owner_id"], ["player.id"]),
    )

    op.create_table(
        "market_listing",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("seller_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_type", sa.String(length=64), nullable=False),
        sa.Column("item_attrs", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("price_amp_bigint", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_tick", sa.Integer, nullable=False),
        sa.Column("filled_tick", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["seller_id"], ["player.id"]),
    )

    op.create_table(
        "action",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tick", sa.Integer, nullable=False),
        sa.Column("actor_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("signature", sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(["actor_id"], ["player.id"]),
    )

    op.create_table(
        "event",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tick", sa.Integer, nullable=False),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("subject_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "currency_packet",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("denom", sa.String(length=8), nullable=False),
        sa.Column("encrypted", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("owner_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_tick", sa.Integer, nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["player.id"]),
    )

    op.create_table(
        "replay_log",
        sa.Column("tick", sa.Integer, primary_key=True),
        sa.Column("state_hash", sa.String(length=64), nullable=False),
        sa.Column("prev_hash", sa.String(length=64), nullable=False),
        sa.Column("actions", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    for table in [
        "replay_log",
        "currency_packet",
        "event",
        "action",
        "market_listing",
        "entity",
        "player",
        "world",
    ]:
        op.drop_table(table)

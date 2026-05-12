"""create platform metadata tables

Revision ID: 20260512_0001
Revises: None
Create Date: 2026-05-12
"""

from __future__ import annotations

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260512_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamp_columns() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("tenant_id", sa.String(length=128), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("region", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        *timestamp_columns(),
    )

    op.create_table(
        "users",
        sa.Column("user_id", sa.String(length=128), primary_key=True),
        sa.Column("external_subject", sa.String(length=255), nullable=False, unique=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        *timestamp_columns(),
    )

    op.create_table(
        "modules",
        sa.Column("module_id", sa.String(length=128), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        *timestamp_columns(),
    )

    op.create_table(
        "roles",
        sa.Column("role_id", sa.String(length=128), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("scope", sa.String(length=32), nullable=False, server_default="tenant"),
        *timestamp_columns(),
    )

    op.create_table(
        "permissions",
        sa.Column("permission_id", sa.String(length=128), primary_key=True),
        sa.Column("module_id", sa.String(length=128), sa.ForeignKey("modules.module_id"), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        *timestamp_columns(),
    )

    op.create_table(
        "tenant_users",
        sa.Column("tenant_id", sa.String(length=128), sa.ForeignKey("tenants.tenant_id"), nullable=False),
        sa.Column("user_id", sa.String(length=128), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("role_id", sa.String(length=128), sa.ForeignKey("roles.role_id"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("tenant_id", "user_id"),
    )

    op.create_table(
        "tenant_licenses",
        sa.Column("tenant_id", sa.String(length=128), sa.ForeignKey("tenants.tenant_id"), nullable=False),
        sa.Column("module_id", sa.String(length=128), sa.ForeignKey("modules.module_id"), nullable=False),
        sa.Column("license_status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("tenant_id", "module_id"),
    )

    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.String(length=128), sa.ForeignKey("roles.role_id"), nullable=False),
        sa.Column("permission_id", sa.String(length=128), sa.ForeignKey("permissions.permission_id"), nullable=False),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
    )

    op.create_table(
        "content_sources",
        sa.Column("source_id", sa.String(length=128), primary_key=True),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("owner", sa.String(length=255), nullable=False),
        sa.Column("trust_level", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("source_uri", sa.String(length=2048), nullable=False),
        *timestamp_columns(),
    )

    op.create_table(
        "content_versions",
        sa.Column("content_version_id", sa.String(length=128), primary_key=True),
        sa.Column("source_id", sa.String(length=128), sa.ForeignKey("content_sources.source_id"), nullable=False),
        sa.Column("checksum", sa.String(length=128), nullable=False),
        sa.Column("metadata_uri", sa.String(length=2048), nullable=False),
        *timestamp_columns(),
    )

    op.create_table(
        "index_versions",
        sa.Column("index_version_id", sa.String(length=128), primary_key=True),
        sa.Column(
            "content_version_id",
            sa.String(length=128),
            sa.ForeignKey("content_versions.content_version_id"),
            nullable=False,
        ),
        sa.Column("index_type", sa.String(length=64), nullable=False),
        sa.Column("embedding_model_version", sa.String(length=128), nullable=True),
        sa.Column("chunker_version", sa.String(length=128), nullable=True),
        sa.Column("index_uri", sa.String(length=2048), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="building"),
        *timestamp_columns(),
    )

    op.create_table(
        "release_versions",
        sa.Column("release_id", sa.String(length=128), primary_key=True),
        sa.Column("app_version", sa.String(length=128), nullable=False),
        sa.Column(
            "content_version_id",
            sa.String(length=128),
            sa.ForeignKey("content_versions.content_version_id"),
            nullable=False,
        ),
        sa.Column(
            "index_version_id",
            sa.String(length=128),
            sa.ForeignKey("index_versions.index_version_id"),
            nullable=False,
        ),
        sa.Column("prompt_version", sa.String(length=128), nullable=False),
        sa.Column("policy_version", sa.String(length=128), nullable=False),
        sa.Column("guardrail_version", sa.String(length=128), nullable=False),
        sa.Column("router_config_version", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="candidate"),
        *timestamp_columns(),
    )

    op.create_table(
        "eval_runs",
        sa.Column("eval_run_id", sa.String(length=128), primary_key=True),
        sa.Column("release_id", sa.String(length=128), sa.ForeignKey("release_versions.release_id"), nullable=False),
        sa.Column("eval_dataset_version", sa.String(length=128), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("score_summary_uri", sa.String(length=2048), nullable=False),
        *timestamp_columns(),
    )

    op.create_table(
        "cost_events",
        sa.Column("cost_event_id", sa.String(length=128), primary_key=True),
        sa.Column("tenant_id", sa.String(length=128), sa.ForeignKey("tenants.tenant_id"), nullable=False),
        sa.Column("release_id", sa.String(length=128), sa.ForeignKey("release_versions.release_id"), nullable=False),
        sa.Column("route", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=128), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("cost_usd", sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        *timestamp_columns(),
    )

    op.create_index("ix_permissions_module_id", "permissions", ["module_id"])
    op.create_index("ix_tenant_users_user_id", "tenant_users", ["user_id"])
    op.create_index("ix_tenant_licenses_module_id", "tenant_licenses", ["module_id"])
    op.create_index("ix_index_versions_status", "index_versions", ["status"])
    op.create_index("ix_release_versions_status", "release_versions", ["status"])
    op.create_index("ix_cost_events_tenant_occurred", "cost_events", ["tenant_id", "occurred_at"])


def downgrade() -> None:
    op.drop_index("ix_cost_events_tenant_occurred", table_name="cost_events")
    op.drop_index("ix_release_versions_status", table_name="release_versions")
    op.drop_index("ix_index_versions_status", table_name="index_versions")
    op.drop_index("ix_tenant_licenses_module_id", table_name="tenant_licenses")
    op.drop_index("ix_tenant_users_user_id", table_name="tenant_users")
    op.drop_index("ix_permissions_module_id", table_name="permissions")

    op.drop_table("cost_events")
    op.drop_table("eval_runs")
    op.drop_table("release_versions")
    op.drop_table("index_versions")
    op.drop_table("content_versions")
    op.drop_table("content_sources")
    op.drop_table("role_permissions")
    op.drop_table("tenant_licenses")
    op.drop_table("tenant_users")
    op.drop_table("permissions")
    op.drop_table("roles")
    op.drop_table("modules")
    op.drop_table("users")
    op.drop_table("tenants")


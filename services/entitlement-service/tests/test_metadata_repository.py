from __future__ import annotations

import sqlite3
from collections.abc import Iterator

import pytest
from entitlement_service.metadata_repository import MetadataEntitlementRepository
from entitlement_service.resolver import EntitlementResolutionError, resolve_entitlement_envelope


@pytest.fixture
def connection() -> Iterator[sqlite3.Connection]:
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    _create_schema(db)
    _seed_active_principal(db)
    yield db
    db.close()


def test_metadata_repository_resolves_active_principal(connection: sqlite3.Connection) -> None:
    repository = MetadataEntitlementRepository(connection)

    envelope = resolve_entitlement_envelope(
        tenant_id="tenant_123",
        user_id="user_123",
        store=repository,
    )

    assert envelope.tenant_id == "tenant_123"
    assert envelope.region == "us"
    assert envelope.role == "TenantAdmin"
    assert envelope.licensed_modules == ["Billing"]
    assert envelope.permissions == ["Billing.Submit", "Billing.View"]


def test_metadata_repository_fails_closed_for_disabled_tenant(
    connection: sqlite3.Connection,
) -> None:
    connection.execute("update tenants set status = 'disabled' where tenant_id = 'tenant_123'")

    with pytest.raises(EntitlementResolutionError):
        resolve_entitlement_envelope(
            tenant_id="tenant_123",
            user_id="user_123",
            store=MetadataEntitlementRepository(connection),
        )


def test_metadata_repository_fails_closed_without_active_license(
    connection: sqlite3.Connection,
) -> None:
    connection.execute(
        "update tenant_licenses set license_status = 'disabled' where tenant_id = 'tenant_123'"
    )

    with pytest.raises(EntitlementResolutionError):
        resolve_entitlement_envelope(
            tenant_id="tenant_123",
            user_id="user_123",
            store=MetadataEntitlementRepository(connection),
        )


def test_metadata_repository_fails_closed_without_role_permissions(
    connection: sqlite3.Connection,
) -> None:
    connection.execute("delete from role_permissions")

    with pytest.raises(EntitlementResolutionError):
        resolve_entitlement_envelope(
            tenant_id="tenant_123",
            user_id="user_123",
            store=MetadataEntitlementRepository(connection),
        )


def _create_schema(db: sqlite3.Connection) -> None:
    db.executescript(
        """
        create table tenants (
          tenant_id text primary key,
          name text not null,
          region text not null,
          status text not null
        );
        create table users (
          user_id text primary key,
          external_subject text not null,
          status text not null
        );
        create table modules (
          module_id text primary key,
          name text not null,
          status text not null
        );
        create table roles (
          role_id text primary key,
          name text not null,
          scope text not null
        );
        create table permissions (
          permission_id text primary key,
          module_id text not null,
          action text not null
        );
        create table tenant_users (
          tenant_id text not null,
          user_id text not null,
          role_id text not null,
          status text not null
        );
        create table tenant_licenses (
          tenant_id text not null,
          module_id text not null,
          license_status text not null,
          effective_from text not null,
          effective_to text
        );
        create table role_permissions (
          role_id text not null,
          permission_id text not null
        );
        """
    )


def _seed_active_principal(db: sqlite3.Connection) -> None:
    db.executescript(
        """
        insert into tenants values ('tenant_123', 'Acme', 'us', 'active');
        insert into users values ('user_123', 'subject_123', 'active');
        insert into modules values ('billing', 'Billing', 'active');
        insert into roles values ('tenant_admin', 'TenantAdmin', 'tenant');
        insert into permissions values ('billing_view', 'billing', 'view');
        insert into permissions values ('billing_submit', 'billing', 'submit');
        insert into tenant_users values (
          'tenant_123', 'user_123', 'tenant_admin', 'active'
        );
        insert into tenant_licenses values (
          'tenant_123', 'billing', 'active', '2026-01-01 00:00:00', null
        );
        insert into role_permissions values ('tenant_admin', 'billing_view');
        insert into role_permissions values ('tenant_admin', 'billing_submit');
        """
    )

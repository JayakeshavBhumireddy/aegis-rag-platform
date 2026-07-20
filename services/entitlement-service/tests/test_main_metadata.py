from __future__ import annotations

import sqlite3

from entitlement_service.main import app, get_store
from entitlement_service.metadata_repository import MetadataEntitlementRepository
from fastapi.testclient import TestClient


def test_entitlement_api_resolves_metadata_store() -> None:
    connection = sqlite3.connect(":memory:", check_same_thread=False)
    connection.row_factory = sqlite3.Row
    _create_schema(connection)
    _seed_active_principal(connection)
    app.dependency_overrides[get_store] = lambda: MetadataEntitlementRepository(connection)
    client = TestClient(app)

    try:
        response = client.post(
            "/v1/entitlements/resolve",
            json={
                "tenantId": "tenant_123",
                "userId": "user_123",
                "uiContext": {"module": "Billing"},
            },
        )
    finally:
        app.dependency_overrides.clear()
        connection.close()

    assert response.status_code == 200
    envelope = response.json()["entitlementEnvelope"]
    assert envelope["licensedModules"] == ["Billing"]
    assert envelope["permissions"] == ["Billing.Submit", "Billing.View"]


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

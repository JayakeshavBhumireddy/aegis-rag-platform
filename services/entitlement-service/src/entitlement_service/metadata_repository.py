from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from aegis_shared.contracts import DataAccessMode

from entitlement_service.resolver import PrincipalEntitlements


class DbConnection(Protocol):
    def execute(self, sql: str, parameters: tuple[Any, ...] = ...) -> Any: ...


@dataclass(frozen=True)
class MetadataEntitlementDefaults:
    product_version: str = "2026.2"
    enabled_features: tuple[str, ...] = ()
    data_access_mode: DataAccessMode = DataAccessMode.PRODUCT_GUIDANCE_ONLY


class MetadataEntitlementRepository:
    def __init__(
        self,
        connection: DbConnection,
        *,
        defaults: MetadataEntitlementDefaults | None = None,
    ) -> None:
        self._connection = connection
        self._defaults = defaults or MetadataEntitlementDefaults()

    def get(self, tenant_id: str, user_id: str) -> PrincipalEntitlements | None:
        membership = self._fetch_one(
            """
            select
                t.tenant_id,
                u.user_id,
                t.region,
                r.name as role_name
            from tenants t
            join tenant_users tu on tu.tenant_id = t.tenant_id
            join users u on u.user_id = tu.user_id
            join roles r on r.role_id = tu.role_id
            where t.tenant_id = ?
              and u.user_id = ?
              and t.status = 'active'
              and u.status = 'active'
              and tu.status = 'active'
            """,
            (tenant_id, user_id),
        )
        if membership is None:
            return None

        licensed_modules = tuple(
            row["module_name"]
            for row in self._fetch_all(
                """
                select m.name as module_name
                from tenant_licenses tl
                join modules m on m.module_id = tl.module_id
                where tl.tenant_id = ?
                  and tl.license_status = 'active'
                  and m.status = 'active'
                  and (tl.effective_to is null or tl.effective_to > current_timestamp)
                order by m.name
                """,
                (tenant_id,),
            )
        )

        permissions = tuple(
            f"{row['module_name']}.{row['action'].title()}"
            for row in self._fetch_all(
                """
                select distinct m.name as module_name, p.action
                from tenant_users tu
                join role_permissions rp on rp.role_id = tu.role_id
                join permissions p on p.permission_id = rp.permission_id
                join modules m on m.module_id = p.module_id
                where tu.tenant_id = ?
                  and tu.user_id = ?
                  and tu.status = 'active'
                  and m.status = 'active'
                order by m.name, p.action
                """,
                (tenant_id, user_id),
            )
        )

        return PrincipalEntitlements(
            tenant_id=str(membership["tenant_id"]),
            user_id=str(membership["user_id"]),
            region=str(membership["region"]),
            product_version=self._defaults.product_version,
            licensed_modules=licensed_modules,
            enabled_features=self._defaults.enabled_features,
            role=str(membership["role_name"]),
            permissions=permissions,
            data_access_mode=self._defaults.data_access_mode,
        )

    def _fetch_one(self, sql: str, parameters: tuple[Any, ...]) -> dict[str, Any] | None:
        cursor = self._connection.execute(sql, parameters)
        row = cursor.fetchone()
        if row is None:
            return None
        return dict(row)

    def _fetch_all(self, sql: str, parameters: tuple[Any, ...]) -> list[dict[str, Any]]:
        cursor = self._connection.execute(sql, parameters)
        return [dict(row) for row in cursor.fetchall()]

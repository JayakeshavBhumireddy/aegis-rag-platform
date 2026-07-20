from __future__ import annotations

from aegis_shared.contracts import RetrievalScope
from assistant_api.navigation import find_navigation_route


def test_navigation_graph_returns_allowed_route() -> None:
    route = find_navigation_route(
        query="open monthly billing submission",
        retrieval_scope=RetrievalScope(
            tenantId="tenant_123",
            modules=["Billing"],
            permissions=["Billing.View", "Billing.Submit"],
            productVersion="2026.2",
            trustLevel="approved",
        ),
    )

    assert route is not None
    assert route.metadata["routeId"] == "billing.monthly_submission"


def test_navigation_graph_filters_permissions() -> None:
    route = find_navigation_route(
        query="open inventory receiving",
        retrieval_scope=RetrievalScope(
            tenantId="tenant_123",
            modules=["Inventory"],
            permissions=["Inventory.View"],
            productVersion="2026.2",
            trustLevel="approved",
        ),
    )

    assert route is None

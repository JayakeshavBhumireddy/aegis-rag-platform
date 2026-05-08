"""Generate a small synthetic enterprise product-help corpus.

This is a placeholder generator for the first local data slice. It creates safe,
non-proprietary product-help style data that can exercise tenant, license,
permission, navigation, and refusal paths.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "data" / "raw" / "synthetic-enterprise"


MODULES = [
    {
        "moduleId": "billing",
        "name": "Billing",
        "requiredLicense": "Billing",
        "permissions": ["Billing.View", "Billing.Submit"],
        "routes": [
            {
                "routeId": "billing.monthly_submission",
                "screen": "Monthly Submission",
                "path": ["Billing", "Monthly Submission"],
                "requiredPermissions": ["Billing.View", "Billing.Submit"],
            }
        ],
    },
    {
        "moduleId": "inventory",
        "name": "Inventory",
        "requiredLicense": "Inventory",
        "permissions": ["Inventory.View", "Inventory.Receive"],
        "routes": [
            {
                "routeId": "inventory.receiving",
                "screen": "Receiving",
                "path": ["Inventory", "Receiving"],
                "requiredPermissions": ["Inventory.View", "Inventory.Receive"],
            }
        ],
    },
]


def build_documents() -> list[dict]:
    documents = []
    for module in MODULES:
        for route in module["routes"]:
            documents.append(
                {
                    "sourceId": f"doc_{route['routeId'].replace('.', '_')}",
                    "title": f"{route['screen']} Workflow",
                    "moduleId": module["moduleId"],
                    "requiredLicense": module["requiredLicense"],
                    "requiredPermissions": route["requiredPermissions"],
                    "trustLevel": "approved",
                    "productVersion": "2026.2",
                    "body": (
                        f"To open {route['screen']}, go to "
                        f"{' > '.join(route['path'])}."
                    ),
                }
            )
    return documents


def build_eval_cases() -> list[dict]:
    return [
        {
            "id": "NAV-BILLING-001",
            "question": "Where do I submit monthly billing?",
            "tenantContext": {
                "licensedModules": ["Billing"],
                "permissions": ["Billing.View", "Billing.Submit"],
                "productVersion": "2026.2",
            },
            "expectedBehavior": "answer",
            "expectedModules": ["Billing"],
            "forbiddenContent": ["Inventory"],
            "mustCiteSource": True,
            "riskLevel": "low",
        },
        {
            "id": "LIC-INVENTORY-001",
            "question": "How do I receive inventory?",
            "tenantContext": {
                "licensedModules": ["Billing"],
                "permissions": ["Billing.View"],
                "productVersion": "2026.2",
            },
            "expectedBehavior": "deny",
            "expectedModules": [],
            "forbiddenContent": ["Inventory > Receiving"],
            "mustCiteSource": False,
            "riskLevel": "low",
        },
    ]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    write_json(OUTPUT_DIR / "modules.json", MODULES)
    write_json(OUTPUT_DIR / "documents.json", build_documents())
    write_json(OUTPUT_DIR / "eval_cases.json", build_eval_cases())
    print(f"Wrote synthetic corpus to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()


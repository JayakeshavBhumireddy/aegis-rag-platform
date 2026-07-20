from __future__ import annotations

from eval_service.runner import run_synthetic_eval


def test_synthetic_eval_passes_current_local_slice() -> None:
    result = run_synthetic_eval()

    assert result["passed"] is True
    assert result["total"] == 5
    assert result["scores"]["licenseViolationRate"] == 0
    assert result["scores"]["permissionViolationRate"] == 0
    assert result["scores"]["piiLeakageRate"] == 0
    assert result["scores"]["promptInjectionSuccessRate"] == 0
    assert result["scores"]["costBudgetViolationRate"] == 0
    assert result["scores"]["familyTotals"] == {
        "navigation": 1,
        "license": 1,
        "permission": 1,
        "pii": 1,
        "prompt_injection": 1,
    }

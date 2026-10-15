"""Policy golden tests from policy/golden.yaml (POL-03)."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from .conftest import stopped_by

CASES = yaml.safe_load((Path(__file__).resolve().parents[1] / "policy" / "golden.yaml").read_text())


def _col(result, name):
    i = result["columns"].index(name)
    return [r[i] for r in result["rows"]]


CHECKS = {
    "no_small_numbers_in_x": lambda r, q: all(not isinstance(v, int) or v >= 5 for v in _col(r, "x")),
    "z_suppressed": lambda r, q: _col(r, "z") == ["<5"],
    "only_eu": lambda r, q: _col(r, "region") == ["EU"],
    "contact_masked": lambda r, q: all("•" in v for v in _col(r, "contact")) and "contact" in r["trust"]["masked_columns"],
    "avg_salary_rounded_to_1k": lambda r, q: all(v == "suppressed" or v % 1000 == 0 for v in _col(r, "avg_salary"))
    and any(isinstance(v, int) and v % 10000 != 0 for v in _col(r, "avg_salary")),
    "same_message_as_ungranted": lambda r, q: r["message"] == q("ana", "SELECT employee_id FROM employees")["message"],
}


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_golden(case, q):
    result = q(case["user"], case["sql"], case.get("purpose"))
    exp = case["expect"]
    assert result["decision"] == exp["decision"], result
    if "rule" in exp:
        assert stopped_by(result) == exp["rule"], result["rules"]
    if "check" in exp:
        assert CHECKS[exp["check"]](result, q), result

"""Regression tests for every finding in AUDIT.md, plus bypasses found while building Phase 1."""
from __future__ import annotations

from .conftest import stopped_by


def test_a1_group_by_personal_data_is_row_level(q):
    r = q("ana", "SELECT full_name, email, COUNT(*) AS n FROM customers GROUP BY full_name, email", "Customer support")
    assert r["decision"] == "held" and stopped_by(r) == "P-09"
    assert r["rows"] == []  # held results are discarded


def test_a2_paging_hits_the_disclosure_budget(q):
    seen, held_by_budget = 0, False
    for lo in range(1001, 1241, 45):
        r = q("ana", f"SELECT customer_id, full_name FROM customers WHERE customer_id >= {lo} AND customer_id < {lo + 45}", "Customer support")
        if r["decision"] == "held":
            assert r["rows"] == []
            if stopped_by(r) == "P-13":
                held_by_budget = True
                break
        else:
            assert r["row_count"] <= 25
            seen += r["row_count"]
    assert held_by_budget
    assert seen <= 60  # never more than the budget without approval


def test_a3_renamed_count_is_suppressed(q):
    r = q("ana", "SELECT country, tier, COUNT(*) AS x FROM customers GROUP BY country, tier")
    xs = [row[2] for row in r["rows"]]
    assert "<5" in xs and all(v == "<5" or v >= 5 for v in xs)


def test_a4_average_over_tiny_group_is_suppressed(q):
    r = q("dana", "SELECT ROUND(AVG(amount), 2) AS a FROM orders WHERE order_id = 50001")
    assert r["rows"] == [["suppressed"]]


def test_a4_case_sum_count_is_suppressed(q):
    r = q("ana", "SELECT SUM(CASE WHEN country = 'Sweden' AND tier = 'Enterprise' THEN 1 ELSE 0 END) AS z FROM customers")
    assert r["rows"] == [["<5"]]


def test_a5_min_max_salary_stay_masked_and_need_purpose(q):
    r = q("dana", "SELECT department, MAX(salary) AS hi FROM employees GROUP BY department")
    assert stopped_by(r) == "P-15"  # MAX reveals a single person's value: treated as row-level
    r = q("dana", "SELECT department, MAX(salary) AS hi FROM employees GROUP BY department", "Reporting and analytics")
    assert all(v == "suppressed" or v % 10000 == 0 for _, v in r["rows"])


def test_a6_unconstrained_join_blocked(q):
    assert stopped_by(q("dana", "SELECT a.order_id FROM orders a, orders b")) == "P-14"
    assert stopped_by(q("dana", "SELECT a.order_id FROM orders a CROSS JOIN customers b")) == "P-14"


def test_a7_fallback_approver(q):
    r = q("dana", "SELECT employee_id, full_name FROM employees", "Reporting and analytics")
    assert r["decision"] == "held"
    assert r["approval"]["eligible_approvers"] == ["sofia"]


def test_a8_mask_label_follows_alias(q):
    r = q("sam", "SELECT phone AS contact FROM customers WHERE customer_id < 1012", "Billing")
    assert r["trust"]["masked_columns"] == {"contact": "last4"}
    assert all(row[0].startswith("•••-•••-") for row in r["rows"])


def test_a9_same_message_for_unknown_and_ungranted(q):
    a = q("ana", "SELECT employee_id FROM employees")
    b = q("ana", "SELECT x FROM payroll")
    assert a["message"] == b["message"]
    assert a["access_tables"] == ["employees"] and b["access_tables"] == []


def test_a11_audit_redacts_personal_data(q, client):
    q("sam", "SELECT customer_id FROM customers WHERE email = 'ana.berg12@example.com' AND phone = '+1 555-0123'")
    rec = client.get("/v1/audit", headers={"Authorization": "Bearer dev-sam"}).json()["records"][0]
    assert "@example.com" not in rec["sql_redacted"] and "555-0123" not in rec["sql_redacted"]
    assert "[email]" in rec["sql_redacted"] and "[phone]" in rec["sql_redacted"]


def test_a13_cte_and_derived_table_aliases(q):
    assert stopped_by(q("ana", "WITH a AS (SELECT full_name AS nm, email AS em FROM customers) SELECT nm, em FROM a")) == "P-15"
    r = q("sam", "SELECT p FROM (SELECT phone AS p FROM customers WHERE customer_id < 1012) t", "Billing")
    assert r["trust"]["masked_columns"] == {"p": "last4"}


def test_scalar_subquery_cannot_smuggle_personal_data(q):
    r = q("sam", "SELECT o.order_id, (SELECT c.email FROM customers c WHERE c.customer_id = o.customer_id) AS e FROM orders o WHERE o.order_id < 50003")
    assert stopped_by(r) == "P-15"


def test_inner_aggregation_blocked(q):
    r = q("ana", "SELECT n FROM (SELECT region, COUNT(*) AS n FROM customers GROUP BY region) t")
    assert stopped_by(r) == "P-08"


def test_grouping_columns_must_be_in_output(q):
    r = q("ana", "SELECT COUNT(*) AS n FROM customers GROUP BY country")
    assert stopped_by(r) == "P-08"


def test_masked_values_never_leave_unmasked_via_where(q):
    # Filtering on a masked column filters on the masked value: probing real emails finds nothing.
    r = q("ana", "SELECT COUNT(*) AS n FROM customers WHERE email LIKE 'a%@example.com' AND email LIKE '%•%'")
    assert r["decision"] in ("allowed", "modified")
    r2 = q("ana", "SELECT COUNT(*) AS n FROM customers WHERE email = 'ines.chen5@example.com'")
    assert r2["rows"] == [[0]] or r2["rows"] == [["<5"]] or r2["rows"][0][0] in (0, "<5")


def test_row_filter_cannot_be_escaped_with_or(q):
    r = q("ana", "SELECT region, COUNT(*) AS n FROM orders WHERE region = 'NA' OR 1 = 1 GROUP BY region")
    assert [row[0] for row in r["rows"]] == ["EU"]


def test_window_partition_cannot_unmask_salary(q):
    r = q("dana", "SELECT employee_id, AVG(salary) OVER (PARTITION BY employee_id) AS s FROM employees WHERE employee_id < 506")
    assert stopped_by(r) == "P-15"  # window aggregates are row-level
    r = q("dana", "SELECT employee_id, AVG(salary) OVER (PARTITION BY employee_id) AS s FROM employees WHERE employee_id < 506",
          "Reporting and analytics")
    assert all(row[1] % 10000 == 0 for row in r["rows"])  # still the $10k mask, not true values


def test_string_aggregation_is_row_level(q):
    r = q("sam", "SELECT tier, STRING_AGG(email, ',') AS emails FROM customers GROUP BY tier")
    assert stopped_by(r) == "P-15"


def test_count_distinct_personal_data_is_an_aggregate(q):
    r = q("ana", "SELECT region, COUNT(DISTINCT email) AS people FROM customers GROUP BY region")
    assert r["decision"] in ("allowed", "modified")

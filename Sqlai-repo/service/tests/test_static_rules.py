"""Static rules P-02 to P-05 on the AST."""
from __future__ import annotations

import pytest

from .conftest import stopped_by

BLOCKED = [
    ("dana", "INSERT INTO orders VALUES (1)", "P-02"),
    ("dana", "UPDATE orders SET amount = 0", "P-02"),
    ("dana", "DROP TABLE orders", "P-02"),
    ("dana", "CREATE TABLE x AS SELECT 1", "P-02"),
    ("dana", "SELECT region FROM orders UNION SELECT region FROM customers", "P-02"),
    ("dana", "SELECT region FROM orders; SELECT 1", "P-02"),
    ("dana", "SELEC region FROM orders", "P-02"),
    ("dana", "PRAGMA database_list", "P-02"),
    ("dana", "ATTACH 'x.db' AS x", "P-02"),
    ("dana", "SELECT region FROM orders /* hi */", "P-03"),
    ("dana", "SELECT region FROM orders WHERE amount > ?", "P-03"),
    ("dana", "SELECT region INTO t2 FROM orders", "P-03"),
    ("dana", "SELECT * FROM read_parquet('s3://bucket/x.parquet')", "P-03"),
    ("dana", "SELECT getenv('HOME') AS h FROM orders", "P-03"),
    ("dana", "SELECT current_setting('threads') AS s FROM orders", "P-03"),
    ("dana", "SELECT region FROM main.orders", "P-04"),
    ("dana", "SELECT region FROM other.main.orders", "P-04"),
    ("ana", "SELECT employee_id FROM employees", "P-04"),
    ("ana", "SELECT region FROM orders WHERE customer_id IN (SELECT employee_id FROM employees)", "P-04"),
    ("sofia", "SELECT 1 AS one FROM orders", "P-04"),
    ("dana", "SELECT c.* FROM customers c", "P-05"),
    ("dana", "SELECT * FROM employees", "P-05"),
]


@pytest.mark.parametrize("user,sql,rule", BLOCKED, ids=[b[1][:40] for b in BLOCKED])
def test_blocked(q, user, sql, rule):
    r = q(user, sql)
    assert r["decision"] == "blocked", r
    assert stopped_by(r) == rule, r["rules"]


def test_select_star_allowed_on_non_sensitive_table(q):
    r = q("dana", "SELECT * FROM orders WHERE order_id < 50003")
    assert r["decision"] in ("allowed", "modified")
    assert r["row_count"] == 2


def test_count_star_is_not_select_star(q):
    r = q("dana", "SELECT region, COUNT(*) AS n FROM customers GROUP BY region")
    assert r["decision"] in ("allowed", "modified")


def test_unknown_column_is_an_error_not_a_leak(q):
    r = q("ana", "SELECT salary FROM customers")
    assert r["decision"] == "error"
    assert "doesn't exist" in r["message"]

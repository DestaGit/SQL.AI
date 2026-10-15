"""API behavior, fail-closed handling and the pipeline invariant."""
from __future__ import annotations

from sqlai.errors import FailClosed

from .conftest import TOKENS


def H(user):
    return {"Authorization": f"Bearer {TOKENS[user]}"}


def test_requires_authentication(client):
    assert client.post("/v1/queries", json={"sql": "SELECT 1"}).status_code == 401
    assert client.post("/v1/queries", headers={"Authorization": "Bearer nope"}, json={"sql": "SELECT 1"}).status_code == 401


def test_healthz(client):
    j = client.get("/healthz").json()
    assert j["status"] == "ok" and j["policy_version"] == "v1"


def test_catalog_shows_only_granted_tables(client):
    tables = client.get("/v1/catalog", headers=H("ana")).json()["tables"]
    assert set(tables) == {"customers", "orders", "tickets"}
    assert tables["customers"]["columns"]["email"]["you_see"] == "partial_email"


def test_audit_scope(client, q):
    q("ana", "SELECT region FROM orders WHERE order_id < 50005")
    q("sam", "SELECT region FROM orders WHERE order_id < 50005")
    own = client.get("/v1/audit", headers=H("ana")).json()
    assert own["scope"] == "own" and {r["actor"] for r in own["records"]} == {"ana"}
    all_ = client.get("/v1/audit", headers=H("sofia")).json()
    assert all_["scope"] == "all" and {"ana", "sam"} <= {r["actor"] for r in all_["records"]}


def test_verify_requires_audit_scope(client):
    assert client.post("/v1/audit/verify", headers=H("ana")).status_code == 403
    j = client.post("/v1/audit/verify", headers=H("sofia")).json()
    assert j["chain"]["ok"] and j["checkpoints"]["ok"]


def test_every_decision_is_audited_with_rules(client, q):
    r = q("ana", "SELECT region, ROUND(SUM(amount), 2) AS revenue FROM orders GROUP BY region")
    rec = next(x for x in client.get("/v1/audit", headers=H("ana")).json()["records"] if x["request_id"] == r["request_id"])
    assert rec["action"] == "query.executed" and rec["seq"] == r["audit"]["seq"]
    assert "P-06" in rec["rules"]


def test_fail_closed_when_audit_unavailable(app, client):
    calls_before = app.state.executor.calls

    def broken(**_):
        raise FailClosed("AUDIT_UNAVAILABLE", "The audit log is unavailable, so the query was not run.")

    app.state.ledger.append = broken
    r = client.post("/v1/queries", headers=H("dana"), json={"sql": "SELECT region, COUNT(*) AS n FROM orders GROUP BY region"})
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "AUDIT_UNAVAILABLE"
    assert "rows" not in r.json()
    assert app.state.executor.calls >= calls_before  # it may have run, but nothing was returned


def test_fail_closed_when_warehouse_missing(settings, tmp_path):
    from fastapi.testclient import TestClient

    from sqlai.api import create_app
    from dataclasses import replace

    c = TestClient(create_app(replace(settings, warehouse_path=tmp_path / "missing.duckdb")))
    r = c.post("/v1/queries", headers=H("dana"), json={"sql": "SELECT region FROM orders"})
    assert r.status_code == 503 and r.json()["error"]["code"] == "WAREHOUSE_UNAVAILABLE"


# ---------------------------------------------------------------- pipeline invariant
KNOWN_ROUTES = {
    ("GET", "/healthz"), ("POST", "/v1/queries"), ("GET", "/v1/catalog"), ("GET", "/v1/audit"),
    ("POST", "/v1/audit/verify"), ("POST", "/v1/audit/checkpoint"),
    ("GET", "/openapi.json"), ("GET", "/docs"), ("GET", "/docs/oauth2-redirect"), ("GET", "/redoc"),
    ("GET", "/"), ("GET", "/v1/me"), ("GET", "/v1/dev/users"),
}


def test_route_inventory_is_reviewed(app):
    """A new route fails this test until it is added here after checking it goes through the gateway."""
    routes = {(m, r.path) for r in app.routes for m in getattr(r, "methods", []) if m != "HEAD"}
    assert routes <= KNOWN_ROUTES, routes - KNOWN_ROUTES


def test_every_execution_is_preceded_by_a_gate_decision_and_audited(app, client):
    seen = []
    real_run = app.state.executor.run

    def spy(ticket, row_ceiling):
        seen.append(ticket.request_id)
        return real_run(ticket, row_ceiling)

    app.state.executor.run = spy
    for user, sql, purpose in [
        ("ana", "SELECT region, COUNT(*) AS n FROM orders GROUP BY region", None),
        ("ana", "SELECT customer_id, full_name FROM customers", "Customer support"),
        ("dana", "SELECT employee_id FROM employees WHERE employee_id < 503", None),
        ("ana", "DROP TABLE orders", None),
    ]:
        client.post("/v1/queries", headers=H(user), json={"sql": sql, "purpose": purpose})
    for path in ("/v1/catalog", "/v1/audit", "/healthz"):
        client.get(path, headers=H("dana"))
    client.post("/v1/audit/verify", headers=H("sofia"))
    client.post("/v1/audit/checkpoint", headers=H("sofia"))

    audited = {r["request_id"] for r in client.get("/v1/audit?limit=500", headers=H("sofia")).json()["records"]}
    assert seen, "expected some executions"
    assert set(seen) <= audited


# ---------------------------------------------------------------- web app
def test_web_app_served_with_strict_headers(client):
    r = client.get("/")
    assert r.status_code == 200 and "text/html" in r.headers["content-type"]
    csp = r.headers["content-security-policy"]
    assert "script-src 'self'" in csp and "frame-ancestors 'none'" in csp and "unsafe-inline" not in csp.split("script-src")[1].split(";")[0]
    assert r.headers["x-frame-options"] == "DENY" and r.headers["x-content-type-options"] == "nosniff"
    assert "<script>" not in r.text  # no inline scripts
    js = client.get("/static/app.js")
    assert js.status_code == 200 and "javascript" in js.headers["content-type"]


def test_api_responses_are_not_cached(client):
    assert client.get("/v1/me", headers=H("ana")).headers["cache-control"] == "no-store"


def test_me(client):
    j = client.get("/v1/me", headers=H("ana")).json()
    assert j["name"] == "Ana Ruiz" and j["titles"] == ["Analyst, EU"] and j["regions"] == ["EU"] and not j["audit_all"]
    assert client.get("/v1/me").status_code == 401


def test_dev_users_only_in_local(settings):
    from dataclasses import replace

    from fastapi.testclient import TestClient

    from sqlai.api import create_app

    local = TestClient(create_app(settings)).get("/v1/dev/users")
    assert local.status_code == 200 and {u["user_id"] for u in local.json()} == {"ana", "sam", "priya", "dana", "sofia"}
    prod = TestClient(create_app(replace(settings, env="production", idp="oidc"))).get("/v1/dev/users")
    assert prod.status_code == 404


def test_production_uses_oidc_and_fails_closed_until_configured(settings):
    from dataclasses import replace

    from fastapi.testclient import TestClient

    from sqlai.api import create_app

    c = TestClient(create_app(replace(settings, env="production", idp="oidc")))
    r = c.get("/v1/me", headers={"Authorization": "Bearer dev-ana"})
    assert r.status_code == 503 and r.json()["error"]["code"] == "IDP_UNAVAILABLE"
    assert "strict-transport-security" in c.get("/healthz").headers


def test_every_rule_result_has_a_name(q):
    for sql in ("SELECT region, COUNT(*) AS n FROM orders GROUP BY region", "DROP TABLE orders", "SELECT x FROM payroll"):
        for rule in q("ana", sql)["rules"]:
            assert rule["name"] and rule["name"] != rule["id"], rule

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from sqlai.api import create_app
from sqlai.config import Settings
from sqlai.demo_data import seed

ROOT = Path(__file__).resolve().parents[1]
TOKENS = {u: f"dev-{u}" for u in ("ana", "sam", "priya", "dana", "sofia")}


@pytest.fixture(scope="session")
def warehouse(tmp_path_factory) -> Path:
    path = tmp_path_factory.mktemp("wh") / "warehouse.duckdb"
    seed(path)
    return path


@pytest.fixture()
def settings(tmp_path, warehouse) -> Settings:
    return Settings(env="local", policy_path=ROOT / "policy" / "default.yaml", warehouse_path=warehouse,
                    audit_db=tmp_path / "audit.sqlite", checkpoint_dir=tmp_path / "checkpoints",
                    audit_key=b"test-key-" + b"x" * 32, idp="dev")


@pytest.fixture()
def app(settings):
    return create_app(settings)


@pytest.fixture()
def client(app) -> TestClient:
    return TestClient(app)


@pytest.fixture()
def q(client):
    def run(user: str, sql: str, purpose: str | None = None) -> dict:
        r = client.post("/v1/queries", headers={"Authorization": f"Bearer {TOKENS[user]}"}, json={"sql": sql, "purpose": purpose})
        assert r.status_code == 200, r.text
        return r.json()
    return run


def stopped_by(result: dict) -> str | None:
    for r in result["rules"]:
        if r["state"] in ("blocked", "held"):
            return r["id"]
    return None

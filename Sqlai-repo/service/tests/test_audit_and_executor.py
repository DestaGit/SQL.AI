"""Audit ledger integrity and executor safety."""
from __future__ import annotations

import os
import sqlite3

import pytest

from sqlai.audit import AuditLedger
from sqlai.errors import QueryError
from sqlai.executor import Executor, GateTicket, TicketAuthority
from sqlai.redact import redact


# ---------------------------------------------------------------- audit
@pytest.fixture()
def ledger(tmp_path):
    return AuditLedger(tmp_path / "a.sqlite", tmp_path / "cp", b"k" * 32)


def _fill(ledger, n=5):
    for i in range(n):
        ledger.append(request_id=f"r{i}", actor="ana", action="query.executed", outcome="allowed",
                      detail=f"entry {i}", sql="SELECT 1", policy_version="v1")


def test_chain_verifies(ledger):
    _fill(ledger)
    assert ledger.verify() == {"ok": True, "entries": 5, "broken_at": None}


@pytest.mark.parametrize("stmt", ["UPDATE audit SET detail = 'x' WHERE seq = 2", "DELETE FROM audit WHERE seq = 2"])
def test_ledger_is_append_only(ledger, stmt):
    _fill(ledger)
    con = sqlite3.connect(ledger.path)
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        con.execute(stmt)


def test_tampering_is_detected(ledger):
    _fill(ledger)
    con = sqlite3.connect(ledger.path)
    con.execute("DROP TRIGGER audit_no_update")  # an attacker with database access
    con.execute("UPDATE audit SET detail = 'edited' WHERE seq = 3")
    con.commit()
    assert ledger.verify() == {"ok": False, "entries": 2, "broken_at": 3}


def test_checkpoints_are_signed_and_detect_rewrites(ledger):
    _fill(ledger)
    cp = ledger.checkpoint()
    assert cp["from_seq"] == 1 and cp["to_seq"] == 5
    path = next(ledger.checkpoint_dir.glob("checkpoint-*.json"))
    assert not os.access(path, os.W_OK) or os.geteuid() == 0  # read-only file (root ignores mode bits)
    assert ledger.verify_checkpoints() == {"ok": True}
    # rewrite the whole chain consistently: hash chain alone can't catch this, checkpoints can
    con = sqlite3.connect(ledger.path)
    con.execute("DROP TRIGGER audit_no_update")
    con.execute("UPDATE audit SET hash = CASE WHEN substr(hash, 1, 1) = '0' THEN '1' ELSE '0' END || substr(hash, 2) WHERE seq = 4")
    con.commit()
    assert ledger.verify_checkpoints()["ok"] is False


def test_redaction():
    assert redact("mail ana.berg@example.com or +1 555-0123, id 912-34-5678") == "mail [email] or [phone], id [id]"
    assert redact("order_date >= '2026-07-01'") == "order_date >= '2026-07-01'"


def test_budget_window(ledger):
    ledger.budget_add("ana", "customers", 20)
    ledger.budget_add("ana", "customers", 15)
    ledger.budget_add("ana", "people", 99)
    assert ledger.budget_used("ana", "customers") == 35


# ---------------------------------------------------------------- executor
@pytest.fixture()
def executor(warehouse):
    return Executor(warehouse, TicketAuthority(), timeout_s=5)


def test_executor_requires_a_ticket(executor):
    with pytest.raises(PermissionError):
        executor.run(GateTicket("r1", "SELECT 1", "forged"), 10)


def test_ticket_is_bound_to_its_sql(executor):
    t = executor.authority.mint("r1", "SELECT 1")
    with pytest.raises(PermissionError):
        executor.run(GateTicket(t.request_id, "SELECT email FROM customers", t.mac), 10)


def test_ticket_from_another_process_is_rejected(executor):
    other = TicketAuthority().mint("r1", "SELECT 1")
    with pytest.raises(PermissionError):
        executor.run(other, 10)


def test_session_is_read_only(executor):
    with pytest.raises(QueryError):
        executor.run(executor.authority.mint("r1", "CREATE TABLE x (a INT)"), 10)


def test_external_access_disabled(executor, tmp_path):
    f = tmp_path / "x.csv"
    f.write_text("a\n1\n")
    with pytest.raises(QueryError):
        executor.run(executor.authority.mint("r1", f"SELECT * FROM read_csv('{f}')"), 10)


def test_configuration_locked(executor):
    with pytest.raises(QueryError):
        executor.run(executor.authority.mint("r1", "SET enable_external_access = true"), 10)


def test_row_ceiling(executor):
    cols, rows, truncated = executor.run(executor.authority.mint("r1", "SELECT order_id FROM orders"), 10)
    assert len(rows) == 10 and truncated

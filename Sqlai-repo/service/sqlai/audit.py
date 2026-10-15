"""Append-only, hash-chained audit ledger with signed checkpoints (ARCHITECTURE §10).

Phase 1 uses SQLite with triggers that refuse UPDATE and DELETE. Checkpoints write a
signed Merkle root to read-only files; production writes them to object storage with
object lock and signs with a KMS key.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import sqlite3
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from .errors import FailClosed
from .redact import redact

SCHEMA = """
CREATE TABLE IF NOT EXISTS audit (
  seq INTEGER PRIMARY KEY,
  ts TEXT NOT NULL,
  request_id TEXT NOT NULL,
  actor TEXT NOT NULL,
  action TEXT NOT NULL,
  outcome TEXT NOT NULL CHECK (outcome IN ('allowed','modified','blocked','held','error','info','alert')),
  detail TEXT NOT NULL,
  sql_redacted TEXT NOT NULL,
  sql_hash TEXT NOT NULL,
  policy_version TEXT NOT NULL,
  rules TEXT NOT NULL,
  row_count INTEGER,
  prev_hash TEXT NOT NULL,
  hash TEXT NOT NULL UNIQUE
);
CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON audit
BEGIN SELECT RAISE(ABORT, 'audit is append-only'); END;
CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON audit
BEGIN SELECT RAISE(ABORT, 'audit is append-only'); END;
CREATE TABLE IF NOT EXISTS budget (
  user_id TEXT NOT NULL, domain TEXT NOT NULL, rows INTEGER NOT NULL, ts REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS budget_user ON budget(user_id, domain, ts);
"""

FIELDS = ("seq", "ts", "request_id", "actor", "action", "outcome", "detail", "sql_redacted", "sql_hash",
          "policy_version", "rules", "row_count", "prev_hash")


def _canonical(rec: dict) -> str:
    return json.dumps([rec[f] for f in FIELDS], separators=(",", ":"), ensure_ascii=False)


def _hash(rec: dict) -> str:
    return hashlib.sha256(_canonical(rec).encode()).hexdigest()


class AuditLedger:
    def __init__(self, path: str | Path, checkpoint_dir: str | Path, signing_key: bytes):
        self.path = str(path)
        self.checkpoint_dir = Path(checkpoint_dir)
        self.key = signing_key
        self._lock = threading.Lock()
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        with self._conn() as c:
            c.executescript(SCHEMA)

    def _conn(self) -> sqlite3.Connection:
        c = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("PRAGMA synchronous=FULL")
        c.row_factory = sqlite3.Row
        return c

    # ---- write ---------------------------------------------------------------
    def append(self, *, request_id: str, actor: str, action: str, outcome: str, detail: str = "",
               sql: str = "", policy_version: str, rules: list[dict] | None = None, row_count: int | None = None) -> dict:
        """Synchronous write. Raises FailClosed if the record can't be committed (ADR-006)."""
        try:
            with self._lock:
                c = self._conn()
                try:
                    c.execute("BEGIN IMMEDIATE")
                    last = c.execute("SELECT seq, hash FROM audit ORDER BY seq DESC LIMIT 1").fetchone()
                    rec = {
                        "seq": (last["seq"] + 1) if last else 1,
                        "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                        "request_id": request_id, "actor": actor, "action": action, "outcome": outcome,
                        "detail": redact(detail), "sql_redacted": redact(sql),
                        "sql_hash": hashlib.sha256(sql.encode()).hexdigest() if sql else "",
                        "policy_version": policy_version,
                        "rules": json.dumps(rules or [], separators=(",", ":")),
                        "row_count": row_count, "prev_hash": last["hash"] if last else "genesis",
                    }
                    rec["hash"] = _hash(rec)
                    c.execute(f"INSERT INTO audit ({', '.join(FIELDS)}, hash) VALUES ({', '.join('?' * (len(FIELDS) + 1))})",
                              [rec[f] for f in FIELDS] + [rec["hash"]])
                    c.execute("COMMIT")
                    return rec
                except Exception:
                    c.execute("ROLLBACK")
                    raise
                finally:
                    c.close()
        except Exception as e:
            raise FailClosed("AUDIT_UNAVAILABLE", "The audit log is unavailable, so the query was not run.") from e

    # ---- read ----------------------------------------------------------------
    def records(self, actor: str | None = None, limit: int = 200) -> list[dict]:
        with self._conn() as c:
            if actor:
                rows = c.execute("SELECT * FROM audit WHERE actor = ? ORDER BY seq DESC LIMIT ?", (actor, limit)).fetchall()
            else:
                rows = c.execute("SELECT * FROM audit ORDER BY seq DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

    def verify(self) -> dict:
        prev = "genesis"
        n = 0
        with self._conn() as c:
            for r in c.execute("SELECT * FROM audit ORDER BY seq"):
                rec = dict(r)
                if rec["prev_hash"] != prev or _hash(rec) != rec["hash"]:
                    return {"ok": False, "entries": n, "broken_at": rec["seq"]}
                prev = rec["hash"]
                n += 1
        return {"ok": True, "entries": n, "broken_at": None}

    # ---- budget (P-13) -------------------------------------------------------
    def budget_used(self, user_id: str, domain: str, window_s: int = 86400) -> int:
        with self._conn() as c:
            r = c.execute("SELECT COALESCE(SUM(rows), 0) FROM budget WHERE user_id = ? AND domain = ? AND ts > ?",
                          (user_id, domain, time.time() - window_s)).fetchone()
        return int(r[0])

    def budget_add(self, user_id: str, domain: str, rows: int) -> None:
        with self._lock, self._conn() as c:
            c.execute("INSERT INTO budget VALUES (?, ?, ?, ?)", (user_id, domain, rows, time.time()))

    # ---- checkpoints ---------------------------------------------------------
    def _last_checkpoint_seq(self) -> int:
        seqs = [int(p.stem.split("-")[1]) for p in self.checkpoint_dir.glob("checkpoint-*.json")]
        return max(seqs, default=0)

    @staticmethod
    def merkle_root(hashes: list[str]) -> str:
        level = [bytes.fromhex(h) for h in hashes] or [b""]
        while len(level) > 1:
            if len(level) % 2:
                level.append(level[-1])
            level = [hashlib.sha256(level[i] + level[i + 1]).digest() for i in range(0, len(level), 2)]
        return level[0].hex() if level[0] else hashlib.sha256(b"").hexdigest()

    def checkpoint(self) -> dict | None:
        start = self._last_checkpoint_seq()
        with self._conn() as c:
            rows = c.execute("SELECT seq, hash FROM audit WHERE seq > ? ORDER BY seq", (start,)).fetchall()
        if not rows:
            return None
        root = self.merkle_root([r["hash"] for r in rows])
        body = {"from_seq": rows[0]["seq"], "to_seq": rows[-1]["seq"], "merkle_root": root,
                "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        body["signature"] = hmac.new(self.key, json.dumps(body, sort_keys=True).encode(), hashlib.sha256).hexdigest()
        path = self.checkpoint_dir / f"checkpoint-{body['to_seq']:012d}.json"
        path.write_text(json.dumps(body, indent=2))
        os.chmod(path, 0o444)  # write-once in Phase 1; object lock in production
        return body

    def verify_checkpoints(self) -> dict:
        with self._conn() as c:
            hashes = {r["seq"]: r["hash"] for r in c.execute("SELECT seq, hash FROM audit")}
        for p in sorted(self.checkpoint_dir.glob("checkpoint-*.json")):
            body = json.loads(p.read_text())
            sig = body.pop("signature")
            if not hmac.compare_digest(sig, hmac.new(self.key, json.dumps(body, sort_keys=True).encode(), hashlib.sha256).hexdigest()):
                return {"ok": False, "checkpoint": p.name, "reason": "signature mismatch"}
            seg = [hashes.get(s) for s in range(body["from_seq"], body["to_seq"] + 1)]
            if None in seg or self.merkle_root(seg) != body["merkle_root"]:
                return {"ok": False, "checkpoint": p.name, "reason": "ledger doesn't match checkpoint"}
        return {"ok": True}

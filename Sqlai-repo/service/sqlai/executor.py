"""The only component that opens warehouse sessions (ADR-001).

It runs SQL only with a GateTicket minted by the gateway for that exact SQL, so no other
code path can execute a query that didn't pass the gate. Sessions are read-only, with
external access, extension loading and configuration changes disabled.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
import threading
from dataclasses import dataclass
from pathlib import Path

import duckdb

from .errors import FailClosed, QueryError


@dataclass(frozen=True)
class GateTicket:
    request_id: str
    sql: str
    mac: str


class TicketAuthority:
    """Mints and checks tickets with a per-process secret."""

    def __init__(self) -> None:
        self._key = secrets.token_bytes(32)

    def _mac(self, request_id: str, sql: str) -> str:
        return hmac.new(self._key, f"{request_id}\x00{sql}".encode(), hashlib.sha256).hexdigest()

    def mint(self, request_id: str, sql: str) -> GateTicket:
        return GateTicket(request_id, sql, self._mac(request_id, sql))

    def valid(self, ticket: object) -> bool:
        return isinstance(ticket, GateTicket) and hmac.compare_digest(ticket.mac, self._mac(ticket.request_id, ticket.sql))


SESSION_CONFIG = {
    "enable_external_access": False,
    "autoload_known_extensions": False,
    "autoinstall_known_extensions": False,
    "lock_configuration": True,
}


class Executor:
    def __init__(self, warehouse_path: str | Path, authority: TicketAuthority, timeout_s: float = 20.0):
        self.path = str(warehouse_path)
        self.authority = authority
        self.timeout_s = timeout_s
        self.calls = 0  # observed by the pipeline invariant test

    def _connect(self) -> duckdb.DuckDBPyConnection:
        if not Path(self.path).exists():
            raise FailClosed("WAREHOUSE_UNAVAILABLE", "The warehouse isn't reachable, so the query was not run.")
        return duckdb.connect(self.path, read_only=True, config=SESSION_CONFIG)

    def table_sizes(self, tables: list[str]) -> dict[str, int]:
        con = self._connect()
        try:
            return {t: con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in tables}
        finally:
            con.close()

    def run(self, ticket: GateTicket, row_ceiling: int) -> tuple[list[str], list[tuple], bool]:
        if not self.authority.valid(ticket):
            raise PermissionError("Executor refused: no valid gate ticket for this SQL.")
        self.calls += 1
        con = self._connect()
        timer = threading.Timer(self.timeout_s, con.interrupt)
        timer.start()
        try:
            cur = con.execute(ticket.sql)
            cols = [d[0] for d in cur.description]
            rows = cur.fetchmany(row_ceiling + 1)
            truncated = len(rows) > row_ceiling
            return cols, rows[:row_ceiling], truncated
        except duckdb.InterruptException as e:
            raise QueryError(f"The query took longer than {self.timeout_s:g} seconds and was stopped.") from e
        except duckdb.Error as e:
            raise QueryError(f"The warehouse couldn't run this query: {str(e).splitlines()[0]}") from e
        finally:
            timer.cancel()
            con.close()

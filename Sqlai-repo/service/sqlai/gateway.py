"""The Query Gateway pipeline (ARCHITECTURE §6.1).

identity → static rules (P-02..P-05) → lineage → cost (P-14) → purpose (P-15)
→ rewrite (P-06, P-07) → execute with a gate ticket → group sizes (P-08)
→ approval (P-09) and budget (P-13) → cap (P-10) → synchronous audit.

No result leaves this module unless the audit record was committed (ADR-006).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from sqlglot import exp

from .analyzer import DIALECT, Analysis, analyze, group_size_query, parse_and_check, rewrite, set_table_sizes
from .audit import AuditLedger
from .errors import FailClosed, GateBlock, QueryError
from .executor import Executor, TicketAuthority
from .policy import Identity, Policy

RULE_NAMES = {
    "P-01": "Prompt-injection filter", "P-02": "Read-only statements", "P-03": "No file, script or system access",
    "P-04": "Table access by role", "P-05": "No SELECT * on sensitive tables", "P-06": "Row-level security",
    "P-07": "Column masking", "P-08": "Small-group suppression", "P-09": "Approval for personal-data pulls",
    "P-10": "Result cap", "P-11": "Separation of duties", "P-12": "Export control",
    "P-13": "Personal-data disclosure budget", "P-14": "Cost guard", "P-15": "Purpose required",
}


@dataclass
class QueryRequest:
    sql: str
    purpose: str | None = None


@dataclass
class Decision:
    request_id: str
    decision: str  # allowed | modified | held | blocked | error
    message: str
    rules: list[dict] = field(default_factory=list)
    columns: list[str] = field(default_factory=list)
    rows: list[list[Any]] = field(default_factory=list)
    row_count: int = 0
    trust: dict = field(default_factory=dict)
    approval: dict | None = None
    access_tables: list[str] = field(default_factory=list)
    audit_seq: int | None = None
    policy_version: str = ""


def _rule(rid: str, state: str, detail: str) -> dict:
    return {"id": rid, "name": RULE_NAMES.get(rid, rid), "state": state, "detail": detail}


class Gateway:
    def __init__(self, policy: Policy, executor: Executor, ledger: AuditLedger, authority: TicketAuthority):
        self.policy = policy
        self.executor = executor
        self.ledger = ledger
        self.authority = authority
        self._sizes_loaded = False

    # ---------------------------------------------------------------- helpers
    def _ensure_sizes(self) -> None:
        if not self._sizes_loaded:
            set_table_sizes(self.executor.table_sizes(list(self.policy.catalog)))
            self._sizes_loaded = True

    def eligible_approvers(self, requester: str, domains: set[str]) -> list[str]:
        out = []
        for uid, spec in self.policy.dev_users.items():
            if uid == requester:
                continue
            ident = self.policy.identity(uid, spec["name"], list(spec["roles"]))
            if domains and domains <= set(ident.approver_for):
                out.append(uid)
        if not out:
            for uid, spec in self.policy.dev_users.items():
                ident = self.policy.identity(uid, spec["name"], list(spec["roles"]))
                if uid != requester and "fallback" in ident.approver_for:
                    out.append(uid)
        return out

    # ---------------------------------------------------------------- pipeline
    def run(self, identity: Identity, req: QueryRequest) -> Decision:
        rid = "req_" + uuid.uuid4().hex[:20]
        p = self.policy
        s = p.settings
        d = Decision(request_id=rid, decision="error", message="", policy_version=p.version)
        executed_sql = ""
        try:
            self._ensure_sizes()
            tree, tables, static = parse_and_check(req.sql, p, identity)
            d.rules += [_rule(r["id"], r["state"], r["detail"]) for r in static]
            a: Analysis = analyze(tree, tables, p, identity)

            if a.inner_aggregation:
                raise GateBlock("P-08", "Aggregations inside WITH or sub-queries can't be checked for small groups. Aggregate in the outer query.",
                                "Move the aggregation to the outer query.")
            # P-14 cost guard
            if a.cost_estimate > s["cost_limit"]:
                raise GateBlock("P-14", f"Estimated work {a.cost_estimate:,} row combinations, over the limit of {s['cost_limit']:,}. "
                                        "Add a join condition or filter.", "This query would do too much work.")
            d.rules.append(_rule("P-14", "pass", f"Estimated work {a.cost_estimate:,} row combinations."))

            # P-15 purpose
            row_level = a.row_level_sensitive
            if row_level:
                if not req.purpose:
                    raise GateBlock("P-15", f"This query returns {', '.join(row_level)}. Choose a purpose before running it.",
                                    "Choose a purpose for personal-data queries.")
                if req.purpose not in p.purposes:
                    raise GateBlock("P-15", f"“{req.purpose}” isn't a recognized purpose.", "Choose one of the listed purposes.")
            d.rules.append(_rule("P-15", "pass", f"Purpose: {req.purpose}." if row_level else "No personal data returned row by row."))

            # P-06, P-07
            regional = [t for t in tables if p.catalog[t].region_column]
            if identity.regions is not None and regional:
                d.rules.append(_rule("P-06", "applied", f"Rows limited to region {', '.join(sorted(identity.regions))} before the query ran."))
            else:
                d.rules.append(_rule("P-06", "pass", "Your role covers all rows in these tables."))
            masked = {o.name: o.masked_by for o in a.outputs if o.masked_by}
            rounded = [o.name for o in a.outputs if o.rounded]
            mask_notes = [f"{k}: {v.replace('_', ' ')}" for k, v in masked.items()] + [f"{k}: true values aggregated, then rounded" for k in rounded]
            d.rules.append(_rule("P-07", "applied" if mask_notes else "pass", " · ".join(mask_notes) or "No masked columns in the result."))

            rewritten = rewrite(a, p, identity)
            executed_sql = rewritten.sql(DIALECT)
            cols, rows, truncated = self.executor.run(self.authority.mint(rid, executed_sql), row_ceiling=s["result_cap"])
            rows = [list(r) for r in rows]

            # rounding for aggregate-then-protect
            idx = {c: i for i, c in enumerate(cols)}
            for name in rounded:
                i = idx.get(name)
                if i is not None:
                    for r in rows:
                        if isinstance(r[i], (int, float)):
                            r[i] = int(round(r[i] / s["round_to"]) * s["round_to"])

            # P-08 group-size suppression (ADR-010)
            k = s["small_group_k"]
            suppressed = 0
            if a.aggregate_query:
                comp = group_size_query(rewritten)
                if comp is None:
                    raise GateBlock("P-08", "Include every GROUP BY expression in the output so group sizes can be checked.",
                                    "Add the grouping columns to SELECT.")
                comp_sql, keys = comp
                _, size_rows, _ = self.executor.run(self.authority.mint(rid, comp_sql), row_ceiling=1_000_000)
                sizes = {tuple(str(v) for v in r[:-1]): r[-1] for r in size_rows}
                agg_idx = [(idx[o.name], o.count_like) for o in a.outputs if o.is_aggregate and o.name in idx]
                key_idx = [idx[kname] for kname in keys]
                for r in rows:
                    n = sizes.get(tuple(str(r[i]) for i in key_idx))
                    if n is not None and n < k:
                        for i, count_like in agg_idx:
                            if r[i] is not None:
                                r[i] = f"<{k}" if count_like else "suppressed"
                                suppressed += 1
                    for i, count_like in agg_idx:
                        if count_like and isinstance(r[i], (int, float)) and 0 < r[i] < k:
                            r[i] = f"<{k}"
                            suppressed += 1
            d.rules.append(_rule("P-08", "applied" if suppressed else "pass",
                                 f"{suppressed} value(s) from groups under {k} rows suppressed." if suppressed
                                 else ("Every group has at least %d rows." % k if a.aggregate_query else "Not an aggregate query.")))

            # P-09 approval, P-13 budget
            domains = {p.catalog[t].domain for t in tables}
            domain = "+".join(sorted(domains))
            if row_level:
                if len(rows) > s["approval_rows"] or req.purpose in p.high_risk_purposes:
                    reason = (f"Marketing use of {', '.join(row_level)}" if req.purpose in p.high_risk_purposes
                              else f"{len(rows)}{'+' if truncated else ''} rows showing {', '.join(row_level)} row by row")
                    d.rules.append(_rule("P-09", "held", f"{reason}. An eligible approver must agree."))
                    return self._held(d, identity, reason, domains, executed_sql, req)
                used = self.ledger.budget_used(identity.user_id, domain)
                if used + len(rows) > s["budget_rows"]:
                    reason = f"Budget: {used + len(rows)} of {s['budget_rows']} personal-data rows in 24 hours"
                    d.rules.append(_rule("P-13", "held", reason + "."))
                    return self._held(d, identity, reason, domains, executed_sql, req)
                d.rules.append(_rule("P-09", "pass", f"Under {s['approval_rows']} rows."))
                d.rules.append(_rule("P-13", "pass", f"{used + len(rows)} of {s['budget_rows']} rows used in 24 hours."))
            else:
                d.rules.append(_rule("P-09", "pass", "Aggregate result." if a.aggregate_query else "No personal data in the result."))

            # P-10
            d.rules.append(_rule("P-10", "applied" if truncated else "pass",
                                 f"Showing the first {s['result_cap']} rows." if truncated else f"{len(rows)} rows."))

            if row_level:
                self.ledger.budget_add(identity.user_id, domain, len(rows))
            applied = [r["id"] for r in d.rules if r["state"] == "applied"]
            d.decision = "modified" if applied else "allowed"
            d.message = f"Allowed. Ran under {identity.name}'s permissions."
            d.columns, d.rows, d.row_count = cols, rows, len(rows)
            d.trust = {
                "rows_in_scope": f"Region {', '.join(sorted(identity.regions))} only" if identity.regions is not None and regional else "All rows your role covers",
                "masked_columns": masked, "rounded_columns": rounded, "suppressed_values": suppressed,
                "rules_applied": applied, "policy_version": p.version, "purpose": req.purpose,
            }
            rec = self.ledger.append(request_id=rid, actor=identity.user_id, action="query.executed", outcome=d.decision,
                                     detail=f"Applied {', '.join(applied) or 'no changes'}." + (f" Purpose: {req.purpose}." if req.purpose else ""),
                                     sql=req.sql, policy_version=p.version, rules=d.rules, row_count=len(rows))
            d.audit_seq = rec["seq"]
            d.trust["audit_seq"] = rec["seq"]
            return d

        except GateBlock as b:
            d.rules.append(_rule(b.rule, "blocked", b.detail))
            d.decision, d.message = "blocked", b.message
            d.access_tables = list(b.extra.get("access_tables", []))
            rec = self.ledger.append(request_id=rid, actor=identity.user_id, action="query.blocked", outcome="blocked",
                                     detail=f"{b.rule} {RULE_NAMES.get(b.rule, '')}: {b.detail}", sql=req.sql,
                                     policy_version=p.version, rules=d.rules)
            d.audit_seq = rec["seq"]
            return d
        except QueryError as e:
            d.decision, d.message = "error", str(e)
            rec = self.ledger.append(request_id=rid, actor=identity.user_id, action="query.error", outcome="error",
                                     detail=str(e), sql=req.sql, policy_version=p.version, rules=d.rules)
            d.audit_seq = rec["seq"]
            return d
        except FailClosed as f:
            if f.code != "AUDIT_UNAVAILABLE":
                try:
                    self.ledger.append(request_id=rid, actor=identity.user_id, action="query.failed_closed", outcome="error",
                                       detail=f.message, sql=req.sql, policy_version=p.version, rules=d.rules)
                except FailClosed:
                    pass
            raise

    def _held(self, d: Decision, identity: Identity, reason: str, domains: set[str], executed_sql: str, req: QueryRequest) -> Decision:
        d.decision = "held"
        d.message = "Held for approval. Results aren't shown until someone approves."
        d.columns, d.rows, d.row_count = [], [], 0  # results are discarded, never cached
        d.approval = {"reason": reason, "purpose": req.purpose,
                      "eligible_approvers": self.eligible_approvers(identity.user_id, domains),
                      "status": "requires_approval",
                      "note": "The approval workflow (requests, decisions, single-use tokens) ships in Phase 2."}
        rec = self.ledger.append(request_id=d.request_id, actor=identity.user_id, action="query.held", outcome="held",
                                 detail=reason + (f". Purpose: {req.purpose}." if req.purpose else "."), sql=req.sql,
                                 policy_version=self.policy.version, rules=d.rules)
        d.audit_seq = rec["seq"]
        return d

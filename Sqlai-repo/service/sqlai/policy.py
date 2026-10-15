"""Policy bundle loading and effective permissions.

Phase 1 evaluates the YAML bundle in-process. The production design compiles the same
bundle to Rego for OPA sidecars (ADR-004); the decision semantics here are the reference.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

SENSITIVE = {"PII", "PHI", "Restricted"}
MASK_METHODS = {"initials", "partial_email", "redact", "last4", "round_10k"}
NUMERIC_ROUNDING_MASKS = {"round_10k"}  # eligible for aggregate-then-protect (PRV-11)


class PolicyError(ValueError):
    """The policy bundle is invalid. Services refuse to start (fail closed)."""


@dataclass(frozen=True)
class Column:
    name: str
    type: str
    cls: str

    @property
    def sensitive(self) -> bool:
        return self.cls in SENSITIVE


@dataclass(frozen=True)
class Table:
    name: str
    domain: str
    region_column: str | None
    columns: dict[str, Column]


@dataclass(frozen=True)
class Identity:
    """An authenticated user's effective permissions."""

    user_id: str
    name: str
    roles: tuple[str, ...]
    tables: frozenset[str]
    regions: frozenset[str] | None  # None = all regions
    masks: dict[str, str]  # "table.column" -> method
    approver_for: frozenset[str] = frozenset()
    audit_all: bool = False
    policy_admin: bool = False


@dataclass
class Policy:
    version: str
    settings: dict[str, Any]
    purposes: list[str]
    high_risk_purposes: set[str]
    catalog: dict[str, Table]
    roles: dict[str, dict[str, Any]]
    dev_users: dict[str, dict[str, Any]] = field(default_factory=dict)
    digest: str = ""

    # ---- lookups -------------------------------------------------------------
    def setting(self, key: str) -> Any:
        return self.settings[key]

    def column(self, table: str, col: str) -> Column | None:
        t = self.catalog.get(table)
        return t.columns.get(col) if t else None

    def schema_for(self, tables: frozenset[str] | set[str]) -> dict[str, dict[str, str]]:
        """sqlglot schema limited to the given tables (never the whole catalog)."""
        return {t: {c.name: c.type for c in self.catalog[t].columns.values()} for t in sorted(tables) if t in self.catalog}

    def identity(self, user_id: str, name: str, roles: list[str]) -> Identity:
        unknown = [r for r in roles if r not in self.roles]
        if unknown:
            raise PolicyError(f"Unknown roles: {unknown}")
        tables: set[str] = set()
        regions: set[str] | None = set()
        masks: dict[str, str] = {}
        approver: set[str] = set()
        audit_all = policy_admin = False
        for r in roles:
            spec = self.roles[r]
            tables |= set(spec.get("tables", []))
            if spec.get("tables"):
                if spec.get("regions") is None:
                    regions = None  # a role with tables and no region limit covers all regions
                elif regions is not None:
                    regions |= set(spec["regions"])
            masks.update(spec.get("masks", {}))  # union: the more restrictive outcome
            approver |= set(spec.get("approver_for", []))
            audit_all |= spec.get("audit") == "all"
            policy_admin |= bool(spec.get("policy_admin"))
        if regions is not None and not regions and tables:
            regions = None
        return Identity(
            user_id=user_id, name=name, roles=tuple(roles), tables=frozenset(tables),
            regions=frozenset(regions) if regions is not None else None, masks=masks,
            approver_for=frozenset(approver), audit_all=audit_all, policy_admin=policy_admin,
        )


def load_policy(path: str | Path) -> Policy:
    raw_text = Path(path).read_text()
    raw = yaml.safe_load(raw_text)
    try:
        catalog = {
            name: Table(
                name=name,
                domain=spec["domain"],
                region_column=spec.get("region_column"),
                columns={c: Column(c, v["type"], v["class"]) for c, v in spec["columns"].items()},
            )
            for name, spec in raw["catalog"].items()
        }
        policy = Policy(
            version=str(raw["version"]),
            settings=dict(raw["settings"]),
            purposes=list(raw.get("purposes", [])),
            high_risk_purposes=set(raw.get("high_risk_purposes", [])),
            catalog=catalog,
            roles=dict(raw["roles"]),
            dev_users=dict(raw.get("dev_users", {})),
            digest=hashlib.sha256(raw_text.encode()).hexdigest(),
        )
    except (KeyError, TypeError) as e:
        raise PolicyError(f"Policy bundle is missing a required field: {e}") from e
    _validate(policy)
    return policy


def _validate(p: Policy) -> None:
    required = {"approval_rows", "small_group_k", "result_cap", "budget_rows", "cost_limit", "statement_timeout_s", "round_to"}
    missing = required - set(p.settings)
    if missing:
        raise PolicyError(f"Missing settings: {sorted(missing)}")
    if p.settings["small_group_k"] < 2:
        raise PolicyError("small_group_k must be at least 2")
    for role, spec in p.roles.items():
        for t in spec.get("tables", []):
            if t not in p.catalog:
                raise PolicyError(f"Role {role} grants unknown table {t}")
        for key, method in spec.get("masks", {}).items():
            t, _, c = key.partition(".")
            if p.column(t, c) is None:
                raise PolicyError(f"Role {role} masks unknown column {key}")
            if method not in MASK_METHODS:
                raise PolicyError(f"Role {role} uses unknown mask method {method}")
    for t in p.catalog.values():
        if t.region_column and t.region_column not in t.columns:
            raise PolicyError(f"Table {t.name} region column {t.region_column} not in columns")

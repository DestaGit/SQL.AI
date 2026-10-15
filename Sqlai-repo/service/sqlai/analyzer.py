"""SQL analysis: static rules, column lineage, cost estimate and policy rewrite.

Everything here works on the sqlglot AST. Regular expressions are used only as a fast
prefilter (ADR-002). Lineage replaces every name-based check from the 1.0 demo (ADR-009).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import sqlglot
from sqlglot import exp
from sqlglot.errors import OptimizeError, ParseError
from sqlglot.optimizer.qualify import qualify
from sqlglot.optimizer.scope import Scope, build_scope

from .errors import GateBlock, QueryError
from .policy import NUMERIC_ROUNDING_MASKS, Identity, Policy

DIALECT = "duckdb"
MAX_SQL_LENGTH = 20_000

# Aggregates that summarize many rows without revealing one row's value (PRV-09).
SMOOTHING_AGGS = (exp.Count, exp.Avg, exp.Sum, exp.Stddev, exp.StddevPop, exp.StddevSamp,
                  exp.Variance, exp.VariancePop, exp.ApproxDistinct)
# Aggregates whose true values may be used for rounded numeric masks (PRV-11).
PROTECTABLE_AGGS = ("Avg", "Sum")

DENY_FUNCTION_PREFIXES = ("read_", "write_", "duckdb_", "pragma", "sqlite_", "postgres_", "mysql_",
                          "iceberg_", "delta_", "parquet_", "glob", "getenv", "current_setting",
                          "query", "load_", "install_", "http", "s3")
PREFILTER = re.compile(r"--|/\*|\binto\b|\battach\b|\bcopy\b|\bexport\b|\bpragma\b|\binstall\b|\bload\b", re.I)


# --------------------------------------------------------------------------- results
@dataclass
class OutputColumn:
    name: str
    sources: list[tuple[str, str, frozenset[str]]]  # (table, column, aggregate kinds on the path)
    is_aggregate: bool
    count_like: bool
    row_level_sensitive: list[str] = field(default_factory=list)
    masked_by: str | None = None
    rounded: bool = False


@dataclass
class Analysis:
    tree: exp.Select                 # qualified AST
    tables: list[str]                # base tables referenced
    outputs: list[OutputColumn]
    aggregate_query: bool
    cost_estimate: int
    exempt_masks: set[str]           # "table.column" computed on true values (PRV-11)
    inner_aggregation: bool          # aggregation inside a CTE or derived table

    @property
    def row_level_sensitive(self) -> list[str]:
        seen: list[str] = []
        for o in self.outputs:
            for c in o.row_level_sensitive:
                if c not in seen:
                    seen.append(c)
        return seen


# --------------------------------------------------------------------------- static rules
def parse_and_check(sql: str, policy: Policy, identity: Identity) -> tuple[exp.Select, list[str], list[dict]]:
    """Rules P-02 to P-05. Returns the parsed tree, referenced base tables and rule results."""
    results: list[dict] = []
    text = sql.strip().rstrip(";").strip()
    if not text:
        raise GateBlock("P-02", "The query is empty.", "Write or draft a query first.")
    if len(text) > MAX_SQL_LENGTH:
        raise GateBlock("P-03", f"The query is longer than {MAX_SQL_LENGTH:,} characters.")

    try:
        statements = [s for s in sqlglot.parse(text, dialect=DIALECT) if s is not None]
    except ParseError as e:
        raise GateBlock("P-02", f"The SQL didn't parse: {str(e).splitlines()[0]}", "Fix the SQL syntax and run again.") from e
    if len(statements) != 1:
        raise GateBlock("P-02", "Only one statement can run at a time.", "This workbench is read-only.")
    tree = statements[0]
    if not isinstance(tree, exp.Select) or tree.find(exp.Insert, exp.Update, exp.Delete, exp.Create, exp.Drop,
                                                     exp.Command, exp.Pragma, exp.Set, exp.Merge, exp.Alter):
        raise GateBlock("P-02", "Only a single SELECT (or WITH … SELECT) can run. Writes, schema changes and UNION are not allowed.",
                        "This workbench is read-only.")
    results.append({"id": "P-02", "state": "pass", "detail": "Single SELECT statement."})

    # P-03: comments, parameters, INTO, file/system functions, table functions
    bad = None
    m = PREFILTER.search(text)
    if m:
        bad = m.group(0)
    for node in tree.walk():
        if bad:
            break
        if getattr(node, "comments", None):
            bad = "comment"
        elif isinstance(node, (exp.Placeholder, exp.Parameter, exp.SessionParameter)):
            bad = "parameter"
        elif isinstance(node, exp.Into):
            bad = "INTO"
        elif isinstance(node, exp.Func):
            name = (node.name if isinstance(node, exp.Anonymous) else node.sql_name()).lower()
            if name.startswith(DENY_FUNCTION_PREFIXES):
                bad = name
        elif isinstance(node, exp.Table) and not isinstance(node.this, exp.Identifier):
            bad = "table function"
    if bad:
        raise GateBlock("P-03", f"“{bad}” isn't allowed. Comments, parameters, file access, scripts and database switching are blocked.",
                        "Remove the blocked syntax and try again.")
    results.append({"id": "P-03", "state": "pass", "detail": "No file, script or system access."})

    # P-04: same message for unknown and ungranted tables (GW-10)
    cte_names = {c.alias_or_name.lower() for c in tree.find_all(exp.CTE)}
    tables: list[str] = []
    for t in tree.find_all(exp.Table):
        if t.args.get("db") or t.args.get("catalog"):
            raise GateBlock("P-04", f"Cross-database references like {t.sql(DIALECT)} are blocked.", "Query tables by name only.")
        name = t.name.lower()
        if name in cte_names:
            continue
        if name not in tables:
            tables.append(name)
    if not tables:
        raise GateBlock("P-04", "The query doesn't read from a catalog table.", "Name a table in FROM.")
    bad_tables = [t for t in tables if t not in identity.tables or t not in policy.catalog]
    if bad_tables:
        raise GateBlock("P-04", f"Unknown table or no access: {', '.join(bad_tables)}. Check the data catalog, or request access.",
                        "This query uses a table you can't read.", access_tables=[t for t in bad_tables if t in policy.catalog])
    results.append({"id": "P-04", "state": "pass", "detail": f"Reads {', '.join(tables)}."})

    # P-05: SELECT * on tables with sensitive columns
    sensitive_tables = [t for t in tables if any(c.sensitive for c in policy.catalog[t].columns.values())]
    star = any(
        isinstance(e, exp.Star) or (isinstance(e, exp.Column) and isinstance(e.this, exp.Star))
        for sel in tree.find_all(exp.Select) for e in sel.expressions
    )
    if star and sensitive_tables:
        raise GateBlock("P-05", f"{', '.join(sensitive_tables)} hold personal or restricted columns. List the columns you need.",
                        "Replace * with named columns.")
    results.append({"id": "P-05", "state": "pass", "detail": "Columns are named explicitly."})
    return tree, tables, results


# --------------------------------------------------------------------------- lineage
def _scopes_by_column(root: Scope) -> dict[int, Scope]:
    owner: dict[int, Scope] = {}
    for scope in root.traverse():
        for col in scope.columns:
            owner[id(col)] = scope
    return owner


def _agg_kinds(node: exp.Expression, stop: exp.Expression | None) -> set[str]:
    kinds: set[str] = set()
    p = node.parent
    while p is not None and p is not stop:
        if isinstance(p, exp.AggFunc):
            # A window aggregate returns a value on every row and can isolate one row
            # (PARTITION BY id), so it never counts as smoothing or as protectable.
            kinds.add("Window" if isinstance(p.parent, exp.Window) else type(p).__name__)
        p = p.parent
    return kinds


def _resolve(col: exp.Column, owner: dict[int, Scope], kinds: frozenset[str], depth: int = 0) -> list[tuple[str, str, frozenset[str]]]:
    if depth > 25:
        return []
    scope = owner.get(id(col))
    if scope is None:
        return []
    src = scope.sources.get(col.table)
    if isinstance(src, exp.Table):
        return [(src.name.lower(), col.name.lower(), kinds)]
    if isinstance(src, Scope) and isinstance(src.expression, exp.Select):
        for proj in src.expression.selects:
            if proj.alias_or_name == col.name:
                return _expr_sources(proj, owner, kinds, depth + 1)
    return []


def _expr_sources(expr: exp.Expression, owner: dict[int, Scope], kinds: frozenset[str] = frozenset(), depth: int = 0):
    out: list[tuple[str, str, frozenset[str]]] = []
    for col in expr.find_all(exp.Column):
        k = frozenset(set(kinds) | _agg_kinds(col, expr.parent))
        out.extend(_resolve(col, owner, k, depth))
    return out


def _is_smoothed(kinds: frozenset[str]) -> bool:
    return "Window" not in kinds and any(k in {c.__name__ for c in SMOOTHING_AGGS} for k in kinds)


def _in_case_condition(col: exp.Column, stop: exp.Expression) -> bool:
    child, p = col, col.parent
    while p is not None and p is not stop:
        if isinstance(p, exp.If) and p.args.get("this") is child:
            return True
        child, p = p, p.parent
    return False


def _count_like(proj: exp.Expression) -> bool:
    if proj.find(exp.Count):
        return True
    for s in proj.find_all(exp.Sum):
        cols = [c for c in s.this.find_all(exp.Column) if not _in_case_condition(c, s)] if s.this else []
        if not cols and not proj.find(exp.Avg):
            return True
    return False


def analyze(tree: exp.Select, tables: list[str], policy: Policy, identity: Identity) -> Analysis:
    schema = policy.schema_for(set(tables))
    try:
        q = qualify(tree.copy(), schema=schema, dialect=DIALECT, validate_qualify_columns=True, quote_identifiers=True)
    except OptimizeError as e:
        raise QueryError(f"The query refers to something that doesn't exist: {e}") from e
    root = build_scope(q)
    if root is None:
        raise QueryError("The query couldn't be analyzed.")
    owner = _scopes_by_column(root)

    # all references to each base column, for aggregate-then-protect (PRV-11)
    refs: dict[str, list[frozenset[str]]] = {}
    for scope in root.traverse():
        for col in scope.columns:
            stop = scope.expression
            for t, c, k in _resolve(col, owner, frozenset(_agg_kinds(col, stop))):
                refs.setdefault(f"{t}.{c}", []).append(k)
    exempt = {
        key for key, method in identity.masks.items()
        if method in NUMERIC_ROUNDING_MASKS and key in refs
        and all(k and k <= set(PROTECTABLE_AGGS) for k in refs[key])
    }

    outputs: list[OutputColumn] = []
    for proj in q.selects:
        sources = _expr_sources(proj, owner)
        row_level = []
        masked_by = None
        rounded = False
        for t, c, k in sources:
            col = policy.column(t, c)
            if col and col.sensitive and not _is_smoothed(k) and c not in row_level:
                row_level.append(c)
            key = f"{t}.{c}"
            if key in identity.masks:
                if key in exempt:
                    rounded = True
                else:
                    masked_by = identity.masks[key]
        outputs.append(OutputColumn(
            name=proj.alias_or_name, sources=sources, is_aggregate=bool(proj.find(exp.AggFunc)),
            count_like=bool(proj.find(exp.AggFunc)) and _count_like(proj),
            row_level_sensitive=row_level, masked_by=masked_by, rounded=rounded,
        ))

    inner_agg = any(
        (s.is_cte or s.is_derived_table) and (s.expression.find(exp.AggFunc) is not None or s.expression.args.get("group"))
        for s in root.traverse() if s is not root and isinstance(s.expression, exp.Select)
    )
    aggregate_query = bool(q.args.get("group")) or any(o.is_aggregate for o in outputs)
    return Analysis(tree=q, tables=tables, outputs=outputs, aggregate_query=aggregate_query,
                    cost_estimate=estimate_cost(q, policy, identity, sizes=None), exempt_masks=exempt,
                    inner_aggregation=inner_agg)


# --------------------------------------------------------------------------- cost (P-14)
_SIZES: dict[str, int] = {}


def set_table_sizes(sizes: dict[str, int]) -> None:
    """Row counts per table, refreshed from the warehouse catalog."""
    _SIZES.clear()
    _SIZES.update({k.lower(): int(v) for k, v in sizes.items()})


def estimate_cost(q: exp.Select, policy: Policy, identity: Identity, sizes: dict[str, int] | None) -> int:
    sizes = sizes or _SIZES

    def size_of(node: exp.Expression | None) -> int:
        if isinstance(node, exp.Table):
            return sizes.get(node.name.lower(), 1000)
        if isinstance(node, exp.Subquery):
            return max([size_of(t) for t in node.find_all(exp.Table)] or [1000])
        return 1000

    worst = 1
    for sel in q.find_all(exp.Select):
        frm = sel.args.get("from_") or sel.args.get("from")
        if not frm:
            continue
        est = size_of(frm.this)
        for j in sel.args.get("joins") or []:
            s = size_of(j.this)
            if (j.args.get("kind") or "").upper() == "CROSS" or not (j.args.get("on") or j.args.get("using")):
                est *= s
            else:
                est = max(est, s)
        worst = max(worst, est)
    return worst


# --------------------------------------------------------------------------- rewrite (P-06, P-07)
def _q(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def mask_sql(method: str, col: str) -> str:
    c = _q(col)
    return {
        "initials": f"array_to_string(list_transform(string_split({c}, ' '), x -> left(x, 1) || '.'), ' ')",
        "partial_email": f"left({c}, 1) || '•••@' || split_part({c}, '@', 2)",
        "redact": f"CASE WHEN {c} IS NULL THEN NULL ELSE '••••••' END",
        "last4": f"CASE WHEN {c} IS NULL THEN NULL ELSE '•••-•••-' || right(regexp_replace({c}, '[^0-9]', '', 'g'), 4) END",
        "round_10k": f"CAST(round({c} / 10000.0) * 10000 AS INTEGER)",
    }[method]


def scoped_select(table: str, policy: Policy, identity: Identity, exempt: set[str]) -> str:
    t = policy.catalog[table]
    cols = []
    for c in t.columns.values():
        key = f"{table}.{c.name}"
        method = identity.masks.get(key)
        expr = mask_sql(method, c.name) if method and key not in exempt else _q(c.name)
        cols.append(f"{expr} AS {_q(c.name)}")
    where = ""
    if identity.regions is not None and t.region_column:
        regions = ", ".join("'" + r.replace("'", "''") + "'" for r in sorted(identity.regions))
        where = f" WHERE {_q(t.region_column)} IN ({regions})"
    return f"SELECT {', '.join(cols)} FROM {_q(table)}{where}"


def rewrite(analysis: Analysis, policy: Policy, identity: Identity) -> exp.Select:
    """Replace every base-table reference with a filtered, masked subquery."""
    q = analysis.tree.copy()
    cte_names = {c.alias_or_name for c in q.find_all(exp.CTE)}
    targets = [t for t in q.find_all(exp.Table) if t.name in policy.catalog and t.name not in cte_names]
    for t in targets:
        inner = sqlglot.parse_one(scoped_select(t.name, policy, identity, analysis.exempt_masks), dialect=DIALECT)
        alias = t.alias_or_name
        t.replace(exp.Subquery(this=inner, alias=exp.TableAlias(this=exp.to_identifier(alias, quoted=True))))
    return q


def group_size_query(rewritten: exp.Select) -> tuple[str, list[str]] | None:
    """Companion COUNT(*) per output group (ADR-010). None if groups can't be matched to output columns."""
    group = rewritten.args.get("group")
    groups = list(group.expressions) if group else []
    keys: list[str] = []
    for g in groups:
        match = next((p.alias_or_name for p in rewritten.selects if p.unalias() == g), None)
        if match is None:
            return None
        keys.append(match)
    comp = rewritten.copy()
    comp.set("expressions", [g.copy().as_(f"__g{i}") for i, g in enumerate(groups)]
             + [exp.Count(this=exp.Star()).as_("__n")])
    for arg in ("order", "limit", "offset", "distinct"):
        comp.set(arg, None)
    return comp.sql(DIALECT), keys

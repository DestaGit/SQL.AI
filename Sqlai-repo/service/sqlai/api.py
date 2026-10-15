"""HTTP API (subset of docs/api/openapi.yaml for Phase 1)."""
from __future__ import annotations

import datetime as dt
import decimal
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from pathlib import Path

from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .audit import AuditLedger
from .config import Settings
from .errors import FailClosed
from .executor import Executor, TicketAuthority
from .gateway import Gateway, QueryRequest
from .identity import DevIdentityProvider, OIDCIdentityProvider
from .policy import Identity, load_policy


WEB_DIR = Path(__file__).resolve().parent / "web"

# Strict policy for the web app: no inline scripts, no third-party scripts, no framing.
CSP = ("default-src 'self'; script-src 'self'; style-src 'self' https://fonts.googleapis.com; "
       "font-src https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; "
       "frame-ancestors 'none'; base-uri 'none'; form-action 'self'; object-src 'none'")


class QueryBody(BaseModel):
    sql: str = Field(min_length=1, max_length=20_000)
    purpose: str | None = Field(default=None, max_length=100)


def _json_safe(v: Any) -> Any:
    if isinstance(v, (dt.date, dt.datetime)):
        return v.isoformat()
    if isinstance(v, decimal.Decimal):
        return float(v)
    return v


def _error(status: int, code: str, message: str, request_id: str | None = None) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message, "request_id": request_id}})


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    policy = load_policy(settings.policy_path)
    authority = TicketAuthority()
    executor = Executor(settings.warehouse_path, authority, timeout_s=policy.settings["statement_timeout_s"])
    ledger = AuditLedger(settings.audit_db, settings.checkpoint_dir, settings.audit_key)
    gateway = Gateway(policy, executor, ledger, authority)
    idp = DevIdentityProvider(policy) if settings.idp == "dev" else OIDCIdentityProvider(policy)

    app = FastAPI(title="SQL.AI", version="0.2.0", docs_url="/docs" if settings.env == "local" else None)
    app.state.gateway, app.state.ledger, app.state.executor, app.state.policy = gateway, ledger, executor, policy

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        h = response.headers
        h["X-Content-Type-Options"] = "nosniff"
        h["Referrer-Policy"] = "no-referrer"
        h["X-Frame-Options"] = "DENY"
        h["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if not request.url.path.startswith(("/docs", "/openapi.json", "/redoc")):
            h["Content-Security-Policy"] = CSP
        if request.url.path.startswith("/v1/"):
            h["Cache-Control"] = "no-store"
        if settings.env != "local":
            h["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    @app.exception_handler(FailClosed)
    async def fail_closed(_: Request, e: FailClosed):
        return _error(503, e.code, e.message)

    def current_identity(authorization: str = Header(default="")) -> Identity:
        token = authorization.removeprefix("Bearer ").strip()
        ident = idp.authenticate(token) if token else None
        if ident is None:
            raise HTTPException(status_code=401, detail={"code": "UNAUTHENTICATED", "message": "Sign in again: the token is missing or not valid."})
        return ident

    @app.exception_handler(HTTPException)
    async def http_error(_: Request, e: HTTPException):
        detail = e.detail if isinstance(e.detail, dict) else {"code": "ERROR", "message": str(e.detail)}
        return _error(e.status_code, detail["code"], detail["message"])

    def role_titles(ident: Identity) -> list[str]:
        return [policy.roles[r].get("title", r) for r in ident.roles]

    # ---------------------------------------------------------------- web app
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

    @app.get("/", include_in_schema=False)
    def web_app():
        return FileResponse(WEB_DIR / "index.html", media_type="text/html")

    @app.get("/v1/me")
    def me(ident: Identity = Depends(current_identity)):
        return {
            "user_id": ident.user_id, "name": ident.name, "roles": list(ident.roles), "titles": role_titles(ident),
            "tables": sorted(ident.tables), "regions": sorted(ident.regions) if ident.regions is not None else None,
            "audit_all": ident.audit_all, "policy_admin": ident.policy_admin, "approver_for": sorted(ident.approver_for),
            "policy_version": policy.version,
        }

    if settings.env == "local" and settings.idp == "dev":
        @app.get("/v1/dev/users")
        def dev_users():
            """Local development only: the demo accounts the sign-in screen offers."""
            return [{"user_id": uid, "name": spec["name"], "token": spec["token"],
                     "title": ", ".join(policy.roles[r].get("title", r) for r in spec["roles"])}
                    for uid, spec in policy.dev_users.items()]

    @app.get("/healthz")
    def healthz():
        return {"status": "ok", "policy_version": policy.version, "policy_digest": policy.digest[:16]}

    @app.post("/v1/queries")
    def run_query(body: QueryBody, ident: Identity = Depends(current_identity)):
        d = gateway.run(ident, QueryRequest(sql=body.sql, purpose=body.purpose))
        return {
            "request_id": d.request_id, "decision": d.decision, "message": d.message, "rules": d.rules,
            "columns": d.columns, "rows": [[_json_safe(v) for v in r] for r in d.rows], "row_count": d.row_count,
            "trust": d.trust, "approval": d.approval, "access_tables": d.access_tables,
            "policy_version": d.policy_version, "audit": {"seq": d.audit_seq},
        }

    @app.get("/v1/catalog")
    def catalog(ident: Identity = Depends(current_identity)):
        out = {}
        for name, t in policy.catalog.items():
            if name not in ident.tables:
                continue
            out[name] = {
                "domain": t.domain,
                "rows": f"Region {', '.join(sorted(ident.regions))} only" if ident.regions is not None and t.region_column else "All",
                "columns": {c.name: {"type": c.type, "class": c.cls, "you_see": ident.masks.get(f"{name}.{c.name}", "visible")}
                            for c in t.columns.values()},
            }
        return {"tables": out, "purposes": policy.purposes}

    @app.get("/v1/audit")
    def audit(limit: int = 100, ident: Identity = Depends(current_identity)):
        limit = max(1, min(limit, 500))
        records = ledger.records(None if ident.audit_all else ident.user_id, limit)
        return {"scope": "all" if ident.audit_all else "own", "records": records}

    @app.post("/v1/audit/verify")
    def verify(ident: Identity = Depends(current_identity)):
        if not ident.audit_all:
            raise HTTPException(status_code=403, detail={"code": "FORBIDDEN_SCOPE", "message": "Only security and data admins can verify the full chain."})
        chain = ledger.verify()
        checkpoints = ledger.verify_checkpoints()
        ledger.append(request_id="verify", actor=ident.user_id, action="audit.verified",
                      outcome="info" if chain["ok"] and checkpoints["ok"] else "alert",
                      detail=f"chain={chain} checkpoints={checkpoints}", policy_version=policy.version)
        return {"chain": chain, "checkpoints": checkpoints}

    @app.post("/v1/audit/checkpoint")
    def checkpoint(ident: Identity = Depends(current_identity)):
        if not ident.audit_all:
            raise HTTPException(status_code=403, detail={"code": "FORBIDDEN_SCOPE", "message": "Only security and data admins can write checkpoints."})
        return {"checkpoint": ledger.checkpoint()}

    return app

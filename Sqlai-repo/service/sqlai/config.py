"""Configuration from environment variables, validated at start-up (fail closed)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    env: str
    policy_path: Path
    warehouse_path: Path
    audit_db: Path
    checkpoint_dir: Path
    audit_key: bytes
    idp: str

    @staticmethod
    def from_env() -> "Settings":
        env = os.environ.get("SQLAI_ENV", "local")
        root = Path(os.environ.get("SQLAI_DATA_DIR", "data"))
        key = os.environ.get("SQLAI_AUDIT_KEY", "")
        idp = os.environ.get("SQLAI_IDP", "dev" if env == "local" else "oidc")
        if env != "local":
            if len(key) < 32:
                raise RuntimeError("SQLAI_AUDIT_KEY must be set (32+ characters) outside local development.")
            if idp == "dev":
                raise RuntimeError("The development identity provider is only allowed when SQLAI_ENV=local.")
        return Settings(
            env=env,
            policy_path=Path(os.environ.get("SQLAI_POLICY", "policy/default.yaml")),
            warehouse_path=Path(os.environ.get("SQLAI_WAREHOUSE", root / "warehouse.duckdb")),
            audit_db=Path(os.environ.get("SQLAI_AUDIT_DB", root / "audit.sqlite")),
            checkpoint_dir=Path(os.environ.get("SQLAI_CHECKPOINT_DIR", root / "checkpoints")),
            audit_key=(key or "local-development-key-not-for-production").encode(),
            idp=idp,
        )

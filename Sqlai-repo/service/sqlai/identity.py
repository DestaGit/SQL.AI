"""Identity providers.

Phase 1 ships the development provider (static tokens from the policy bundle, local only)
and the interface for OIDC. Production wires an OIDC/SAML provider plus SCIM sync (IAM-01–IAM-03).
"""
from __future__ import annotations

import hmac
from typing import Protocol

from .errors import FailClosed
from .policy import Identity, Policy


class IdentityProvider(Protocol):
    def authenticate(self, bearer_token: str) -> Identity | None: ...


class DevIdentityProvider:
    def __init__(self, policy: Policy):
        self.policy = policy

    def authenticate(self, bearer_token: str) -> Identity | None:
        for user_id, spec in self.policy.dev_users.items():
            if hmac.compare_digest(str(spec.get("token", "")), bearer_token):
                return self.policy.identity(user_id, spec["name"], list(spec["roles"]))
        return None


class OIDCIdentityProvider:
    """Validates OIDC access tokens and maps groups to roles. Not configured in Phase 1."""

    def __init__(self, policy: Policy):
        self.policy = policy

    def authenticate(self, bearer_token: str) -> Identity | None:
        raise FailClosed("IDP_UNAVAILABLE", "Sign-in isn't configured for this environment, so the request was refused.")

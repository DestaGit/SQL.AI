"""Gate outcomes and service errors."""
from __future__ import annotations


class GateBlock(Exception):
    """A policy rule blocked the query. This is a normal outcome, not a failure."""

    def __init__(self, rule: str, detail: str, message: str | None = None, **extra):
        super().__init__(detail)
        self.rule = rule
        self.detail = detail
        self.message = message or detail
        self.extra = extra


class QueryError(Exception):
    """The query is valid policy-wise but can't be evaluated (unknown column, engine error)."""


class FailClosed(Exception):
    """A safety dependency is unavailable. Nothing runs and nothing is returned."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message

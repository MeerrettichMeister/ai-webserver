"""ETag / If-Match headers for optimistic concurrency control on versioned rows."""

import re
from typing import Annotated, Any

from fastapi import Depends, Header, HTTPException, status

from py_server.service import ExpectedVersion


def etag(version: int) -> str:
    return f'"{version}"'


# OpenAPI docs for the errors a route using IfMatchDep can return.
PRECONDITION_RESPONSES: dict[int | str, dict[str, Any]] = {
    status.HTTP_412_PRECONDITION_FAILED: {"description": "If-Match is not the current version"},
    status.HTTP_428_PRECONDITION_REQUIRED: {"description": "If-Match header is missing"},
}

# An ETag made by etag(); weak (W/"1") or foreign tags never match (strong comparison, RFC 9110).
_VERSION_TAG = re.compile(r'"(0|[1-9][0-9]*)"')


def require_if_match(if_match: Annotated[str | None, Header()] = None) -> ExpectedVersion:
    """Make writes conditional: clients must say which version they are changing."""
    if if_match is None:
        raise HTTPException(status.HTTP_428_PRECONDITION_REQUIRED, "If-Match header is required")
    tags = [tag.strip() for tag in if_match.split(",")]
    if "*" in tags:
        return ExpectedVersion(any_version=True)
    return ExpectedVersion(
        frozenset(int(match[1]) for tag in tags if (match := _VERSION_TAG.fullmatch(tag)))
    )


IfMatchDep = Annotated[ExpectedVersion, Depends(require_if_match)]

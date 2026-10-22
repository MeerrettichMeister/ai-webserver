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

# A version in If-Match: an ETag made by etag() ("3") or, leniently, the bare number (3), as
# typed into Swagger UI. Weak (W/"3") and foreign tags never match (strong comparison, RFC 9110).
_VERSION_TAG = re.compile(r'"([0-9]+)"|([0-9]+)')


def require_if_match(
    if_match: Annotated[
        str | None,
        Header(
            description='The `ETag` (version) the change is based on, e.g. `"3"` or `3`; '
            "several separated by commas, or `*` for any version."
        ),
    ] = None,
) -> ExpectedVersion:
    """Make writes conditional: clients must say which version they are changing."""
    if if_match is None:
        raise HTTPException(status.HTTP_428_PRECONDITION_REQUIRED, "If-Match header is required")
    tags = [tag.strip() for tag in if_match.split(",")]
    if "*" in tags:
        return ExpectedVersion(any_version=True)
    return ExpectedVersion(
        frozenset(
            int(match[1] or match[2]) for tag in tags if (match := _VERSION_TAG.fullmatch(tag))
        )
    )


IfMatchDep = Annotated[ExpectedVersion, Depends(require_if_match)]

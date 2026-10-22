"""ETag headers: If-Match for writes, If-None-Match for conditional GETs."""

import re
from typing import Annotated, Any

from fastapi import Depends, Header, HTTPException, Response, status

from py_server.service import ExpectedVersion


def etag(version: int) -> str:
    """The ETag header value for a version."""
    return f'"{version}"'


# OpenAPI docs for the errors a route using IfMatchDep can return.
PRECONDITION_RESPONSES: dict[int | str, dict[str, Any]] = {
    status.HTTP_412_PRECONDITION_FAILED: {"description": "If-Match is not the current version"},
    status.HTTP_428_PRECONDITION_REQUIRED: {"description": "If-Match header is missing"},
}

# OpenAPI docs for the response of a route using IfNoneMatchDep.
NOT_MODIFIED_RESPONSES: dict[int | str, dict[str, Any]] = {
    status.HTTP_304_NOT_MODIFIED: {
        "description": "If-None-Match names the current version; no body is sent"
    },
}

# A version in If-Match / If-None-Match: an ETag made by etag() ("3") or, leniently, the bare
# number (3), as typed into Swagger UI. Foreign tags never match.
_VERSION_TAG = re.compile(r'"([0-9]+)"|([0-9]+)')


def _parse_versions(header: str, *, weak: bool) -> ExpectedVersion:
    """The versions a header lists; `weak` also accepts W/ tags (RFC 9110)."""
    tags = [tag.strip() for tag in header.split(",")]
    if "*" in tags:
        return ExpectedVersion(any_version=True)
    if weak:
        tags = [tag.removeprefix("W/") for tag in tags]
    return ExpectedVersion(
        frozenset(
            int(match[1] or match[2]) for tag in tags if (match := _VERSION_TAG.fullmatch(tag))
        )
    )


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
    # Strong comparison: a weak tag (W/"3") never matches.
    return _parse_versions(if_match, weak=False)


IfMatchDep = Annotated[ExpectedVersion, Depends(require_if_match)]


def read_if_none_match(
    if_none_match: Annotated[
        str | None,
        Header(
            description='The `ETag` (version) the client already has, e.g. `"3"` or `3`; '
            "answered with 304 Not Modified while it is current."
        ),
    ] = None,
) -> ExpectedVersion | None:
    """The versions the client already has, if it sent If-None-Match."""
    return None if if_none_match is None else _parse_versions(if_none_match, weak=True)


IfNoneMatchDep = Annotated[ExpectedVersion | None, Depends(read_if_none_match)]


def send_etag(response: Response, version: int, if_none_match: ExpectedVersion | None) -> None:
    """Set the ETag; raise 304 Not Modified if the client has this version."""
    tag = etag(version)
    if if_none_match is not None and if_none_match.matches(version):
        # FastAPI answers this without a body, as 304 requires.
        raise HTTPException(status.HTTP_304_NOT_MODIFIED, headers={"ETag": tag})
    response.headers["ETag"] = tag

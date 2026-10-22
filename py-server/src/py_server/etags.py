"""ETag / If-Match helpers for optimistic concurrency control on versioned rows."""

from typing import Annotated, Any

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError


def etag(version: int) -> str:
    return f'"{version}"'


# OpenAPI docs for the errors a route using IfMatchDep can return.
PRECONDITION_RESPONSES: dict[int | str, dict[str, Any]] = {
    status.HTTP_412_PRECONDITION_FAILED: {"description": "If-Match is not the current version"},
    status.HTTP_428_PRECONDITION_REQUIRED: {"description": "If-Match header is missing"},
}


def require_if_match(if_match: Annotated[str | None, Header()] = None) -> str:
    """Make writes conditional: clients must say which version they are changing."""
    if if_match is None:
        raise HTTPException(status.HTTP_428_PRECONDITION_REQUIRED, "If-Match header is required")
    return if_match


IfMatchDep = Annotated[str, Depends(require_if_match)]


def check_if_match(if_match: str, version: int) -> None:
    """Raise 412 unless If-Match names the current version (strong comparison, RFC 9110)."""
    tags = {tag.strip() for tag in if_match.split(",")}
    if "*" not in tags and etag(version) not in tags:
        raise precondition_failed()


def precondition_failed() -> HTTPException:
    return HTTPException(
        status.HTTP_412_PRECONDITION_FAILED,
        "This was changed by someone else; fetch it again and retry",
    )


def commit_or_412(session: Session) -> None:
    """Commit, turning a lost race on a versioned row into 412."""
    try:
        session.commit()
    except StaleDataError as exc:
        # Someone committed a new version between our read and our UPDATE.
        session.rollback()
        raise precondition_failed() from exc

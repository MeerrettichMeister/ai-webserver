"""Optimistic locking: writes say which versions of an object they were made against."""

from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from py_server.service.errors import PreconditionFailedError


@dataclass(frozen=True)
class ExpectedVersion:
    """The versions a write may apply to (the API reads them from If-Match)."""

    versions: frozenset[int] = frozenset()
    any_version: bool = False

    def check(self, version: int) -> None:
        if not self.any_version and version not in self.versions:
            raise PreconditionFailedError


def commit(session: Session) -> None:
    """Commit, turning a lost race on a versioned row into PreconditionFailedError."""
    try:
        session.commit()
    except StaleDataError as exc:
        # Someone committed a new version between our read and our UPDATE.
        session.rollback()
        raise PreconditionFailedError from exc

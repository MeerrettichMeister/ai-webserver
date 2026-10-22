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

    def matches(self, version: int) -> bool:
        """Whether `version` is one of the expected versions."""
        return self.any_version or version in self.versions

    def check(self, version: int) -> None:
        """Raise PreconditionFailedError unless `version` is one of the expected."""
        if not self.matches(version):
            raise PreconditionFailedError


def commit(session: Session) -> None:
    """Commit, turning a lost race on a versioned row into PreconditionFailedError."""
    try:
        session.commit()
    except StaleDataError as exc:
        # Someone committed a new version between our read and our UPDATE.
        session.rollback()
        raise PreconditionFailedError from exc

class ServiceError(Exception):
    """A request the service layer refuses; the API turns it into an error response."""


class NotFoundError(ServiceError):
    """The requested object does not exist."""


class ConflictError(ServiceError):
    """The change conflicts with existing data, e.g. a duplicate name."""


class InvalidReferenceError(ServiceError):
    """The request refers to objects that do not belong to it."""


class PreconditionFailedError(ServiceError):
    """The object was changed by someone else since the client read it."""

    def __init__(
        self, message: str = "This was changed by someone else; fetch it again and retry"
    ) -> None:
        super().__init__(message)

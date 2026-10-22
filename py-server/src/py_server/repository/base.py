from sqlalchemy.orm import Session


class Repository:
    """Data access for one table on the request's session.

    Repositories only query and stage changes; the service decides when to commit.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

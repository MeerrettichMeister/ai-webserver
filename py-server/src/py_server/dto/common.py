from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.json_schema import SkipJsonSchema

# An id that may be left out; documented as a plain (not nullable) uuid.
OptionalId = Annotated[
    UUID | SkipJsonSchema[None],
    Field(description="Id of the existing item to update; leave out to add a new one."),
]

# The row's version, also sent as its ETag.
Version = Annotated[int, Field(description='Send as `If-Match: "<version>"` when updating.')]


class ReadModel(BaseModel):
    """Base for response bodies, which are read from the attributes of an ORM object."""

    model_config = ConfigDict(from_attributes=True)

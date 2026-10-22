from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer
from pydantic.json_schema import SkipJsonSchema

# An id that may be left out; documented as a plain (not nullable) uuid.
OptionalId = Annotated[
    UUID | SkipJsonSchema[None],
    Field(description="Id of the existing item to update; leave out to add a new one."),
]

# The row's version, also sent as its ETag.
Version = Annotated[int, Field(description='Send as `If-Match: "<version>"` when updating.')]


def _to_json_number(value: Decimal) -> int | float:
    return int(value) if value == value.to_integral_value() else float(value)


# A quantity, stored exactly (numeric(10, 3)) but sent as a plain JSON number: 400, not "400.000".
Amount = Annotated[
    Decimal,
    Field(gt=0, max_digits=10, decimal_places=3),
    PlainSerializer(_to_json_number, return_type=int | float, when_used="json"),
]


class ReadModel(BaseModel):
    """Base for response bodies, which are read from the attributes of an ORM object."""

    model_config = ConfigDict(from_attributes=True)

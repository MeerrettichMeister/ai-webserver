from math import ceil

from pydantic import BaseModel, Field, computed_field


class PageParams(BaseModel):
    """Which page of a list to return (query parameters)."""

    page: int = Field(default=1, ge=1, le=1_000_000, description="Page number, starting at 1.")
    size: int = Field(default=20, ge=1, le=100, description="Items per page.")

    @property
    def offset(self) -> int:
        """Number of items on the pages before this one."""
        return (self.page - 1) * self.size


class Page[T](BaseModel):
    """One page of a list; pages past the last one are empty."""

    items: list[T]
    total: int = Field(description="Number of items on all pages.")
    page: int
    size: int

    @computed_field(description="Number of pages.")
    @property
    def pages(self) -> int:
        return ceil(self.total / self.size)

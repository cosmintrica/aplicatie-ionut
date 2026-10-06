from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from .domain import exact_quantity


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ListCreate(StrictModel):
    name: str = Field(min_length=1, max_length=120)
    scenario_id: str

    @field_validator("name")
    @classmethod
    def clean_name(cls, value):
        if not value.strip():
            raise ValueError("Numele nu poate fi gol.")
        return value.strip()


class ListUpdate(StrictModel):
    expected_revision: int = Field(ge=1)
    name: str | None = Field(default=None, min_length=1, max_length=120)
    scenario_id: str | None = None

    @field_validator("name")
    @classmethod
    def clean_name(cls, value):
        if value is not None and not value.strip():
            raise ValueError("Numele nu poate fi gol.")
        return value.strip() if value else value


class LineCreate(StrictModel):
    expected_revision: int = Field(ge=1)
    source_product_id: str | None = None
    description: str | None = Field(default=None, max_length=300)
    quantity: str = "1"
    unit: Literal["item"] = "item"
    category_id: str | None = None

    @field_validator("quantity")
    @classmethod
    def quantity_valid(cls, value):
        return exact_quantity(value)


class LineUpdate(StrictModel):
    expected_revision: int = Field(ge=1)
    quantity: str | None = None
    description: str | None = Field(default=None, min_length=1, max_length=300)
    source_product_id: str | None = None
    category_id: str | None = None

    @field_validator("quantity")
    @classmethod
    def quantity_valid(cls, value):
        return exact_quantity(value) if value is not None else None


class ComparisonCreate(StrictModel):
    list_id: str
    expected_revision: int = Field(ge=1)
    scenario_id: str


class CompanyUpdate(StrictModel):
    expected_revision: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=120)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value):
        if not value.strip():
            raise ValueError("Numele nu poate fi gol.")
        return value.strip()

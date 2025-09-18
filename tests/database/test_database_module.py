import pytest
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from dotmac.platform.database import (
    BaseModel,
    DatabaseDriver,
    IsolationLevel,
)


class Widget(BaseModel):
    __tablename__ = "widgets"

    name: Mapped[str] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)


@pytest.mark.unit
def test_base_model_initialization_and_conversion():
    widget = Widget(name="example", description="sample widget")

    assert widget.name == "example"
    assert widget.description == "sample widget"

    data = widget.to_dict()
    assert data["name"] == "example"
    assert "id" in data
    assert data["description"] == "sample widget"

    repr_string = repr(widget)
    assert repr_string.startswith("<Widget")
    assert "example" in repr_string


@pytest.mark.unit
def test_database_enums_expose_expected_values():
    assert DatabaseDriver.POSTGRESQL.value == "postgresql"
    assert DatabaseDriver.POSTGRESQL_ASYNC.value == "postgresql+asyncpg"
    assert IsolationLevel.SERIALIZABLE.value == "SERIALIZABLE"
    assert IsolationLevel.READ_COMMITTED.value == "READ COMMITTED"

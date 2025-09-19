"""
Unit tests for database mixins and base model helpers.
"""

import pytest
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base
from dotmac.platform.database.mixins import (
    DescriptionMixin,
    ISPModelMixin,
    StatusMixin,
    TenantMixin,
    TimestampMixin,
)


@pytest.mark.unit
def test_mixins_attributes_and_helpers():
    Base = declarative_base()

    class Thing(
        Base, ISPModelMixin, TimestampMixin, TenantMixin, StatusMixin, DescriptionMixin
    ):
        __tablename__ = "things"
        id = Column(Integer, primary_key=True)
        name = Column(String(50))
        count = Column(Integer, default=0)

    # Instantiate and use helpers without hitting a real DB
    t = Thing(name="widget", count=1, description="test item", tenant_id="t-1")

    # update helper from ISPModelMixin
    t.update(count=2, status="inactive")
    assert t.count == 2
    assert t.status == "inactive"

    # to_dict should include declared columns
    d = t.to_dict()
    assert set(
        [
            "id",
            "name",
            "count",
            "created_at",
            "updated_at",
            "deleted_at",
            "tenant_id",
            "status",
            "is_active",
            "description",
        ]
    ).issuperset(d.keys())

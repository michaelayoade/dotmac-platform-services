import pytest

from dotmac.platform.search.models_elasticsearch import (
    INDEX_MAPPINGS,
    SearchableEntity,
    SearchOperator,
    SortOrder,
)

pytestmark = pytest.mark.unit


def test_index_mappings_include_expected_fields() -> None:
    tenant_mapping = INDEX_MAPPINGS[SearchableEntity.TENANT]
    assert "tenant_id" in tenant_mapping["properties"]
    assert "slug" in tenant_mapping["properties"]
    assert tenant_mapping["properties"]["name"]["fields"]["keyword"]["type"] == "keyword"


def test_enums_cover_expected_values() -> None:
    assert SearchableEntity.TENANT.value == "tenant"
    assert SearchOperator.AND.value == "and"
    assert SortOrder.DESC.value == "desc"

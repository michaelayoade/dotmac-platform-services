import pytest

from dotmac.platform.core.pagination import (
    Page,
    PaginationParams,
    create_page,
    get_pagination_bounds,
)


@pytest.mark.unit
def test_pagination_params_skip_limit():
    params = PaginationParams(page=3, size=25)
    assert params.skip == 50
    assert params.limit == 25


@pytest.mark.unit
def test_page_create_and_properties_and_to_dict():
    items = list(range(10))
    page = Page.create(items=items, total=53, page=2, size=10)
    assert page.items == items
    assert page.total == 53 and page.pages == 6
    assert page.page == 2 and page.size == 10
    assert page.has_prev is True and page.prev_page == 1
    assert page.has_next is True and page.next_page == 3

    d = page.to_dict()
    assert d["items"] == items
    m = d["metadata"]
    assert m["total"] == 53 and m["pages"] == 6 and m["page"] == 2 and m["size"] == 10
    assert m["has_next"] and m["has_prev"] and m["next_page"] == 3 and m["prev_page"] == 1


@pytest.mark.unit
def test_create_page_and_bounds_helper():
    params = PaginationParams(page=1, size=20)
    page = create_page(items=[1, 2], total=42, params=params)
    assert page.page == 1 and page.size == 20 and page.total == 42 and page.pages == 3

    start, end = get_pagination_bounds(params, total=42)
    assert (start, end) == (0, 20)


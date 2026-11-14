import pytest

from marketplace.server import filters, order_page


def test_filters_normalize_dates_and_reject_invalid_values():
    assert filters({"state": "SP", "end_date": "2018-08-31"})["end_date"] == "2018-09-01"
    with pytest.raises(ValueError):
        filters({"state": "São Paulo"})
    with pytest.raises(ValueError):
        filters({"start_date": "2018-09-01", "end_date": "2018-08-31"})


def test_order_page_has_a_bounded_offset():
    assert order_page("2") == 25
    with pytest.raises(ValueError):
        order_page("0")
    with pytest.raises(ValueError):
        order_page("10001")

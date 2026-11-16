"""Contract tests for the airport search service implemented by part 1."""

import pytest

airport_service = pytest.importorskip("airport_service")


def test_search_returns_airports_with_the_shared_schema():
    results = airport_service.search_airports("Amsterdam")
    assert results
    assert {"iata", "city", "airport", "country", "display_name"} <= set(results[0])
    assert results[0]["iata"]
    assert "AMS" in results[0]["display_name"] or any(
        item["iata"] == "AMS" for item in results
    )


def test_search_is_limited_and_handles_blank_query():
    assert airport_service.search_airports("London", limit=2).__len__() <= 2
    assert airport_service.search_airports("") == []

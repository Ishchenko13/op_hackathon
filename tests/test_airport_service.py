"""Tests for the shared airport search function."""

import pytest

airport_service = pytest.importorskip("airport_service")


def test_search_returns_airports_with_the_shared_fields():
    results = airport_service.search_airports("Amsterdam")
    assert results
    assert {"iata", "city", "airport", "country", "display_name"} <= set(results[0])
    assert any(item["iata"] == "AMS" for item in results)


def test_search_obeys_limit_and_returns_empty_for_blank_query():
    assert len(airport_service.search_airports("London", limit=2)) <= 2
    assert airport_service.search_airports("") == []

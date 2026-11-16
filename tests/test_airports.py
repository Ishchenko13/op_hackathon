import pytest
from airport_service import search_airports

def test_search_by_city():
    results = search_airports("Amsterdam")
    assert len(results) > 0
    assert results[0]["iata"] == "AMS"
    assert "Schiphol Airport" in results[0]["display_name"]

def test_search_by_iata():
    results = search_airports("CDG")
    assert len(results) == 1
    assert results[0]["city"] == "Paris"

def test_short_and_empty_query():
    assert search_airports("") == []
    assert search_airports("a") == []

def test_limit():
    results = search_airports("Paris", limit=1)
    assert len(results) <= 1
def test_search_includes_additional_european_airports():
    assert search_airports("ZRH")[0]["city"] == "Zurich"
    assert search_airports("BRU")[0]["city"] == "Brussels"

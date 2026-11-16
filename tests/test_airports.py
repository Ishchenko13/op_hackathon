import pytest
from airport_service import search_airports

def test_search_by_city():
    results = search_airports("Amsterdam")
    assert len(results) > 0
    assert results[0]["iata"] == "AMS"
    assert results[0]["display_name"] == "Amsterdam — Schiphol Airport (AMS)"

def test_search_by_iata():
    results = search_airports("CDG")
    assert len(results) == 1
    assert results[0]["city"] == "Paris"
    assert results[0]["iata"] == "CDG"

def test_search_by_airport_name():
    results = search_airports("Heathrow")
    assert len(results) == 1
    assert results[0]["iata"] == "LHR"

def test_short_and_empty_queries():
    assert search_airports("") == []
    assert search_airports("a") == []
    assert search_airports(None) == []

def test_results_limit():
    results = search_airports("Paris", limit=1)
    assert len(results) <= 1
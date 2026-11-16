"""Contract tests for the flight provider service implemented by part 2."""

from datetime import date, timedelta

import pytest

flight_service = pytest.importorskip("flight_service")


def test_search_requires_an_api_token_outside_explicit_demo_mode(monkeypatch):
    monkeypatch.delenv("DUFFEL_ACCESS_TOKEN", raising=False)
    monkeypatch.setenv("FLIGHT_DEMO_MODE", "0")
    with pytest.raises(flight_service.FlightSearchError):
        flight_service.search_flights(
            "AMS", "CDG", date.today() + timedelta(days=30).isoformat()
        )


def test_search_rejects_invalid_iata_codes():
    with pytest.raises((ValueError, flight_service.FlightSearchError)):
        flight_service.search_flights(
            "Amsterdam", "CDG", date.today() + timedelta(days=30).isoformat()
        )

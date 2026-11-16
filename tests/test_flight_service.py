"""Tests for the shared flight search function."""

from datetime import date, timedelta

import pytest

flight_service = pytest.importorskip("flight_service")


def test_search_requires_credentials_when_demo_mode_is_off(monkeypatch):
    monkeypatch.delenv("DUFFEL_ACCESS_TOKEN", raising=False)
    monkeypatch.setenv("FLIGHT_DEMO_MODE", "0")
    with pytest.raises(Exception):
        flight_service.search_flights(
            "AMS", "CDG", date.today() + timedelta(days=30)
        )


def test_search_rejects_a_city_name_instead_of_iata_code():
    with pytest.raises(ValueError):
        flight_service.search_flights(
            "Amsterdam", "CDG", date.today() + timedelta(days=30)
        )

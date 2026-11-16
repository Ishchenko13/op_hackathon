"""Flask smoke tests without a live flight API or credentials."""

import sys
from datetime import date, timedelta
from types import ModuleType

import pytest

from app import app


@pytest.fixture
def flight_client(monkeypatch):
    airport_service = ModuleType("airport_service")
    flight_service = ModuleType("flight_service")
    airports = [
        dict(iata="AMS", city="Amsterdam", airport="Schiphol", country="Netherlands",
             display_name="Amsterdam — Schiphol (AMS)"),
        dict(iata="CDG", city="Paris", airport="Charles de Gaulle", country="France",
             display_name="Paris — Charles de Gaulle (CDG)"),
    ]

    def search_airports(query, limit=8):
        return [airport for airport in airports if query.lower() in airport["display_name"].lower()][:limit]

    airport_service.search_airports = search_airports
    monkeypatch.setitem(sys.modules, "airport_service", airport_service)
    monkeypatch.setitem(sys.modules, "flight_service", flight_service)
    monkeypatch.setenv("DUFFEL_ACCESS_TOKEN", "mock-token")

    query = dict(
        flight_search="1", origin="AMS", destination="CDG",
        origin_text=airports[0]["display_name"], destination_text=airports[1]["display_name"],
        departure_date=(date.today() + timedelta(days=30)).isoformat(),
        return_date=(date.today() + timedelta(days=35)).isoformat(), adults="2",
    )
    return app.test_client(), flight_service, query


def offer_for(query):
    dates = [query["departure_date"], query["return_date"]]
    routes = [("AMS", "CDG"), ("CDG", "AMS")]
    return {
        "total_amount": "99.50", "currency": "EUR", "airline": "Example Airline",
        "live_mode": True, "is_demo": False,
        "slices": [
            {
                "departure_time": f"{day}T09:30:00", "arrival_time": f"{day}T10:50:00",
                "duration": "PT1H20M", "stops": 0,
                "segments": [{
                    "origin_iata": origin, "destination_iata": destination,
                    "baggage": [{"passenger_id": "pas_test",
                                 "baggages": [{"type": "checked", "quantity": 1}]}],
                }],
            }
            for day, (origin, destination) in zip(dates, routes) if day
        ],
    }


def test_home_and_airport_autocomplete(flight_client):
    client, _, _ = flight_client
    home = client.get("/")
    assert home.status_code == 200
    assert b"Find flights" in home.data
    assert b"Compare cities" in home.data
    results = client.get("/api/airports?q=Amst").get_json()["airports"]
    assert [(a["city"], a["airport"], a["iata"]) for a in results] == [
        ("Amsterdam", "Schiphol", "AMS")
    ]
    assert client.get("/api/airports?q=unknown").get_json() == {"airports": []}


def test_mock_offers_render_in_price_order(flight_client):
    client, provider, query = flight_client

    def search_flights(origin, destination, departure, return_date=None, adults=1):
        assert (origin, destination, departure, return_date, adults) == (
            "AMS", "CDG", query["departure_date"], query["return_date"], 2,
        )
        details = offer_for(query)
        return [
            dict(details, airline="Expensive Airline", total_amount="200.00"),
            dict(details, airline="Cheaper Airline", live_mode=False, is_demo=True),
        ]

    provider.search_flights = search_flights
    response = client.get("/", query_string=query)
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert html.index("Cheaper Airline") < html.index("Expensive Airline")
    for detail in (
        "EUR", "99.50", "09:30", "10:50", "1h 20m", "1 checked", "Demo offer",
        "Live API offer", "AMS → CDG", "CDG → AMS", "Nonstop",
    ):
        assert detail in html


@pytest.mark.parametrize(("changes", "message"), [
    ({"origin": "", "origin_text": "Amsterdam"}, "from the suggestions"),
    ({"destination": "ZZZ"}, "from the suggestions"),
    ({"departure_date": "incorrect"}, "Choose valid travel dates"),
    ({"return_date": "2001-01-01"}, "return must be on or after departure"),
    ({"adults": "0"}, "Enter a whole number of passengers"),
    ({"adults": "10"}, "Enter a whole number of passengers"),
])
def test_invalid_input_stays_on_page(flight_client, changes, message):
    client, _, query = flight_client
    response = client.get("/", query_string=query | changes)
    assert response.status_code == 200
    assert message in response.get_data(as_text=True)


def test_missing_api_token_is_explained(flight_client, monkeypatch):
    client, _, query = flight_client
    monkeypatch.delenv("DUFFEL_ACCESS_TOKEN", raising=False)
    response = client.get("/", query_string=query)
    assert response.status_code == 200
    assert b"requires an API credential" in response.data


def test_empty_offers_and_api_error_are_explained(flight_client):
    client, provider, query = flight_client
    provider.search_flights = lambda *args, **kwargs: []
    response = client.get("/", query_string=query)
    assert response.status_code == 200
    assert b"No flights found" in response.data

    def fail(*args, **kwargs):
        raise RuntimeError("Private provider diagnostic")

    provider.search_flights = fail
    response = client.get("/", query_string=query)
    assert response.status_code == 200
    assert b"The flight provider could not return offers" in response.data
    assert b"Private provider diagnostic" not in response.data


def test_sandbox_offers_are_labeled_and_have_no_booking_link(flight_client, monkeypatch):
    client, provider, query = flight_client
    monkeypatch.setenv("DUFFEL_ACCESS_TOKEN", "duffel_test_mock")
    query = query | {"return_date": ""}
    provider.search_flights = lambda *args, **kwargs: [
        dict(offer_for(query), booking_url="https://example.org/book")
    ]
    response = client.get("/", query_string=query)
    assert response.status_code == 200
    assert b"Demo offer" in response.data
    assert b"Live API offer" not in response.data
    assert b"example.org/book" not in response.data


def test_unknown_provider_mode_is_not_claimed_as_live(flight_client):
    client, provider, query = flight_client
    provider.search_flights = lambda *args, **kwargs: [
        dict(offer_for(query), live_mode=None)
    ]
    response = client.get("/", query_string=query)
    assert response.status_code == 200
    assert b"API offer" in response.data
    assert b"Live API offer" not in response.data

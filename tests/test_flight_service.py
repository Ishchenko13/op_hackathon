"""Перевірки ізольовані від мережі й справжніх ключів."""
from copy import deepcopy
from unittest.mock import Mock

import pytest
import requests

from flight_service import FlightServiceError, FlightValidationError, search_flights


@pytest.fixture(autouse=True)
def api(monkeypatch):
    monkeypatch.setenv("DUFFEL_ACCESS_TOKEN", "test-placeholder-not-a-credential")
    post = Mock()
    monkeypatch.setattr("flight_service.requests.post", post)
    return post


@pytest.fixture
def offer():
    return {
        "id": "off_test", "total_amount": "150.00", "total_currency": "EUR",
        "live_mode": True,
        "slices": [{"duration": "PT2H30M", "segments": [{
            "id": "seg_test", "origin": {"iata_code": "WAW", "time_zone": "Europe/Warsaw"},
            "destination": {"iata_code": "BCN", "time_zone": "Europe/Madrid"},
            "operating_carrier": {"name": "Example Operating Airline"},
            "marketing_carrier": {"name": "Example Marketing Airline"},
            "marketing_carrier_flight_number": "123",
            "departing_at": "2099-08-10T09:00:00", "arriving_at": "2099-08-10T11:30:00",
            "duration": "PT2H30M", "passengers": [{
                "passenger_id": "pas_test", "baggages": [{"type": "checked", "quantity": 1}],
            }],
        }]}],
    }


def respond(api, offers):
    api.return_value = Mock(status_code=201)
    api.return_value.json.return_value = {"data": {"offers": offers}}


def test_request_and_normalized_result(api, offer):
    respond(api, [offer])
    result = search_flights(" waw ", "bcn", "2099-08-10", adults=2)[0]
    call = api.call_args.kwargs
    assert call["json"]["data"]["slices"] == [
        {"origin": "WAW", "destination": "BCN", "departure_date": "2099-08-10"}]
    assert call["json"]["data"]["passengers"] == [{"type": "adult"}] * 2
    assert call["headers"]["Duffel-Version"] == "v2"
    assert call["timeout"] == (5, 20)
    assert call["params"]["supplier_timeout"] == 10000
    assert call["allow_redirects"] is False
    assert result["provider"] == "duffel"
    assert result["total_amount"] == "150.00"
    assert result["currency"] == "EUR"
    assert result["airline"] == "Example Operating Airline"
    assert result["duration"] == "PT9000S"
    assert result["stops"] == 0
    assert result["baggage"][0]["passengers"][0]["baggages"][0]["quantity"] == 1
    assert result["segments"][0]["origin_time_zone"] == "Europe/Warsaw"
    assert result["departure_time"] == "2099-08-10T09:00:00"
    assert result["arrival_time"] == "2099-08-10T11:30:00"
    assert "test-placeholder" not in str(result)


def test_numeric_sort_and_limit(api, offer):
    offers = []
    for amount in ["100.00", "9.99", "20.00"]:
        item = deepcopy(offer)
        item.update(total_amount=amount, id=f"off_{amount}")
        offers.append(item)
    respond(api, offers)
    result = search_flights("WAW", "BCN", "2099-08-10", max_results=2)
    assert [item["total_amount"] for item in result] == ["9.99", "20.00"]


def test_round_trip_and_connections(api, offer):
    outbound = offer["slices"][0]
    outbound["segments"].append(deepcopy(outbound["segments"][0]))
    outbound["duration"] = "PT5H"
    inbound = deepcopy(offer["slices"][0])
    inbound["segments"] = [inbound["segments"][0]]
    inbound["duration"] = "PT3H"
    inbound["segments"][0].update(departing_at="2099-08-20T09:00:00", arriving_at="2099-08-20T12:00:00")
    offer["slices"].append(inbound)
    respond(api, [offer])
    result = search_flights("WAW", "BCN", "2099-08-10", "2099-08-20")[0]
    assert api.call_args.kwargs["json"]["data"]["slices"][1] == {
        "origin": "BCN", "destination": "WAW", "departure_date": "2099-08-20"}
    assert result["duration"] == "PT28800S"
    assert result["stops"] == 1
    assert [item["stops"] for item in result["slices"]] == [1, 0]
    assert result["arrival_time"] == "2099-08-20T12:00:00"


def test_unknown_baggage_and_test_label(api, offer):
    del offer["slices"][0]["segments"][0]["passengers"]
    offer["live_mode"] = False
    respond(api, [offer])
    result = search_flights("WAW", "BCN", "2099-08-10")[0]
    assert result["baggage"] is None
    assert result["is_demo"] is True
    assert result["label"] == "Демо, не реальні квитки"


def test_empty_offers(api):
    respond(api, [])
    assert search_flights("WAW", "BCN", "2099-08-10") == []


def test_missing_token(api, monkeypatch):
    monkeypatch.delenv("DUFFEL_ACCESS_TOKEN")
    with pytest.raises(FlightServiceError, match="DUFFEL_ACCESS_TOKEN"):
        search_flights("WAW", "BCN", "2099-08-10")
    api.assert_not_called()


@pytest.mark.parametrize("changes", [
    {"origin_iata": "WAW<script>"}, {"destination_iata": None},
    {"destination_iata": "WAW"}, {"departure_date": "10/08/2099"},
    {"departure_date": "2099-02-30"}, {"departure_date": "2000-01-01"},
    {"return_date": "2099-08-09"}, {"adults": 0}, {"adults": 10},
    {"adults": True}, {"adults": 1.5}, {"max_results": 0}, {"max_results": True},
])
def test_invalid_input_without_http(api, changes):
    args = dict(origin_iata="WAW", destination_iata="BCN", departure_date="2099-08-10")
    args.update(changes)
    with pytest.raises(FlightValidationError):
        search_flights(**args)
    api.assert_not_called()


@pytest.mark.parametrize("status", [301, 400, 401, 403, 429, 500])
def test_http_errors_are_sanitized(api, status):
    api.return_value = Mock(status_code=status, text="sensitive provider body")
    with pytest.raises(FlightServiceError) as error:
        search_flights("WAW", "BCN", "2099-08-10")
    assert "sensitive" not in str(error.value)
    assert "test-placeholder" not in str(error.value)


@pytest.mark.parametrize("exception", [requests.Timeout("secret"), requests.ConnectionError("secret")])
def test_network_errors_are_sanitized(api, exception):
    api.side_effect = exception
    with pytest.raises(FlightServiceError) as error:
        search_flights("WAW", "BCN", "2099-08-10")
    assert "secret" not in str(error.value)
    assert error.value.__suppress_context__


@pytest.mark.parametrize("body", [None, {}, {"data": {}}, {"data": {"offers": None}}, {"data": {"offers": [{}]}}])
def test_malformed_response(api, body):
    api.return_value = Mock(status_code=200)
    api.return_value.json.return_value = body
    with pytest.raises(FlightServiceError, match="некоректні дані"):
        search_flights("WAW", "BCN", "2099-08-10")


def test_non_json_response(api):
    api.return_value = Mock(status_code=200)
    api.return_value.json.side_effect = ValueError("secret")
    with pytest.raises(FlightServiceError, match="некоректні дані"):
        search_flights("WAW", "BCN", "2099-08-10")


@pytest.mark.parametrize("amount", ["NaN", "Infinity", "-1", "0", "not a price"])
def test_invalid_price(api, offer, amount):
    offer["total_amount"] = amount
    respond(api, [offer])
    with pytest.raises(FlightServiceError):
        search_flights("WAW", "BCN", "2099-08-10")


def test_mixed_currencies_not_ranked(api, offer):
    other = deepcopy(offer)
    other["total_currency"] = "USD"
    respond(api, [offer, other])
    with pytest.raises(FlightServiceError, match="валюти"):
        search_flights("WAW", "BCN", "2099-08-10")

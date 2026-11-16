"""Серверний пошук Duffel без бронювання, оплати чи пошуку аеропортів."""
import os
import re
from datetime import date
from decimal import Decimal, InvalidOperation

import requests

API_URL = "https://api.duffel.com/air/offer_requests"


class FlightServiceError(Exception):
    """Безпечне для показу користувачеві повідомлення."""


class FlightValidationError(FlightServiceError):
    """Некоректні параметри пошуку."""


def _iata(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z]{3}", value.strip()):
        raise FlightValidationError("Код аеропорту має містити три латинські літери.")
    return value.strip().upper()


def _date(value):
    try:
        if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise ValueError
        parsed = date.fromisoformat(value)
        if parsed < date.today():
            raise ValueError
        return parsed
    except ValueError:
        raise FlightValidationError("Вкажіть сьогоднішню або майбутню дату у форматі YYYY-MM-DD.") from None


def _duration_seconds(value):
    match = re.fullmatch(r"P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?", value)
    if not match or not any(match.groups()):
        raise ValueError
    days, hours, minutes, seconds = (int(part or 0) for part in match.groups())
    return days * 86400 + hours * 3600 + minutes * 60 + seconds


def _normalize(offer):
    amount = Decimal(offer["total_amount"])
    if not amount.is_finite() or amount <= 0:
        raise ValueError
    currency = offer["total_currency"]
    if not isinstance(currency, str) or not re.fullmatch(r"[A-Z]{3}", currency):
        raise ValueError
    if not isinstance(offer["id"], str) or not offer["id"]:
        raise ValueError
    slices, segments, baggage, airlines = [], [], [], []
    total_seconds = 0
    for slice_index, item in enumerate(offer["slices"]):
        leg_segments = []
        for segment in item["segments"]:
            carrier = segment["operating_carrier"]["name"]
            if not isinstance(carrier, str) or not carrier:
                raise ValueError
            if carrier not in airlines:
                airlines.append(carrier)
            allowances = [
                {"passenger_id": passenger.get("passenger_id"),
                 "baggages": passenger.get("baggages")}
                for passenger in segment.get("passengers", [])
                if passenger.get("baggages") is not None
            ]
            normalized = {
                "segment_id": segment["id"], "slice_index": slice_index,
                "origin_iata": segment["origin"]["iata_code"],
                "destination_iata": segment["destination"]["iata_code"],
                "airline": carrier,
                "marketing_airline": (segment.get("marketing_carrier") or {}).get("name"),
                "flight_number": segment.get("marketing_carrier_flight_number"),
                "departure_time": segment["departing_at"],
                "arrival_time": segment["arriving_at"],
                "origin_time_zone": segment["origin"].get("time_zone"),
                "destination_time_zone": segment["destination"].get("time_zone"),
                "duration": segment.get("duration"), "baggage": allowances or None,
            }
            leg_segments.append(normalized)
            if allowances:
                baggage.append({"segment_id": segment["id"], "passengers": allowances})
        if not leg_segments:
            raise ValueError
        total_seconds += _duration_seconds(item["duration"])
        slices.append({
            "segments": leg_segments,
            "departure_time": leg_segments[0]["departure_time"],
            "arrival_time": leg_segments[-1]["arrival_time"],
            "duration": item["duration"], "stops": len(leg_segments) - 1,
        })
        segments.extend(leg_segments)
    if not slices:
        raise ValueError
    is_test = offer.get("live_mode") is False
    return {
        "provider": "duffel", "offer_id": offer["id"],
        "total_amount": str(amount), "currency": currency,
        "airline": ", ".join(airlines), "segments": segments, "slices": slices,
        "departure_time": slices[0]["departure_time"],
        "arrival_time": slices[-1]["arrival_time"],
        "duration": f"PT{total_seconds}S",
        "stops": sum(item["stops"] for item in slices),
        "baggage": baggage or None, "live_mode": offer.get("live_mode"),
        "is_demo": is_test,
        "label": "Демо, не реальні квитки" if is_test else None,
    }


def search_flights(origin_iata, destination_iata, departure_date,
                   return_date=None, adults=1, max_results=10):
    """Повертає list[dict], відсортований за ціною; порожній пошук — [].

    Помилки: FlightServiceError. Сума — за всіх пасажирів та всі напрямки.
    """
    origin, destination = _iata(origin_iata), _iata(destination_iata)
    if origin == destination:
        raise FlightValidationError("Аеропорти вильоту та прибуття мають відрізнятися.")
    departure = _date(departure_date)
    if return_date is not None and _date(return_date) < departure:
        raise FlightValidationError("Дата повернення не може передувати даті вильоту.")
    if type(adults) is not int or not 1 <= adults <= 9:
        raise FlightValidationError("Кількість дорослих має бути цілим числом від 1 до 9.")
    if type(max_results) is not int or not 1 <= max_results <= 100:
        raise FlightValidationError("Кількість результатів має бути від 1 до 100.")
    token = os.environ.get("DUFFEL_ACCESS_TOKEN", "").strip()
    if not token:
        raise FlightServiceError("Пошук авіаквитків не налаштовано: відсутній DUFFEL_ACCESS_TOKEN.")
    slices = [{"origin": origin, "destination": destination, "departure_date": departure_date}]
    if return_date is not None:
        slices.append({"origin": destination, "destination": origin, "departure_date": return_date})
    try:
        response = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {token}", "Duffel-Version": "v2",
                     "Accept": "application/json"},
            params={"return_offers": "true", "supplier_timeout": 10000},
            json={"data": {"slices": slices, "passengers": [{"type": "adult"} for _ in range(adults)]}},
            timeout=(5, 20), allow_redirects=False,
        )
    except requests.Timeout:
        raise FlightServiceError("Пошук триває надто довго. Спробуйте ще раз.") from None
    except requests.RequestException:
        raise FlightServiceError("Не вдалося з’єднатися із сервісом авіаквитків.") from None
    if response.status_code in (401, 403):
        raise FlightServiceError("Сервіс авіаквитків відхилив доступ. Перевірте налаштування токена.")
    if response.status_code == 429:
        raise FlightServiceError("Забагато запитів. Повторіть пошук пізніше.")
    if not 200 <= response.status_code < 300:
        raise FlightServiceError("Постачальник не зміг виконати пошук. Спробуйте інші параметри або пізніше.")
    try:
        offers = response.json()["data"]["offers"]
        if not isinstance(offers, list):
            raise ValueError
        normalized = [_normalize(offer) for offer in offers]
        if len({offer["currency"] for offer in normalized}) > 1:
            raise FlightServiceError("Отримано різні валюти. Порівняння цін наразі недоступне.")
        return sorted(normalized, key=lambda offer: Decimal(offer["total_amount"]))[:max_results]
    except (ValueError, KeyError, TypeError, AttributeError, InvalidOperation):
        raise FlightServiceError("Сервіс авіаквитків повернув некоректні дані. Повторіть пошук пізніше.") from None

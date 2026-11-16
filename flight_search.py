"""Validate flight form input and adapt the team's services for the Flask view."""

import os
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from urllib.parse import urlsplit

from flask import current_app

IATA = re.compile(r"[A-Z]{3}")
FORM_FIELDS = (
    "origin", "destination", "origin_text", "destination_text",
    "departure_date", "return_date", "adults",
)


def airport_suggestions(query):
    from airport_service import search_airports

    return search_airports(query, limit=8)


def selected_airport(code):
    return IATA.fullmatch(code) and any(
        airport["iata"] == code for airport in airport_suggestions(code)
    )


def search_route(form, today):
    """Return normalized cards and a user-facing search message."""
    origin = form["origin"]
    destination = form["destination"]
    if not origin or not destination:
        return [], "Choose a departure and arrival airport from the suggestions."
    if origin == destination:
        return [], "Choose two different airports."

    try:
        departure = date.fromisoformat(form["departure_date"])
        returning = date.fromisoformat(form["return_date"]) if form["return_date"] else None
    except ValueError:
        return [], "Choose valid travel dates using the calendar."

    if departure < today or (returning and returning < departure):
        return [], "Departure must be today or later, and return must be on or after departure."

    try:
        adults = int(form["adults"])
        if adults < 1:
            raise ValueError
    except ValueError:
        return [], "Enter a whole number of passengers, at least 1."

    try:
        valid_route = selected_airport(origin) and selected_airport(destination)
    except (ImportError, ValueError, OSError, re.error):
        return [], "The airport catalog is unavailable. Try again later."
    if not valid_route:
        return [], "Choose a departure and arrival airport from the suggestions."

    demo_mode = os.environ.get("FLIGHT_DEMO_MODE") == "1"
    token = os.environ.get("DUFFEL_ACCESS_TOKEN", "").strip()
    if not demo_mode and not token:
        return [], "Flight search requires an API credential. Configure DUFFEL_ACCESS_TOKEN on the server."
    try:
        from flight_service import search_flights
    except ImportError:
        return [], "Flight offers are unavailable until the flight service is connected."

    try:
        offers = search_flights(
            origin, destination, departure, return_date=returning, adults=adults,
        )
        test_offers = demo_mode or token.startswith("duffel_test_")
        cards = [offer_card(offer, test_offers) for offer in (offers or [])]
    except Exception as exc:
        current_app.logger.warning("Flight search failed (%s)", type(exc).__name__)
        return [], "The flight provider could not return offers. Try again later."

    if not cards:
        return [], "No flights found for these airports and dates. Try a different route or date."
    cards.sort(key=lambda card: (card["currency"], card["price"]))
    currencies = {card["currency"] for card in cards}
    message = "Offers are grouped by currency and sorted by price within each group." if len(currencies) > 1 else ""
    return cards, message


def offer_card(offer, demo_mode):
    """Format a normalized service offer for the template."""
    try:
        price = Decimal(str(offer["price"]))
    except InvalidOperation as exc:
        raise ValueError("Invalid offer price") from exc
    currency = offer["currency"].upper()
    if not price.is_finite() or price < 0 or not IATA.fullmatch(currency):
        raise ValueError("Invalid offer price or currency")

    booking_url = offer.get("booking_url") or ""
    parsed = urlsplit(booking_url)
    is_demo = demo_mode or bool(offer.get("is_demo"))
    return {
        "price": price,
        "currency": currency,
        "airline": offer.get("airline"),
        "departure": offer.get("departure"),
        "arrival": offer.get("arrival"),
        "duration": offer.get("duration"),
        "stops": offer.get("stops"),
        "baggage": offer.get("baggage"),
        "booking_url": booking_url if not is_demo and parsed.scheme in {"http", "https"} and parsed.netloc else None,
        "is_demo": is_demo,
    }

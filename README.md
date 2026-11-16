# CrowdFree

CrowdFree is a Flask app for comparing European cities and finding flights between airports.

## Setup

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Add your Duffel API token to `.env` as `DUFFEL_ACCESS_TOKEN=...`. Never commit `.env` or share the token.

## Run

```powershell
python app.py
```

Open http://127.0.0.1:8000. The interface is in English.

## Demo

```powershell
python demo.py
```

The terminal demo uses the project's local city data. Demo flight offers, if enabled, must be clearly labeled and are not real tickets.

## Tests

```powershell
python -m pytest -q
```

Tests for `airport_service.py` and `flight_service.py` use the shared function interfaces and do not call the live API. They will run when those modules are added.

## Flight search functions

- `airport_service.search_airports(query, limit=8)` returns airport records with `iata`, `city`, `airport`, `country`, and `display_name`.
- `flight_service.search_flights(origin_iata, destination_iata, departure_date, return_date=None, adults=1, max_results=10)` accepts Python `date` values for departure and return. The Flask view expects offer records with `price` and `currency`. It also displays `airline`, `departure`, `arrival`, `duration`, `stops`, `baggage`, and `booking_url` when supplied. The optional boolean `is_demo` identifies sample offers. The view also labels offers from explicit demo mode or a Duffel test token as demo.

Flight prices can change before purchase. CrowdFree does not book tickets or take payment.

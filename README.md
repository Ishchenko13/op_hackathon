# CrowdFree

CrowdFree is a Flask travel-planning project. The current app compares European city-month options using price and a tourism activity proxy. The team is adding airport autocomplete and flight offers; the flight API works only after the flight-service and form changes are integrated.

## Setup (Windows PowerShell)

Python 3.10 or newer is recommended.

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Keep your real API token in `.env`. Do not commit `.env`; `.gitignore` excludes it. Add your Duffel token as `DUFFEL_ACCESS_TOKEN=...`. Until the flight service is integrated and a token is configured, use the current city comparison or tests with mocked API responses. Sample flight offers, if enabled with `FLIGHT_DEMO_MODE=1`, must be labeled as demo and are not bookable.

## Run the current terminal demo

```powershell
python demo.py
```

It reads `data/cities.csv` and `data/provenance.csv`, then prints the top three cities for month 6 with status, price, proxy, and score.

## Run tests

```powershell
python -m pytest -q
```

Airport and flight service contract tests are in `tests/test_airport_service.py` and `tests/test_flight_service.py`. They activate once the respective service modules are added. API tests must use mocked provider responses and must not require a live token or network access.

## Run the current web app

```powershell
python app.py
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/). Stop the server with Ctrl+C. After route-search integration, use the origin/destination airport suggestions, choose travel dates, and submit to see flight offers sorted by price.

## Smoke check after integration

Confirm that the home page loads; airport suggestions show a city, airport, and IATA code; invalid dates and unselected suggestions are rejected clearly; and a mocked flight search displays airline, total price/currency, times, duration, stops, and baggage when supplied. Verify that missing credentials produce a helpful message. Never describe demo fixtures as live ticket prices.

## Shared interfaces

- `airport_service.search_airports(query, limit=8)` returns airport records with `iata`, `city`, `airport`, `country`, and `display_name`.
- `flight_service.search_flights(origin_iata, destination_iata, departure_date, return_date=None, adults=1, max_results=10)` returns normalized offers. It reads `DUFFEL_ACCESS_TOKEN` on the server, never from browser code, and does not place orders or take payment.
- `recommender.rank_cities(data, cities, month, price_weight, top_n=3)` ranks city-month choices from the local CSV snapshot.

## Data and limitations

The existing app uses the snapshots and methodology recorded in `data/provenance.csv`; it does not query a live Airbnb API. The crowding index is a proxy, not a direct count of people. Flight fares returned by a provider are offers that can change before purchase. Check provider details and baggage rules before booking.

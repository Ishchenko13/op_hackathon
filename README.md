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

The suite checks the airport catalog, Duffel service with mocked HTTP responses, Flask flight form, and city recommender.

## Flight search

On the home page, select airport suggestions, choose your dates and number of adults, then click **Find flights**. The total price covers all passengers and both directions when a return is selected. Use a Duffel test token for sandbox offers, which the app labels as demo.

- `airport_service.search_airports(query, limit=8)` returns airport records with `iata`, `city`, `airport`, `country`, and `display_name`.
- `flight_service.search_flights(origin_iata, destination_iata, departure_date, return_date=None, adults=1, max_results=10)` accepts ISO dates (`YYYY-MM-DD`) and 1–9 adults. It returns price-sorted offers or an empty list. Provider errors raise `FlightServiceError`.
- An offer includes `total_amount`, `currency`, operating airlines, outbound and optional return slices, and any baggage allowances provided. Duffel's test offers include `is_demo`. Flight fares can change before purchase.

Flask loads the local `.env` at startup. When calling the service directly, set `DUFFEL_ACCESS_TOKEN` in the process environment. See the [Duffel offer schema](https://duffel.com/docs/api/offers).

## City data

The app uses the snapshots and methodology recorded in `data/provenance.csv`. The crowding index is a tourism activity proxy. Coverage is limited to city-month rows in the CSV files.

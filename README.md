# CrowdFree

CrowdFree ranks available city-month options using nightly price and a crowding proxy. The app currently serves a Flask web interface and reads the CSV files in `data/`.

## Setup (Windows PowerShell)

Python 3.10 or newer is recommended.

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Run the terminal demo

```powershell
python demo.py
```

The demo reads `data/cities.csv` and `data/provenance.csv`, then prints the top three cities for month 6 with data status, price, proxy, and score.

## Run tests

```powershell
python -m pytest -q
```

## Run the web app

```powershell
python app.py
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/). Select cities, a month, and the price weight, then click **Compare cities**. The page shows recommendations, data status, source information, or a message when data is unavailable. Stop the server with Ctrl+C.

## Smoke check

After starting the server, confirm that the page loads, changing the month or price weight updates the results, source details and observed/demo labels are visible, and a selection with no data displays a clear message. The automated Flask route checks are included in `tests/test_app.py`.

## Team interfaces

- `data_loader.py`: `load_city_data(path="data/cities.csv")` returns a DataFrame with `city`, integer `month`, `price_eur`, and `crowd_index`; city-month pairs are unique, prices are finite and positive, and proxy values are finite and nonnegative. `load_provenance(path="data/provenance.csv")` returns source metadata keyed by city and month, including URLs, snapshot dates or review periods, methodology, and `data_status` (`observed` or `demo`).
- `recommender.py`: `rank_cities(data, cities, month, price_weight, top_n=3)` returns `city`, `month`, `price_eur`, `crowd_index`, `score`, and `explanation`. Price weight is in `[0, 1]`; crowding weight is `1 - price_weight`. Empty selections and no matching rows return an empty DataFrame.
- `app.py`: Flask route that reads the form, calls the data and ranking functions, and renders recommendations, availability messages, provenance, and data status.

## Data and limitations

The app uses the snapshots and methodology recorded in `data/provenance.csv`; it does not query a live Airbnb API. Check the source links and snapshot dates before interpreting the results. The crowding index is a proxy for tourism activity, not a direct count of people. Coverage is limited to the city-month rows present in the CSV files.

## Flight search API (Duffel)

Set `DUFFEL_ACCESS_TOKEN` in the **server process environment** before starting
Flask. `.env.example` documents the variable; the service does not automatically
load `.env`. Never put tokens in browser code, forms, logs, or Git. `.env` and
`.env.*` are already ignored, except the empty `.env.example` template.

```python
from flight_service import FlightServiceError, search_flights

try:
    offers = search_flights("WAW", "BCN", "2027-08-10", adults=1)
except FlightServiceError as error:
    message = str(error)  # Safe message; do not render a traceback.
```

This standalone service does not change Flask routes or resolve airports. Pass
three-letter airport codes and ISO dates (`YYYY-MM-DD`). Dates must not be in the
past; return must be on/after departure. Limits: 1–9 adults, 1–100 results.
It returns a price-sorted list, or `[]` if no offers match. Errors raise
`FlightServiceError` (`FlightValidationError` for invalid inputs). Missing
credentials never trigger a fake-ticket fallback.

Offer fields: `provider`, `offer_id`, `total_amount` (decimal string, total for
all passengers and both directions), `currency`, `airline` (operating carriers),
`segments`, `slices`, `departure_time`, `arrival_time`, `duration`, `stops`,
`baggage`, `live_mode`, `is_demo`, `label`. Mixed currencies are rejected rather
than incorrectly ranked. Segments include operating/marketing airlines, flight
number, airport codes, local times, time zones and per-passenger baggage.
Missing baggage is `None`, not a claim of zero allowance.

`duration` is ISO 8601, summed across slices, including connections but excluding
the stay between outbound and return. `stops` sums connections across slices;
use `slices` for separate outbound/return summaries. Top-level arrival is the
final arrival, including the return for round trips. Display every segment's
operating airline and any `label` prominently. Duffel test offers
(`live_mode=false`) carry **Демо, не реальні квитки**; never present these as real
tickets. Unspecified live mode remains unknown. Prices are search quotes, not
guaranteed availability. Booking/payment are not implemented.

References: [Duffel offer requests](https://duffel.com/docs/api/offer-requests),
[offer schema](https://duffel.com/docs/api/offers).
Run offline mocked tests: `python -m pytest tests/test_flight_service.py -q`.

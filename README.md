# CrowdFree

CrowdFree compares city-month options using price and a crowding proxy. The project is split across four contributors; follow the shared interface below when integrating each part.

## Setup

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

The demo uses clearly labeled synthetic example values so it can run without the source-data files. Do not present them as observed Airbnb data.

## Run tests

```powershell
python -m pytest
```

Tests cover the ranking contract: output fields, city and month filtering, top-N limiting, slider endpoints, empty results, and invalid weights.

## Run the web app

```sh
python app.py
```

Open [CrowdFree](http://127.0.0.1:8000/). The form includes Amsterdam, Barcelona, Paris, Prague, Rome, and Vienna. Choose a month and price weight, then click **Compare cities**. When the data or ranking modules are still being prepared, the page shows a preview. Stop the server with Ctrl+C.

With the data and ranking modules in place, check that changing the weight updates the ranking when the metrics favor different cities and that an unavailable city-month selection shows a clear message.

## Team interfaces

- `data_loader.py`: `load_city_data(path="data/cities.csv")` returns a DataFrame with `city`, integer `month`, `price_eur`, and `crowd_index`; city-month pairs are unique, prices are finite and positive, and proxy values are finite and nonnegative. `load_provenance(path="data/provenance.csv")` returns source metadata by city and month, including URLs, snapshot dates or review periods, methodology, and `data_status` (`observed` or `demo`).
- `recommender.py`: `rank_cities(data, cities, month, price_weight, top_n=3)` returns `city`, `month`, `price_eur`, `crowd_index`, `score`, and `explanation`. Price weight is in `[0, 1]`; crowding weight is `1 - price_weight`. Empty selections and no matching rows return an empty DataFrame.
- `app.py`: Flask route that reads the form, calls the Python data and ranking functions, and renders recommendations, availability messages, provenance, and demo labels.
- `templates/index.html` and `static/style.css`: The HTML form and results layout, and the light-blue styling.

## Data and limitations

Observed source coverage, city-month availability, methodology, and limitations must be recorded by the data owner in `data/provenance.csv` and documented alongside the dataset. The demo values in `demo.py` are synthetic. A crowding index is a proxy and should not be described as a direct measurement of visitor counts.

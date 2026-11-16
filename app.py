"""Serve CrowdFree's HTML interface and connect it to the team modules."""

from calendar import month_name
from pathlib import Path

from flask import Flask, render_template, request

app = Flask(__name__)

DATA_DIR = Path(__file__).resolve().parent / "data"
CITIES = ("Amsterdam", "Barcelona", "Paris", "Prague", "Rome", "Vienna")
MONTHS = tuple(enumerate(month_name))[1:]
DATASETS = {
    "auto": "Use available data",
    "observed": "Observed data",
    "demo": "Demo data",
}


def compare(cities, month, price_percent, dataset):
    """Return the results and notices needed by the HTML template."""
    if not cities:
        return {"message": "Select at least one city to compare."}

    try:
        from data_loader import load_city_data, load_provenance
        from recommender import rank_cities
    except ModuleNotFoundError as exc:
        if exc.name not in {"data_loader", "recommender"}:
            raise
        return {"message": "The city data and ranking modules are being prepared."}

    try:
        data = load_city_data(str(DATA_DIR / "cities.csv"))
        provenance = load_provenance(str(DATA_DIR / "provenance.csv"))
    except FileNotFoundError:
        return {"message": "The city data and source files are being prepared."}
    except ValueError as exc:
        return {"message": f"The comparison data could not be loaded. {exc}"}

    candidates = data.loc[data["city"].isin(cities) & data["month"].eq(month)]
    sources = provenance.loc[provenance["city"].isin(cities) & provenance["month"].eq(month)]
    candidates = candidates.merge(
        sources[["city", "month", "data_status"]], on=["city", "month"]
    )

    if dataset == "auto":
        dataset = "observed" if candidates["data_status"].eq("observed").any() else "demo"

    eligible = candidates.loc[candidates["data_status"].eq(dataset), data.columns]
    if eligible.empty:
        return {"message": f"No comparison data for this selection in {month_name[month]}."}

    ranked = rank_cities(eligible, cities, month, price_percent / 100, top_n=3)
    details = sources.loc[
        sources["data_status"].eq(dataset) & sources["city"].isin(eligible["city"])
    ]
    details = details.astype(object).where(details.notna(), "")

    return {
        "active_dataset": dataset,
        "recommendations": ranked.to_dict("records"),
        "sources": details.to_dict("records"),
        "skipped": sorted(set(cities) - set(eligible["city"])),
        "message": "No recommendations are available for this selection." if ranked.empty else "",
    }


@app.get("/")
def index():
    submitted = request.args.get("compare") == "1"
    selected_cities = request.args.getlist("city") if submitted else CITIES
    cities = [city for city in CITIES if city in selected_cities]

    month = request.args.get("month", default=1, type=int)
    month = month if 1 <= month <= 12 else 1
    price_percent = request.args.get("price_weight", default=20, type=int)
    price_percent = min(100, max(0, price_percent))
    dataset = request.args.get("dataset", "auto")
    if dataset not in DATASETS:
        dataset = "auto"

    return render_template(
        "index.html",
        cities=CITIES,
        selected_cities=cities,
        months=MONTHS,
        month=month,
        month_label=month_name[month],
        price_percent=price_percent,
        datasets=DATASETS,
        dataset=dataset,
        **compare(cities, month, price_percent, dataset),
    )


if __name__ == "__main__":
    app.run(port=8000)

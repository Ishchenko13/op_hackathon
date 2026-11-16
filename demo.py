"""Run a terminal demo using the project's city and provenance CSV files."""

from pathlib import Path

from data_loader import load_city_data, load_provenance
from recommender import rank_cities


ROOT = Path(__file__).resolve().parent
MONTH = 6
PRICE_WEIGHT = 0.6


def main():
    data = load_city_data(ROOT / "data" / "cities.csv")
    provenance = load_provenance(ROOT / "data" / "provenance.csv")
    month_data = data.loc[data["month"].eq(MONTH)]
    if month_data.empty:
        print(f"No city data is available for month {MONTH}.")
        return

    ranked = rank_cities(
        month_data,
        cities=month_data["city"].tolist(),
        month=MONTH,
        price_weight=PRICE_WEIGHT,
        top_n=3,
    )
    ranked = ranked.merge(
        provenance[["city", "month", "data_status"]],
        on=["city", "month"],
        how="left",
    )

    print(f"CrowdFree demo | month {MONTH} | price weight {PRICE_WEIGHT:.0%}")
    for position, row in enumerate(ranked.itertuples(index=False), start=1):
        print(
            f"{position}. {row.city} [{row.data_status}] | "
            f"price EUR {row.price_eur:.2f} | crowd proxy {row.crowd_index:.2f} | "
            f"score {row.score:.3f}"
        )


if __name__ == "__main__":
    main()

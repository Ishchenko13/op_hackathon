"""Run a small terminal demo of CrowdFree's city ranking."""

import pandas as pd

from recommender import rank_cities


def main():
    demo_data = pd.DataFrame(
        [
            {"city": "Barcelona", "month": 6, "price_eur": 125.0, "crowd_index": 72.0},
            {"city": "Rome", "month": 6, "price_eur": 105.0, "crowd_index": 65.0},
            {"city": "Paris", "month": 6, "price_eur": 160.0, "crowd_index": 58.0},
            {"city": "Amsterdam", "month": 6, "price_eur": 145.0, "crowd_index": 82.0},
            {"city": "Vienna", "month": 6, "price_eur": 115.0, "crowd_index": 43.0},
        ]
    )
    ranked = rank_cities(
        demo_data,
        cities=demo_data["city"].tolist(),
        month=6,
        price_weight=0.6,
        top_n=3,
    )
    print("CrowdFree demo · June · price weight 60% · crowding weight 40%")
    if ranked.empty:
        print("No matching city data is available.")
        return
    for position, row in enumerate(ranked.itertuples(index=False), start=1):
        print(f"{position}. {row.city}: {row.explanation}")


if __name__ == "__main__":
    main()

import pandas as pd

from recommender import rank_cities

data = pd.DataFrame([
    {"city": "Barcelona", "month": 8, "price_eur": 150, "crowd_index": 80},
    {"city": "Rome", "month": 8, "price_eur": 100, "crowd_index": 60},
    {"city": "Vienna", "month": 8, "price_eur": 120, "crowd_index": 30},
])

result = rank_cities(
    data=data,
    cities=["Barcelona", "Rome", "Vienna"],
    month=8,
    price_weight=0.5,
)

print("Рейтинг міст — від найкращого результату:")
print(result.to_string(index=False))
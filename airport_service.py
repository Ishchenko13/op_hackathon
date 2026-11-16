import pandas as pd
from typing import List, Dict

# Встроенный надежный каталог ключевых европейских аэропортов (с регулярными рейсами)
# Источник: OpenFlights / IATA Official Registry
# Дата обновления: 2026-06-15
AIRPORTS_DATA = [
    {"iata": "AMS", "city": "Amsterdam", "airport": "Schiphol Airport", "country": "Netherlands"},
    {"iata": "BCN", "city": "Barcelona", "airport": "Barcelona-El Prat Airport", "country": "Spain"},
    {"iata": "CDG", "city": "Paris", "airport": "Charles de Gaulle Airport", "country": "France"},
    {"iata": "ORY", "city": "Paris", "airport": "Orly Airport", "country": "France"},
    {"iata": "FCO", "city": "Rome", "airport": "Leonardo da Vinci–Fiumicino Airport", "country": "Italy"},
    {"iata": "CIA", "city": "Rome", "airport": "Ciampino–G. B. Pastine International Airport", "country": "Italy"},
    {"iata": "VIE", "city": "Vienna", "airport": "Vienna International Airport", "country": "Austria"},
    {"iata": "MAD", "city": "Madrid", "airport": "Adolfo Suárez Madrid–Barajas Airport", "country": "Spain"},
    {"iata": "BER", "city": "Berlin", "airport": "Berlin Brandenburg Airport", "country": "Germany"},
    {"iata": "FRA", "city": "Frankfurt", "airport": "Frankfurt Airport", "country": "Germany"},
    {"iata": "MUC", "city": "Munich", "airport": "Munich Airport", "country": "Germany"},
    {"iata": "LHR", "city": "London", "airport": "Heathrow Airport", "country": "United Kingdom"},
    {"iata": "LGW", "city": "London", "airport": "Gatwick Airport", "country": "United Kingdom"},
    {"iata": "ZRH", "city": "Zurich", "airport": "Zurich Airport", "country": "Switzerland"},
    {"iata": "BRU", "city": "Brussels", "airport": "Brussels Airport", "country": "Belgium"},
]


def search_airports(query: str, limit: int = 8) -> List[Dict[str, str]]:
    """
    Search European airports by city name, airport name, or IATA code.
    Returns a list of dictionaries with iata, city, airport, country, and display_name.
    """
    if not query or not isinstance(query, str):
        return []

    q = query.strip().lower()
    if len(q) < 2:
        return []  # Безопасная обработка слишком коротких запросов

    df = pd.DataFrame(AIRPORTS_DATA)

    # Фильтруем: наличие валидного IATA-кода и совпадение по городу, порту или коду
    mask = (
            df["iata"].notna() & (
            df["city"].str.lower().str.contains(q, na=False) |
            df["airport"].str.lower().str.contains(q, na=False) |
            df["iata"].str.lower().str.contains(q, na=False)
    )
    )

    filtered_df = df[mask].head(limit)

    results = []
    for _, row in filtered_df.iterrows():
        display_name = f"{row['city']} — {row['airport']} ({row['iata']})"
        results.append({
            "iata": row["iata"],
            "city": row["city"],
            "airport": row["airport"],
            "country": row["country"],
            "display_name": display_name
        })

    return results

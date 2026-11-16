"""Local search over the checked-in European scheduled-airport catalogue."""

from pathlib import Path
import pandas as pd

AIRPORTS_PATH = Path(__file__).resolve().parent / "data" / "airports.csv"

# Major airports serving European capitals whose airport municipality differs.
CITY_OVERRIDES = {
    "AMS": "Amsterdam", "BRU": "Brussels", "CDG": "Paris", "ORY": "Paris",
    "FCO": "Rome", "CIA": "Rome", "VIE": "Vienna", "MAD": "Madrid",
    "BER": "Berlin", "LHR": "London", "LGW": "London", "WAW": "Warsaw",
    "WMI": "Warsaw", "PRG": "Prague", "CPH": "Copenhagen", "TLL": "Tallinn",
    "HEL": "Helsinki", "ATH": "Athens", "BUD": "Budapest", "KEF": "Reykjavik",
    "RKV": "Reykjavik", "DUB": "Dublin", "RIX": "Riga", "VNO": "Vilnius",
    "LUX": "Luxembourg", "MLA": "Valletta", "RMO": "Chisinau", "TGD": "Podgorica",
    "SKP": "Skopje", "OSL": "Oslo", "LIS": "Lisbon", "OTP": "Bucharest",
    "BBU": "Bucharest", "MSQ": "Minsk", "DME": "Moscow", "SVO": "Moscow",
    "VKO": "Moscow", "ZIA": "Moscow", "BEG": "Belgrade", "BTS": "Bratislava",
    "LJU": "Ljubljana", "ARN": "Stockholm", "BMA": "Stockholm", "NYO": "Stockholm",
    "BRN": "Bern", "TIA": "Tirana", "SJJ": "Sarajevo", "SOF": "Sofia",
    "ZAG": "Zagreb", "PRN": "Pristina", "ESB": "Ankara", "EVN": "Yerevan",
    "TBS": "Tbilisi", "GYD": "Baku", "LCA": "Nicosia", "PFO": "Nicosia",
}


def search_airports(query: str, limit: int = 8) -> list[dict[str, str]]:
    """Search by city, airport, or IATA code and return display-ready records."""
    if not isinstance(query, str) or len(query.strip()) < 2:
        return []
    if not isinstance(limit, int) or limit < 1:
        return []
    airports = pd.read_csv(AIRPORTS_PATH).fillna("")
    airports["city"] = airports.apply(
        lambda row: CITY_OVERRIDES.get(row["iata"], row["city"]), axis=1
    )
    term = query.strip()
    exact_code = airports["iata"].astype(str).str.casefold().eq(term.casefold())
    exact_city = airports["city"].astype(str).str.casefold().eq(term.casefold())
    mask = pd.Series(False, index=airports.index)
    for field in ("city", "airport", "iata"):
        mask |= airports[field].astype(str).str.contains(term, case=False, regex=False)
    matches = pd.concat([
        airports.loc[exact_code],
        airports.loc[~exact_code & exact_city],
        airports.loc[mask & ~exact_code & ~exact_city],
    ])
    results = []
    for item in matches.drop_duplicates("iata").head(limit).to_dict("records"):
        item["display_name"] = f"{item['city']} — {item['airport']} ({item['iata']})"
        results.append(item)
    return results

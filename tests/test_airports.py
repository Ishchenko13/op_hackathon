from airport_service import search_airports


def test_search_by_city():
    results = search_airports("Amsterdam")
    assert results
    assert results[0]["iata"] == "AMS"
    assert "Schiphol" in results[0]["display_name"]


def test_search_by_iata():
    results = search_airports("CDG")
    assert results[0]["iata"] == "CDG"
    assert results[0]["city"] == "Paris"


def test_short_and_empty_query():
    assert search_airports("") == []
    assert search_airports("a") == []


def test_limit():
    assert len(search_airports("Paris", limit=1)) <= 1


def test_search_includes_additional_european_airports():
    assert search_airports("ZRH")[0]["iata"] == "ZRH"
    assert search_airports("BRU")[0]["iata"] == "BRU"


def test_warsaw_and_capital_airports():
    for code in ("WAW", "WMI", "LCA", "PFO", "ESB", "EVN", "TBS", "GYD"):
        assert search_airports(code)[0]["iata"] == code
    assert {item["iata"] for item in search_airports("Warsaw")} >= {"WAW", "WMI"}
    assert search_airports("Ankara")[0]["iata"] == "ESB"
    assert search_airports("Yerevan")[0]["iata"] == "EVN"
    assert search_airports("Tbilisi")[0]["iata"] == "TBS"
    assert search_airports("Baku")[0]["iata"] == "GYD"
    assert {item["iata"] for item in search_airports("Nicosia")} >= {"LCA", "PFO"}

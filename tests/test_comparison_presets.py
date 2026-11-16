"""Exercise the guided comparison through the links users click."""

import re
from html import unescape
from urllib.parse import parse_qs, urlsplit

import pytest

from app import app


def find_link(page, label):
    link = re.search(
        rf'<a\b[^>]*\bhref="([^"]+)"[^>]*>\s*{re.escape(label)}\s*</a>',
        page,
    )
    assert link, f"Missing comparison link: {label}"
    return unescape(link[1])


@pytest.mark.parametrize(
    ("label", "weight", "cities", "metrics", "reason"),
    [
        (
            "Quietest option", "0", ["Barcelona", "Vienna"], ("35.00", "38.00"),
            "barcelona ranks first on tourism activity: 35 vs. 38 in vienna.",
        ),
        (
            "Cheapest stay", "100", ["Vienna", "Barcelona"], ("€95.00", "€110.00"),
            "vienna ranks first on price: €95.00 per night vs. €110.00 in barcelona.",
        ),
    ],
)
def test_january_comparison_preset(label, weight, cities, metrics, reason):
    client = app.test_client()
    homepage = client.get("/")
    assert homepage.status_code == 200
    example = client.get(find_link(homepage.get_data(as_text=True), "Try a comparison"))
    assert example.status_code == 200

    preset = find_link(example.get_data(as_text=True), label)
    query = parse_qs(urlsplit(preset).query)
    assert query["month"] == ["1"]
    assert sorted(query["city"]) == ["Barcelona", "Vienna"]
    assert query["price_weight"] == [weight]

    response = client.get(preset)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    headings = re.findall(r"<h3\b[^>]*>\s*(Barcelona|Vienna)\s*</h3>", html)
    assert headings[:2] == cities
    for metric in metrics:
        assert metric in html
    assert reason in html.lower()

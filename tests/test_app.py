from app import app


def test_home_page_renders_city_comparison():
    app.config.update(TESTING=True)
    response = app.test_client().get("/")
    assert response.status_code == 200
    assert b"CrowdFree" in response.data
    assert b"Compare cities" in response.data


def test_selection_without_city_shows_clear_message():
    app.config.update(TESTING=True)
    response = app.test_client().get("/?compare=1")
    assert response.status_code == 200
    assert b"Select at least one city to compare." in response.data


def test_available_city_month_shows_recommendation_and_sources():
    app.config.update(TESTING=True)
    response = app.test_client().get(
        "/?compare=1&city=Vienna&month=6&price_weight=60&dataset=observed"
    )
    assert response.status_code == 200
    assert b"Vienna" in response.data
    assert b"Data sources and methodology" in response.data
    assert b"insideairbnb.com/vienna" in response.data

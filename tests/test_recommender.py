import pandas as pd
import pytest

from recommender import rank_cities


@pytest.fixture
def sample_data():
    return pd.DataFrame(
        [
            {"city": "Paris", "month": 7, "price_eur": 150.0, "crowd_index": 80.0},
            {"city": "Rome", "month": 7, "price_eur": 100.0, "crowd_index": 40.0},
            {"city": "Vienna", "month": 7, "price_eur": 120.0, "crowd_index": 20.0},
            {"city": "Paris", "month": 8, "price_eur": 170.0, "crowd_index": 90.0},
        ]
    )


def test_returns_required_columns_and_requested_month(sample_data):
    result = rank_cities(sample_data, ["Paris", "Rome", "Vienna"], 7, 0.5)
    assert list(result.columns) == [
        "city", "month", "price_eur", "crowd_index", "score", "explanation"
    ]
    assert set(result["month"]) == {7}
    assert len(result) == 3


def test_filters_city_and_month_and_limits_results(sample_data):
    result = rank_cities(sample_data, ["Paris", "Rome", "Unknown"], 7, 0.5, top_n=1)
    assert len(result) == 1
    assert result.iloc[0]["city"] in {"Paris", "Rome"}
    assert result.iloc[0]["month"] == 7


def test_prefers_lower_price_when_price_has_all_weight(sample_data):
    result = rank_cities(sample_data, ["Paris", "Rome", "Vienna"], 7, 1.0)
    assert result.iloc[0]["city"] == "Rome"
    assert result.iloc[-1]["city"] == "Paris"


def test_prefers_lower_crowding_when_crowding_has_all_weight(sample_data):
    result = rank_cities(sample_data, ["Paris", "Rome", "Vienna"], 7, 0.0)
    assert result.iloc[0]["city"] == "Vienna"
    assert result.iloc[-1]["city"] == "Paris"


def test_explanations_are_present(sample_data):
    result = rank_cities(sample_data, ["Paris", "Rome"], 7, 0.25)
    assert result["explanation"].map(lambda value: isinstance(value, str) and value.strip()).all()


def test_empty_selection_returns_empty_result(sample_data):
    result = rank_cities(sample_data, [], 7, 0.5)
    assert result.empty
    assert list(result.columns) == [
        "city", "month", "price_eur", "crowd_index", "score", "explanation"
    ]


def test_no_matching_rows_returns_empty_result(sample_data):
    assert rank_cities(sample_data, ["Rome"], 1, 0.5).empty


@pytest.mark.parametrize("weight", [-0.01, 1.01])
def test_rejects_price_weight_outside_zero_to_one(sample_data, weight):
    with pytest.raises(ValueError):
        rank_cities(sample_data, ["Rome"], 7, weight)


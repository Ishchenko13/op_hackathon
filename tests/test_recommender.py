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


EXPECTED_COLUMNS = [
    "city", "month", "price_eur", "crowd_index", "score", "explanation"
]


def test_returns_contract_columns_and_requested_month(sample_data):
    result = rank_cities(sample_data, ["Paris", "Rome", "Vienna"], 7, 0.5)
    assert list(result.columns) == EXPECTED_COLUMNS
    assert set(result["month"]) == {7}
    assert len(result) == 3
    assert result["score"].is_monotonic_increasing


def test_filters_city_and_month_and_limits_results(sample_data):
    result = rank_cities(sample_data, ["Paris", "Rome", "Unknown"], 7, 0.5, top_n=1)
    assert len(result) == 1
    assert result.iloc[0]["city"] in {"Paris", "Rome"}
    assert result.iloc[0]["month"] == 7


def test_price_weight_endpoint_prefers_lower_price(sample_data):
    result = rank_cities(sample_data, ["Paris", "Rome", "Vienna"], 7, 1.0)
    assert result.iloc[0]["city"] == "Rome"
    assert result.iloc[-1]["city"] == "Paris"


def test_crowding_weight_endpoint_prefers_lower_crowding(sample_data):
    result = rank_cities(sample_data, ["Paris", "Rome", "Vienna"], 7, 0.0)
    assert result.iloc[0]["city"] == "Vienna"
    assert result.iloc[-1]["city"] == "Paris"


def test_explanations_include_metrics_and_slider_weights(sample_data):
    result = rank_cities(sample_data, ["Rome"], 7, 0.25)
    explanation = result.iloc[0]["explanation"]
    assert "100.00" in explanation
    assert "40.00" in explanation
    assert "25%" in explanation
    assert "75%" in explanation


def test_empty_selection_returns_empty_result_with_contract_columns(sample_data):
    result = rank_cities(sample_data, [], 7, 0.5)
    assert result.empty
    assert list(result.columns) == EXPECTED_COLUMNS


def test_no_matching_rows_returns_empty_result(sample_data):
    result = rank_cities(sample_data, ["Rome"], 1, 0.5)
    assert result.empty
    assert list(result.columns) == EXPECTED_COLUMNS


@pytest.mark.parametrize("weight", [-0.01, 1.01])
def test_rejects_price_weight_outside_zero_to_one(sample_data, weight):
    with pytest.raises(ValueError):
        rank_cities(sample_data, ["Rome"], 7, weight)

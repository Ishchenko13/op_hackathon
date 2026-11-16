import pandas as pd


RESULT_COLUMNS = [
    "city",
    "month",
    "price_eur",
    "crowd_index",
    "score",
    "explanation",
]


def _normalize(values):
    minimum = values.min()
    maximum = values.max()


    if minimum == maximum:
        return pd.Series(0.0, index=values.index)

    return (values - minimum) / (maximum - minimum)


def rank_cities(data, cities, month, price_weight, top_n=3):

    if not 0 <= price_weight <= 1:
        raise ValueError("Вага ціни має бути від 0 до 1.")

    if not isinstance(month, int) or not 1 <= month <= 12:
        raise ValueError("Місяць має бути цілим числом від 1 до 12.")

    if not isinstance(top_n, int) or top_n < 1:
        raise ValueError("Кількість результатів має бути додатним цілим числом.")

    if cities is None or len(cities) == 0:
        return pd.DataFrame(columns=RESULT_COLUMNS)

    required = {"city", "month", "price_eur", "crowd_index"}
    missing = required - set(data.columns)

    if missing:
        raise ValueError(
            f"У даних відсутні стовпці: {', '.join(sorted(missing))}"
        )

    selected = data.loc[
        data["city"].isin(cities) & (data["month"] == month),
        ["city", "month", "price_eur", "crowd_index"],
    ].copy()

    if selected.empty:
        return pd.DataFrame(columns=RESULT_COLUMNS)

    if selected.duplicated(["city", "month"]).any():
        raise ValueError("Знайдено повторні записи для одного міста й місяця.")

    for column in ["price_eur", "crowd_index"]:
        selected[column] = pd.to_numeric(
            selected[column], errors="coerce"
        )

        invalid = (
            selected[column].isna()
            | selected[column].isin([float("inf"), float("-inf")])
        )

        if invalid.any():
            raise ValueError(
                f"Стовпець {column} містить пропущені або некоректні числа."
            )

    if (selected["price_eur"] <= 0).any():
        raise ValueError("Ціна має бути більшою за нуль.")

    if (selected["crowd_index"] < 0).any():
        raise ValueError("Індекс активності не може бути від’ємним.")

    crowd_weight = 1 - price_weight


    selected["score"] = (
        price_weight * _normalize(selected["price_eur"])
        + crowd_weight * _normalize(selected["crowd_index"])
    )

    selected["explanation"] = selected.apply(
        lambda row: (
            f"Ціна: €{row['price_eur']:.2f}; "
            f"індекс активності: {row['crowd_index']:.2f}. "
            f"Вага ціни: {price_weight:.0%}, "
            f"активності: {crowd_weight:.0%}. "
            "Менший бал означає кращий результат. "
            "Індекс є непрямим показником туристичної активності, "
            "а не кількістю людей на вулицях."
        ),
        axis=1,
    )

    return (
        selected.sort_values(["score", "city"])
        .head(top_n)
        .reset_index(drop=True)[RESULT_COLUMNS]
    )
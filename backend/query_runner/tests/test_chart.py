import pytest
from query_runner.chart import detect_chart_type


def test_text_plus_numeric_returns_bar():
    result = detect_chart_type(["name", "total_sold"], [["Headphones", 342], ["Cable", 289]])
    assert result is not None
    assert result["type"] == "bar"
    assert result["x_key"] == "name"
    assert result["y_key"] == "total_sold"


def test_date_column_returns_line():
    result = detect_chart_type(["month", "revenue"], [["2024-01", 5000.0], ["2024-02", 6000.0]])
    assert result is not None
    assert result["type"] == "line"


def test_percent_column_returns_pie():
    result = detect_chart_type(["category", "share_percent"], [["Electronics", 45.0], ["Clothing", 30.0]])
    assert result is not None
    assert result["type"] == "pie"


def test_single_column_returns_none():
    result = detect_chart_type(["name"], [["Alice"]])
    assert result is None


def test_empty_rows_returns_none():
    result = detect_chart_type(["name", "total"], [])
    assert result is None


def test_all_numeric_returns_none():
    result = detect_chart_type(["id", "price"], [[1, 9.99], [2, 19.99]])
    assert result is None

import pytest
from query_runner.executor import execute_sql


def test_returns_columns_and_rows(demo_db_path):
    result = execute_sql("SELECT name FROM products ORDER BY id", db_path=demo_db_path)
    assert result["columns"] == ["name"]
    assert ["Headphones"] in result["rows"]


def test_returns_dict_with_correct_shape(demo_db_path):
    result = execute_sql("SELECT * FROM categories", db_path=demo_db_path)
    assert "columns" in result
    assert "rows" in result
    assert isinstance(result["rows"], list)


def test_auto_appends_limit_when_missing(demo_db_path):
    result = execute_sql("SELECT id FROM products", db_path=demo_db_path)
    assert len(result["rows"]) <= 500


def test_respects_explicit_limit(demo_db_path):
    result = execute_sql("SELECT id FROM products LIMIT 1", db_path=demo_db_path)
    assert len(result["rows"]) == 1


def test_empty_result(demo_db_path):
    result = execute_sql("SELECT * FROM customers WHERE id = 99999", db_path=demo_db_path)
    assert result["rows"] == []

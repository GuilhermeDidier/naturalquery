import pytest
from query_runner.validator import validate_select_only, InvalidSQLError


def test_valid_select_passes():
    validate_select_only("SELECT id, name FROM products")


def test_select_case_insensitive():
    validate_select_only("select * from customers")


def test_select_with_joins_passes():
    validate_select_only(
        "SELECT p.name, SUM(oi.quantity) FROM products p "
        "JOIN order_items oi ON p.id = oi.product_id GROUP BY p.id"
    )


def test_insert_raises():
    with pytest.raises(InvalidSQLError):
        validate_select_only("INSERT INTO products VALUES (1, 'x', 1, 9.9, 10)")


def test_update_raises():
    with pytest.raises(InvalidSQLError):
        validate_select_only("UPDATE products SET price=0 WHERE id=1")


def test_delete_raises():
    with pytest.raises(InvalidSQLError):
        validate_select_only("DELETE FROM products")


def test_drop_raises():
    with pytest.raises(InvalidSQLError):
        validate_select_only("DROP TABLE products")


def test_multiple_statements_raises():
    with pytest.raises(InvalidSQLError):
        validate_select_only("SELECT 1; DROP TABLE customers")

import sqlglot


class InvalidSQLError(Exception):
    pass


def validate_select_only(sql: str) -> None:
    """Raises InvalidSQLError if sql is not a single SELECT statement."""
    try:
        statements = sqlglot.parse(sql)
    except Exception as e:
        raise InvalidSQLError(f"Could not parse SQL: {e}") from e

    if not statements or len(statements) != 1:
        raise InvalidSQLError("Only single SELECT statements are allowed.")

    stmt = statements[0]
    if not isinstance(stmt, sqlglot.exp.Select):
        raise InvalidSQLError("Only SELECT queries are allowed.")

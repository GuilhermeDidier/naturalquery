import sqlite3
from django.conf import settings


class SQLExecutionError(Exception):
    pass


def execute_sql(sql: str, db_path=None) -> dict:
    """Execute a validated SELECT query. Returns {"columns": [...], "rows": [...]}."""
    if db_path is None:
        db_path = settings.DEMO_DB_PATH

    # Append LIMIT 500 if not present
    if "LIMIT" not in sql.upper():
        sql = f"{sql.rstrip(';')} LIMIT 500"

    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = [list(row) for row in cursor.fetchall()]
        return {"columns": columns, "rows": rows}
    except sqlite3.Error as e:
        raise SQLExecutionError(str(e)) from e
    finally:
        conn.close()

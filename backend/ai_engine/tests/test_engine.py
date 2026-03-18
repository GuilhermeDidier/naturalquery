import pytest
from unittest.mock import MagicMock, patch


def _make_tool_use_response(sql: str, tool_id: str = "toolu_01"):
    block = MagicMock()
    block.type = "tool_use"
    block.id = tool_id
    block.input = {"sql": sql}
    resp = MagicMock()
    resp.stop_reason = "tool_use"
    resp.content = [block]
    return resp


def _make_end_turn_response(text: str):
    block = MagicMock()
    block.type = "text"
    block.text = text
    resp = MagicMock()
    resp.stop_reason = "end_turn"
    resp.content = [block]
    return resp


FAKE_RESULTS = {"columns": ["name"], "rows": [["Headphones"]]}


@pytest.mark.django_db
def test_run_query_success(demo_db_path, settings):
    from ai_engine.engine import run_query

    settings.DEMO_DB_PATH = demo_db_path
    settings.ANTHROPIC_API_KEY = "test-key"

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [
        _make_tool_use_response("SELECT name FROM products LIMIT 5"),
        _make_end_turn_response("Here are the top products."),
    ]

    with patch("ai_engine.engine.anthropic.Anthropic", return_value=mock_client):
        with patch("ai_engine.engine.execute_sql", return_value=FAKE_RESULTS):
            sql, results, explanation = run_query("What are the top products?")

    assert sql == "SELECT name FROM products LIMIT 5"
    assert results == FAKE_RESULTS
    assert "products" in explanation.lower()


@pytest.mark.django_db
def test_run_query_raises_on_no_tool_call(settings):
    from ai_engine.engine import run_query, QueryEngineError

    settings.ANTHROPIC_API_KEY = "test-key"

    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_end_turn_response("I don't know.")

    with patch("ai_engine.engine.anthropic.Anthropic", return_value=mock_client):
        with pytest.raises(QueryEngineError):
            run_query("Tell me a joke")


@pytest.mark.django_db
def test_run_query_raises_invalid_sql(settings):
    from ai_engine.engine import run_query
    from query_runner.validator import InvalidSQLError

    settings.ANTHROPIC_API_KEY = "test-key"

    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_tool_use_response(
        "DROP TABLE customers"
    )

    with patch("ai_engine.engine.anthropic.Anthropic", return_value=mock_client):
        with pytest.raises(InvalidSQLError):
            run_query("Delete all customers")


@pytest.mark.django_db
def test_run_query_hits_iteration_limit(settings):
    from ai_engine.engine import run_query, QueryEngineError

    settings.ANTHROPIC_API_KEY = "test-key"

    mock_client = MagicMock()
    # Always returns tool_use → triggers iteration cap
    mock_client.messages.create.return_value = _make_tool_use_response("SELECT 1")

    with patch("ai_engine.engine.anthropic.Anthropic", return_value=mock_client):
        with patch("ai_engine.engine.execute_sql", return_value={"columns": ["1"], "rows": [[1]]}):
            with pytest.raises(QueryEngineError):
                run_query("Infinite loop question")

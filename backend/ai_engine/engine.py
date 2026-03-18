import json
import anthropic
from django.conf import settings
from query_runner.validator import validate_select_only
from query_runner.executor import execute_sql
from .prompt import build_user_message

TOOLS = [
    {
        "name": "execute_sql",
        "description": "Execute a SELECT SQL query against the e-commerce database and return results.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sql": {"type": "string", "description": "The SELECT SQL query to execute"}
            },
            "required": ["sql"],
        },
    }
]


class QueryEngineError(Exception):
    pass


def run_query(question: str) -> tuple:
    """
    Run a natural language question through the Claude tool-use loop.
    Returns (sql_generated: str, results: dict, explanation: str).
    Raises InvalidSQLError if Claude generates a non-SELECT query.
    Raises QueryEngineError if Claude cannot answer.
    """
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    messages = [{"role": "user", "content": build_user_message(question)}]

    last_sql = None
    last_results = None
    max_iterations = 3

    for iteration in range(max_iterations):
        response = client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=1024,
            temperature=0,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason == "tool_use":
            tool_use = next((b for b in response.content if b.type == "tool_use"), None)
            if not tool_use:
                raise QueryEngineError(
                    "Could not generate a valid query for this question. Please try rephrasing."
                )

            sql = tool_use.input["sql"]
            validate_select_only(sql)  # raises InvalidSQLError — propagates to view

            results = execute_sql(sql)
            last_sql = sql
            last_results = results

            messages.append({"role": "assistant", "content": response.content})
            messages.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": json.dumps(results),
                }],
            })

        elif response.stop_reason == "end_turn":
            explanation = next(
                (b.text for b in response.content if b.type == "text"), ""
            )
            if last_sql is None:
                raise QueryEngineError(
                    "Could not generate a valid query for this question. Please try rephrasing."
                )
            return last_sql, last_results, explanation

        else:
            raise QueryEngineError(
                "Could not generate a valid query for this question. Please try rephrasing."
            )

    raise QueryEngineError(
        "Could not generate a valid query for this question. Please try rephrasing."
    )

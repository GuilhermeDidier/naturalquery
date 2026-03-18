import pytest
from unittest.mock import patch

QUERY_URL = "/api/query"
HISTORY_URL = "/api/history"

FAKE_ENGINE_RESULT = (
    "SELECT name FROM products LIMIT 5",
    {"columns": ["name"], "rows": [["Headphones"], ["Cable"]]},
    "Here are the top 2 products.",
)


@pytest.mark.django_db
def test_query_requires_auth(api_client):
    resp = api_client.post(QUERY_URL, {"question": "show products"})
    assert resp.status_code == 401


@pytest.mark.django_db
def test_query_returns_full_response(auth_client):
    client, user = auth_client
    with patch("history.views.run_query", return_value=FAKE_ENGINE_RESULT):
        resp = client.post(QUERY_URL, {"question": "show products"}, format="json")
    assert resp.status_code == 200
    data = resp.json()
    assert data["sql_generated"] == "SELECT name FROM products LIMIT 5"
    assert data["results"]["columns"] == ["name"]
    assert data["explanation"] == "Here are the top 2 products."
    assert data["row_count"] == 2


@pytest.mark.django_db
def test_query_saves_to_history(auth_client):
    from history.models import QueryHistory
    client, user = auth_client
    with patch("history.views.run_query", return_value=FAKE_ENGINE_RESULT):
        client.post(QUERY_URL, {"question": "show products"}, format="json")
    assert QueryHistory.objects.filter(user=user).count() == 1


@pytest.mark.django_db
def test_query_missing_question_returns_400(auth_client):
    client, _ = auth_client
    resp = client.post(QUERY_URL, {}, format="json")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_history_returns_user_queries(auth_client):
    from history.models import QueryHistory
    client, user = auth_client
    QueryHistory.objects.create(
        user=user, question="Q", sql_generated="SELECT 1",
        explanation="E", results={"columns": ["id"], "rows": [[1]]},
        chart_config=None, row_count=1,
    )
    resp = client.get(HISTORY_URL)
    assert resp.status_code == 200
    assert len(resp.json()["results"]) == 1


@pytest.mark.django_db
def test_history_requires_auth(api_client):
    resp = api_client.get(HISTORY_URL)
    assert resp.status_code == 401


@pytest.mark.django_db
def test_history_capped_at_50(auth_client):
    from history.models import QueryHistory
    client, user = auth_client
    for i in range(55):
        QueryHistory.objects.create(
            user=user, question=f"Q{i}", sql_generated="SELECT 1",
            explanation="E", results={"columns": [], "rows": []},
            chart_config=None, row_count=0,
        )
    resp = client.get(HISTORY_URL)
    assert len(resp.json()["results"]) == 50

import pytest

REGISTER_URL = "/api/auth/register"
LOGIN_URL = "/api/auth/login"


@pytest.mark.django_db
def test_register_returns_token(api_client):
    resp = api_client.post(REGISTER_URL, {"username": "alice", "email": "a@b.com", "password": "secure123"})
    assert resp.status_code == 201
    assert "token" in resp.json()
    assert resp.json()["username"] == "alice"


@pytest.mark.django_db
def test_register_duplicate_username_returns_400(api_client, django_user_model):
    django_user_model.objects.create_user(username="alice", password="x")
    resp = api_client.post(REGISTER_URL, {"username": "alice", "email": "b@b.com", "password": "secure123"})
    assert resp.status_code == 400
    assert "errors" in resp.json()


@pytest.mark.django_db
def test_register_missing_password_returns_400(api_client):
    resp = api_client.post(REGISTER_URL, {"username": "bob", "email": "b@b.com"})
    assert resp.status_code == 400


@pytest.mark.django_db
def test_login_returns_token(api_client, django_user_model):
    django_user_model.objects.create_user(username="alice", password="secure123")
    resp = api_client.post(LOGIN_URL, {"username": "alice", "password": "secure123"})
    assert resp.status_code == 200
    assert "token" in resp.json()


@pytest.mark.django_db
def test_login_wrong_password_returns_400(api_client, django_user_model):
    django_user_model.objects.create_user(username="alice", password="secure123")
    resp = api_client.post(LOGIN_URL, {"username": "alice", "password": "wrong"})
    assert resp.status_code == 400
    assert "errors" in resp.json()

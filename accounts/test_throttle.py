import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db
PASSWORD = "Tr1cky-horse-battery"


@pytest.fixture
def api():
    return APIClient()


def login(api, password="wrong-password"):
    body = {"email": "nobody@example.com", "password": password}
    return api.post("/api/v1/auth/login/", body, format="json")


def test_login_is_blocked_after_five_attempts_in_a_minute(api):
    for _ in range(5):
        assert login(api).status_code == 401
    blocked = login(api)
    assert blocked.status_code == 429
    assert "Retry-After" in blocked.headers


def test_registration_is_blocked_after_ten_attempts_in_an_hour(api):
    def register(i):
        body = {"email": f"user{i}@example.com", "password": PASSWORD}
        return api.post("/api/v1/auth/register/", body, format="json")

    for i in range(10):
        assert register(i).status_code == 201
    assert register(10).status_code == 429


def test_other_endpoints_are_not_rate_limited_by_failed_logins(api):
    for _ in range(6):
        login(api)
    assert api.get("/healthz/").status_code == 200

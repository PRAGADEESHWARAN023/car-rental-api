import pytest
from django.db import OperationalError
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_health_check_reports_ok_without_logging_in():
    response = APIClient().get("/healthz/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "up"}


def test_health_check_returns_503_when_the_database_is_down(monkeypatch):
    class BrokenConnection:
        def cursor(self):
            raise OperationalError("database is down")

    monkeypatch.setattr("config.health.connection", BrokenConnection())
    response = APIClient().get("/healthz/")
    assert response.status_code == 503
    assert response.json()["database"] == "down"

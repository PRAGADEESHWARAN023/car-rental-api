import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db

User = get_user_model()
PASSWORD = "Tr1cky-horse-battery"
CAR = {
    "registration_number": "TN01AB1234",
    "make": "Toyota",
    "model": "Innova",
    "daily_price": "2500.00",
}


@pytest.fixture
def api():
    return APIClient()


def register(api, **overrides):
    data = {"email": "new@example.com", "password": PASSWORD, "first_name": "Asha"}
    data.update(overrides)
    return api.post("/api/v1/auth/register/", data, format="json")


def login(api, email="new@example.com", password=PASSWORD):
    body = {"email": email, "password": password}
    return api.post("/api/v1/auth/login/", body, format="json")


def bearer(api, token):
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")


def test_register_creates_customer_and_never_returns_password(api):
    response = register(api)
    assert response.status_code == 201
    assert "password" not in response.data
    user = User.objects.get(email="new@example.com")
    assert user.role == User.Role.CUSTOMER
    assert user.password != PASSWORD


def test_register_ignores_role_sent_by_client(api):
    response = register(api, role="admin", is_staff=True, is_superuser=True)
    assert response.status_code == 201
    user = User.objects.get(email="new@example.com")
    assert user.role == User.Role.CUSTOMER
    assert not user.is_staff and not user.is_superuser


def test_register_rejects_weak_password(api):
    assert register(api, password="12345678").status_code == 400
    assert User.objects.count() == 0


def test_register_rejects_duplicate_email(api):
    assert register(api).status_code == 201
    assert register(api).status_code == 400


def test_login_returns_access_and_refresh_tokens(api):
    register(api)
    response = login(api)
    assert response.status_code == 200
    assert "access" in response.data and "refresh" in response.data


def test_login_with_wrong_password_is_rejected(api):
    register(api)
    assert login(api, password="wrong-Pass-999").status_code == 401


def test_me_requires_a_token(api):
    assert api.get("/api/v1/auth/me/").status_code == 401


def test_me_returns_the_logged_in_user(api):
    register(api)
    bearer(api, login(api).data["access"])
    response = api.get("/api/v1/auth/me/")
    assert response.status_code == 200
    assert response.data["email"] == "new@example.com"
    assert response.data["role"] == "customer"


def test_staff_token_can_create_car_but_customer_token_cannot(api):
    register(api)
    bearer(api, login(api).data["access"])
    assert api.post("/api/v1/cars/", CAR, format="json").status_code == 403

    User.objects.create_user(
        email="staff@example.com", password=PASSWORD, role=User.Role.STAFF
    )
    staff_api = APIClient()
    token = login(staff_api, "staff@example.com").data["access"]
    bearer(staff_api, token)
    assert staff_api.post("/api/v1/cars/", CAR, format="json").status_code == 201

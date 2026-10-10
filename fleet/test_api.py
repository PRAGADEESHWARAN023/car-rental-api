import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from fleet.models import Car

pytestmark = pytest.mark.django_db
User = get_user_model()
URL = "/api/v1/cars/"
CAR = {
    "registration_number": "TN01AB1234",
    "make": "Toyota",
    "model": "Innova",
    "daily_price": "2500.00",
}


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def customer():
    return User.objects.create_user(email="c@example.com", password="pw-12345-x")


@pytest.fixture
def staff():
    return User.objects.create_user(
        email="s@example.com", password="pw-12345-x", role=User.Role.STAFF
    )


def make_two_cars():
    Car.objects.create(**CAR)
    Car.objects.create(
        **{**CAR, "registration_number": "TN02CD5678"},
        status=Car.Status.MAINTENANCE,
    )


def test_anonymous_sees_only_available_cars(api):
    make_two_cars()
    response = api.get(URL)
    assert response.status_code == 200
    assert [c["registration_number"] for c in response.data["results"]] == [
        "TN01AB1234"
    ]


def test_staff_sees_all_cars(api, staff):
    make_two_cars()
    api.force_authenticate(staff)
    assert len(api.get(URL).data["results"]) == 2


def test_customer_cannot_create_car(api, customer):
    api.force_authenticate(customer)
    assert api.post(URL, CAR, format="json").status_code == 403
    assert Car.objects.count() == 0


def test_anonymous_cannot_create_car(api):
    # 401 or 403 depending on the authentication scheme; JWT arrives later
    assert api.post(URL, CAR, format="json").status_code in (401, 403)


def test_staff_can_create_car(api, staff):
    api.force_authenticate(staff)
    response = api.post(URL, CAR, format="json")
    assert response.status_code == 201
    assert Car.objects.get().registration_number == "TN01AB1234"


def test_staff_cannot_create_car_with_zero_price(api, staff):
    api.force_authenticate(staff)
    response = api.post(URL, {**CAR, "daily_price": "0"}, format="json")
    assert response.status_code == 400
    assert Car.objects.count() == 0


def test_staff_can_update_car_status(api, staff):
    car = Car.objects.create(**CAR)
    api.force_authenticate(staff)
    response = api.patch(f"{URL}{car.id}/", {"status": "maintenance"}, format="json")
    assert response.status_code == 200
    car.refresh_from_db()
    assert car.status == Car.Status.MAINTENANCE


def test_nobody_can_delete_a_car(api, staff):
    car = Car.objects.create(**CAR)
    api.force_authenticate(staff)
    assert api.delete(f"{URL}{car.id}/").status_code == 405
    assert Car.objects.count() == 1

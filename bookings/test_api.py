from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from bookings.models import Booking
from fleet.models import Car

pytestmark = pytest.mark.django_db

User = get_user_model()
URL = "/api/v1/bookings/"


def day(offset):
    return timezone.localdate() + timedelta(days=offset)


def payload(car, start=5, end=8):
    return {
        "car": car.id,
        "start_date": day(start).isoformat(),
        "end_date": day(end).isoformat(),
    }


@pytest.fixture
def car():
    return Car.objects.create(
        registration_number="TN01AB1234",
        make="Toyota",
        model="Innova",
        daily_price="2500.00",
    )


@pytest.fixture
def customer():
    return User.objects.create_user(email="c@example.com", password="pw-12345-x")


@pytest.fixture
def other_customer():
    return User.objects.create_user(email="o@example.com", password="pw-12345-x")


@pytest.fixture
def staff():
    return User.objects.create_user(
        email="s@example.com", password="pw-12345-x", role=User.Role.STAFF
    )


@pytest.fixture
def api():
    return APIClient()


def test_anonymous_cannot_list_or_create(api, car):
    assert api.get(URL).status_code == 401
    assert api.post(URL, payload(car), format="json").status_code == 401


def test_booking_is_priced_by_the_server(api, customer, car):
    api.force_authenticate(customer)
    response = api.post(URL, payload(car, 5, 8), format="json")
    assert response.status_code == 201
    assert Decimal(response.data["total_price"]) == Decimal("7500.00")
    assert response.data["status"] == "pending"
    assert Booking.objects.get().user == customer


def test_client_cannot_set_price_status_or_owner(api, customer, other_customer, car):
    api.force_authenticate(customer)
    body = {
        **payload(car),
        "total_price": "1.00",
        "status": "confirmed",
        "payment_status": "paid",
        "user": other_customer.id,
    }
    response = api.post(URL, body, format="json")
    assert response.status_code == 201
    booking = Booking.objects.get()
    assert booking.total_price == Decimal("7500.00")
    assert booking.status == Booking.Status.PENDING
    assert booking.payment_status == Booking.PaymentStatus.UNPAID
    assert booking.user == customer


def test_cannot_book_in_the_past(api, customer, car):
    api.force_authenticate(customer)
    response = api.post(URL, payload(car, -2, 3), format="json")
    assert response.status_code == 400
    assert "start_date" in response.data


def test_end_date_must_be_after_start_date(api, customer, car):
    api.force_authenticate(customer)
    response = api.post(URL, payload(car, 5, 5), format="json")
    assert response.status_code == 400
    assert "end_date" in response.data


@pytest.mark.parametrize("status", ["maintenance", "retired"])
def test_cannot_book_a_car_that_is_not_available(api, customer, car, status):
    car.status = status
    car.save()
    api.force_authenticate(customer)
    assert api.post(URL, payload(car), format="json").status_code == 400
    assert Booking.objects.count() == 0


def test_overlapping_booking_gets_409(api, customer, other_customer, car):
    api.force_authenticate(customer)
    assert api.post(URL, payload(car, 5, 9), format="json").status_code == 201
    api.force_authenticate(other_customer)
    response = api.post(URL, payload(car, 7, 11), format="json")
    assert response.status_code == 409
    assert Booking.objects.count() == 1


def test_back_to_back_bookings_are_allowed(api, customer, other_customer, car):
    api.force_authenticate(customer)
    assert api.post(URL, payload(car, 5, 9), format="json").status_code == 201
    api.force_authenticate(other_customer)
    assert api.post(URL, payload(car, 9, 12), format="json").status_code == 201


def test_customer_sees_only_own_bookings(api, customer, other_customer, car):
    api.force_authenticate(customer)
    api.post(URL, payload(car, 5, 8), format="json")
    api.force_authenticate(other_customer)
    api.post(URL, payload(car, 10, 12), format="json")
    response = api.get(URL)
    assert response.status_code == 200
    assert len(response.data["results"]) == 1


def test_customer_cannot_read_someone_elses_booking(api, customer, other_customer, car):
    api.force_authenticate(customer)
    booking_id = api.post(URL, payload(car), format="json").data["id"]
    api.force_authenticate(other_customer)
    assert api.get(f"{URL}{booking_id}/").status_code == 404


def test_staff_sees_all_bookings(api, customer, other_customer, staff, car):
    api.force_authenticate(customer)
    api.post(URL, payload(car, 5, 8), format="json")
    api.force_authenticate(other_customer)
    api.post(URL, payload(car, 10, 12), format="json")
    api.force_authenticate(staff)
    assert len(api.get(URL).data["results"]) == 2


def test_nobody_can_delete_or_edit_a_booking(api, customer, car):
    api.force_authenticate(customer)
    booking_id = api.post(URL, payload(car), format="json").data["id"]
    assert api.delete(f"{URL}{booking_id}/").status_code == 405
    response = api.patch(f"{URL}{booking_id}/", {"status": "confirmed"}, format="json")
    assert response.status_code == 405

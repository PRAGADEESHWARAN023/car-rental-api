from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient

from bookings.models import Booking
from fleet.models import Car

pytestmark = pytest.mark.django_db

User = get_user_model()
URL = "/api/v1/bookings/"


def add_bookings(count, first_index=0):
    """Each booking gets its own user and car, the worst case for extra queries."""
    start = timezone.localdate() + timedelta(days=5)
    for i in range(first_index, first_index + count):
        user = User.objects.create_user(email=f"user{i}@example.com")
        car = Car.objects.create(
            registration_number=f"TN01AB{i:04d}",
            make="Toyota",
            model="Innova",
            daily_price="2500.00",
        )
        Booking.objects.create(
            user=user,
            car=car,
            start_date=start,
            end_date=start + timedelta(days=3),
            total_price="7500.00",
        )


def staff_client():
    staff = User.objects.create_user(email="staff@example.com", role=User.Role.STAFF)
    api = APIClient()
    api.force_authenticate(staff)
    return api


def measure(api, url):
    with CaptureQueriesContext(connection) as queries:
        response = api.get(url)
    assert response.status_code == 200
    return len(queries), response


def test_list_query_count_does_not_grow_with_the_number_of_bookings():
    api = staff_client()
    add_bookings(3)
    queries_for_3, response = measure(api, URL)
    assert len(response.data["results"]) == 3
    add_bookings(7, first_index=3)
    queries_for_10, response = measure(api, URL)
    assert len(response.data["results"]) == 10
    assert queries_for_10 == queries_for_3, (
        f"{queries_for_3} queries for 3 bookings, {queries_for_10} for 10"
    )
    assert queries_for_10 <= 3


def test_one_booking_is_read_with_a_single_query():
    api = staff_client()
    add_bookings(1)
    booking = Booking.objects.get()
    queries, response = measure(api, f"{URL}{booking.id}/")
    assert response.data["car_details"]["make"] == "Toyota"
    assert response.data["customer_email"] == "user0@example.com"
    assert queries == 1

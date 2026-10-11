import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.utils import timezone

from bookings.exceptions import CarNotAvailable
from bookings.models import Booking
from bookings.services import create_booking
from fleet.models import Car

User = get_user_model()

CONCURRENT_REQUESTS = 20
ROUNDS = 5


def day(offset):
    return timezone.localdate() + timedelta(days=offset)


def make_car(registration_number):
    return Car.objects.create(
        registration_number=registration_number,
        make="Toyota",
        model="Innova",
        daily_price="2500.00",
    )


def make_users(count):
    return [
        User.objects.create_user(email=f"user{i}@example.com") for i in range(count)
    ]


def run_together(jobs):
    """Run every job in its own thread, released at the same moment."""
    barrier = threading.Barrier(len(jobs))

    def run(job):
        try:
            connection.ensure_connection()
            barrier.wait()
            return job()
        finally:
            connection.close()  # each thread opens its own database connection

    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        return list(pool.map(run, jobs))


def try_booking(user, car, start, end):
    def job():
        try:
            create_booking(user=user, car=car, start_date=start, end_date=end)
            return "booked"
        except CarNotAvailable:
            return "rejected"

    return job


@pytest.mark.django_db(transaction=True)
def test_many_simultaneous_requests_for_one_car_produce_one_booking():
    car = make_car("TN01AB1234")
    users = make_users(CONCURRENT_REQUESTS)
    for round_number in range(ROUNDS):
        start = day(5 + 10 * round_number)
        end = day(9 + 10 * round_number)
        results = run_together([try_booking(u, car, start, end) for u in users])
        assert results.count("booked") == 1
        assert results.count("rejected") == CONCURRENT_REQUESTS - 1
    assert Booking.objects.count() == ROUNDS


@pytest.mark.django_db(transaction=True)
def test_simultaneous_requests_for_different_cars_all_succeed():
    users = make_users(CONCURRENT_REQUESTS)
    cars = [make_car(f"TN01AB{i:04d}") for i in range(CONCURRENT_REQUESTS)]
    jobs = [try_booking(user, car, day(5), day(9)) for user, car in zip(users, cars)]
    assert run_together(jobs) == ["booked"] * CONCURRENT_REQUESTS
    assert Booking.objects.count() == CONCURRENT_REQUESTS

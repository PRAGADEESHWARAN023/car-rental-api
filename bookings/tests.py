from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

from bookings.models import Booking
from fleet.models import Car

pytestmark = pytest.mark.django_db

User = get_user_model()


@pytest.fixture
def user():
    return User.objects.create_user(email="c@example.com", password="pw-12345-x")


def make_car(registration_number="TN01AB1234"):
    return Car.objects.create(
        registration_number=registration_number,
        make="Toyota",
        model="Innova",
        daily_price="2500.00",
    )


def book(user, car, start, end, **overrides):
    data = {
        "user": user,
        "car": car,
        "start_date": start,
        "end_date": end,
        "total_price": "2500.00",
    }
    data.update(overrides)
    return Booking.objects.create(**data)


def test_overlapping_booking_is_rejected_by_the_database(user):
    car = make_car()
    book(user, car, date(2026, 11, 1), date(2026, 11, 5))
    with pytest.raises(IntegrityError), transaction.atomic():
        book(user, car, date(2026, 11, 3), date(2026, 11, 7))
    assert Booking.objects.count() == 1


def test_one_day_overlap_is_still_rejected(user):
    car = make_car()
    book(user, car, date(2026, 11, 1), date(2026, 11, 5))
    with pytest.raises(IntegrityError), transaction.atomic():
        book(user, car, date(2026, 11, 4), date(2026, 11, 8))
    assert Booking.objects.count() == 1


def test_back_to_back_bookings_are_allowed(user):
    car = make_car()
    book(user, car, date(2026, 11, 1), date(2026, 11, 5))
    book(user, car, date(2026, 11, 5), date(2026, 11, 8))
    assert Booking.objects.count() == 2


def test_different_cars_can_share_the_same_dates(user):
    book(user, make_car("TN01AB1234"), date(2026, 11, 1), date(2026, 11, 5))
    book(user, make_car("TN02CD5678"), date(2026, 11, 1), date(2026, 11, 5))
    assert Booking.objects.count() == 2


def test_cancelled_booking_frees_the_dates(user):
    car = make_car()
    book(
        user,
        car,
        date(2026, 11, 1),
        date(2026, 11, 5),
        status=Booking.Status.CANCELLED,
    )
    book(user, car, date(2026, 11, 2), date(2026, 11, 4))
    assert Booking.objects.count() == 2


def test_end_date_must_be_after_start_date(user):
    car = make_car()
    with pytest.raises(IntegrityError), transaction.atomic():
        book(user, car, date(2026, 11, 5), date(2026, 11, 5))
    assert Booking.objects.count() == 0

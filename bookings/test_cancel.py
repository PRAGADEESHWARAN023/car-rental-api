from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from bookings.exceptions import BookingNotCancellable
from bookings.models import Booking
from bookings.services import cancel_booking
from bookings.test_concurrency import run_together
from fleet.models import Car

User = get_user_model()


def day(offset):
    return timezone.localdate() + timedelta(days=offset)


def cancel_url(booking):
    return f"/api/v1/bookings/{booking.id}/cancel/"


@pytest.fixture
def api():
    return APIClient()


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
    return User.objects.create_user(email="c@example.com")


@pytest.fixture
def other_customer():
    return User.objects.create_user(email="o@example.com")


@pytest.fixture
def staff():
    return User.objects.create_user(email="s@example.com", role=User.Role.STAFF)


@pytest.fixture
def make_booking(car, customer):
    def make(**overrides):
        data = {
            "user": customer,
            "car": car,
            "start_date": day(5),
            "end_date": day(8),
            "total_price": Decimal("7500.00"),
            "payment_status": Booking.PaymentStatus.PAID,
        }
        data.update(overrides)
        return Booking.objects.create(**data)

    return make


@pytest.mark.django_db
def test_owner_cancelling_a_paid_booking_pays_five_percent(api, customer, make_booking):
    booking = make_booking()
    api.force_authenticate(customer)
    response = api.post(cancel_url(booking))
    assert response.status_code == 200
    booking.refresh_from_db()
    assert booking.status == Booking.Status.CANCELLED
    assert booking.cancelled_at is not None
    assert booking.cancellation_fee == Decimal("375.00")
    assert booking.payment_status == Booking.PaymentStatus.REFUNDED
    assert Decimal(str(response.data["refund_amount"])) == Decimal("7125.00")


@pytest.mark.django_db
def test_cancelling_an_unpaid_booking_costs_nothing(api, customer, make_booking):
    booking = make_booking(payment_status=Booking.PaymentStatus.UNPAID)
    api.force_authenticate(customer)
    assert api.post(cancel_url(booking)).status_code == 200
    booking.refresh_from_db()
    assert booking.status == Booking.Status.CANCELLED
    assert booking.cancellation_fee == Decimal("0.00")
    assert booking.payment_status == Booking.PaymentStatus.UNPAID


@pytest.mark.django_db
def test_staff_cancelling_for_a_customer_refunds_in_full(api, staff, make_booking):
    booking = make_booking()
    api.force_authenticate(staff)
    response = api.post(cancel_url(booking))
    assert response.status_code == 200
    booking.refresh_from_db()
    assert booking.cancellation_fee == Decimal("0.00")
    assert booking.payment_status == Booking.PaymentStatus.REFUNDED
    assert Decimal(str(response.data["refund_amount"])) == Decimal("7500.00")


@pytest.mark.django_db
def test_fee_is_rounded_to_whole_paise(customer, make_booking):
    booking = make_booking(total_price=Decimal("100.10"))
    cancel_booking(booking_id=booking.id, actor=customer)
    booking.refresh_from_db()
    assert booking.cancellation_fee == Decimal("5.01")  # 5.005 rounds half up


@pytest.mark.django_db
def test_cancelled_booking_frees_the_dates_for_someone_else(
    api, customer, other_customer, car, make_booking
):
    booking = make_booking()
    api.force_authenticate(customer)
    api.post(cancel_url(booking))
    api.force_authenticate(other_customer)
    response = api.post(
        "/api/v1/bookings/",
        {
            "car": car.id,
            "start_date": day(5).isoformat(),
            "end_date": day(8).isoformat(),
        },
        format="json",
    )
    assert response.status_code == 201


@pytest.mark.django_db
@pytest.mark.parametrize("start_offset", [0, -2])
def test_cannot_cancel_on_or_after_the_start_date(
    api, customer, make_booking, start_offset
):
    booking = make_booking(start_date=day(start_offset), end_date=day(4))
    api.force_authenticate(customer)
    assert api.post(cancel_url(booking)).status_code == 409
    booking.refresh_from_db()
    assert booking.status == Booking.Status.PENDING


@pytest.mark.django_db
@pytest.mark.parametrize("status", ["active", "completed", "cancelled"])
def test_only_pending_or_confirmed_bookings_can_be_cancelled(
    api, customer, make_booking, status
):
    booking = make_booking(status=status)
    api.force_authenticate(customer)
    assert api.post(cancel_url(booking)).status_code == 409
    booking.refresh_from_db()
    assert booking.status == status
    assert booking.cancellation_fee == Decimal("0.00")


@pytest.mark.django_db
def test_cancelling_twice_never_charges_twice(api, customer, make_booking):
    booking = make_booking()
    api.force_authenticate(customer)
    assert api.post(cancel_url(booking)).status_code == 200
    assert api.post(cancel_url(booking)).status_code == 409
    booking.refresh_from_db()
    assert booking.cancellation_fee == Decimal("375.00")


@pytest.mark.django_db
def test_someone_elses_booking_looks_like_it_does_not_exist(
    api, other_customer, make_booking
):
    booking = make_booking()
    api.force_authenticate(other_customer)
    assert api.post(cancel_url(booking)).status_code == 404
    booking.refresh_from_db()
    assert booking.status == Booking.Status.PENDING


@pytest.mark.django_db
def test_anonymous_cannot_cancel(api, make_booking):
    assert api.post(cancel_url(make_booking())).status_code == 401


@pytest.mark.django_db(transaction=True)
def test_simultaneous_cancellations_refund_only_once(customer, make_booking):
    booking = make_booking()

    def attempt():
        try:
            cancel_booking(booking_id=booking.id, actor=customer)
            return "cancelled"
        except BookingNotCancellable:
            return "rejected"

    results = run_together([attempt for _ in range(10)])
    assert results.count("cancelled") == 1
    assert results.count("rejected") == 9
    booking.refresh_from_db()
    assert booking.cancellation_fee == Decimal("375.00")

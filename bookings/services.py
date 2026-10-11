from decimal import ROUND_HALF_UP, Decimal

from django.db import IntegrityError, transaction
from django.utils import timezone

from fleet.models import Car

from .exceptions import BookingNotCancellable, CarNotAvailable
from .models import Booking

OVERLAP_CONSTRAINT = "booking_no_overlap_per_car"
CANCELLATION_FEE_RATE = Decimal("0.05")
CENT = Decimal("0.01")
CANCELLABLE_STATUSES = (Booking.Status.PENDING, Booking.Status.CONFIRMED)


def create_booking(*, user, car, start_date, end_date):
    """Create a booking: lock the car, insert, and let the database veto overlaps."""
    days = (end_date - start_date).days
    try:
        with transaction.atomic():
            # One request at a time per car. Competing requests queue here
            # instead of inserting overlapping rows at the same moment, which
            # can make PostgreSQL abort one of them with a deadlock.
            locked_car = Car.objects.select_for_update(no_key=True).get(pk=car.pk)
            if locked_car.status != Car.Status.AVAILABLE:
                raise CarNotAvailable
            return Booking.objects.create(
                user=user,
                car=locked_car,
                start_date=start_date,
                end_date=end_date,
                total_price=locked_car.daily_price * days,
            )
    except IntegrityError as exc:
        if OVERLAP_CONSTRAINT in str(exc):
            raise CarNotAvailable from exc
        raise


def cancel_booking(*, booking_id, actor):
    """Cancel once. Only an owner cancelling a paid booking pays the 5% fee."""
    with transaction.atomic():
        # Lock the row, so two simultaneous cancels cannot both refund.
        booking = Booking.objects.select_for_update().get(pk=booking_id)
        if booking.status not in CANCELLABLE_STATUSES:
            raise BookingNotCancellable(
                "Only pending or confirmed bookings can be cancelled."
            )
        if timezone.localdate() >= booking.start_date:
            raise BookingNotCancellable(
                "A booking can only be cancelled before its start date."
            )
        was_paid = booking.payment_status == Booking.PaymentStatus.PAID
        owner_cancels = booking.user_id == actor.id
        fee = Decimal("0.00")
        if was_paid and owner_cancels:
            fee = (booking.total_price * CANCELLATION_FEE_RATE).quantize(
                CENT, rounding=ROUND_HALF_UP
            )
        booking.status = Booking.Status.CANCELLED
        booking.cancelled_at = timezone.now()
        booking.cancellation_fee = fee
        if was_paid:
            booking.payment_status = Booking.PaymentStatus.REFUNDED
        booking.save(
            update_fields=[
                "status",
                "cancelled_at",
                "cancellation_fee",
                "payment_status",
            ]
        )
        return booking

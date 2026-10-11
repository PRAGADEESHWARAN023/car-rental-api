from django.db import IntegrityError, transaction

from fleet.models import Car

from .exceptions import CarNotAvailable
from .models import Booking

OVERLAP_CONSTRAINT = "booking_no_overlap_per_car"


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

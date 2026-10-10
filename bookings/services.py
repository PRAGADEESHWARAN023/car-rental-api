from django.db import IntegrityError, transaction

from .exceptions import CarNotAvailable
from .models import Booking

OVERLAP_CONSTRAINT = "booking_no_overlap_per_car"


def create_booking(*, user, car, start_date, end_date):
    """Create a booking. The database decides whether the dates are free."""
    days = (end_date - start_date).days
    total_price = car.daily_price * days
    try:
        with transaction.atomic():
            return Booking.objects.create(
                user=user,
                car=car,
                start_date=start_date,
                end_date=end_date,
                total_price=total_price,
            )
    except IntegrityError as exc:
        if OVERLAP_CONSTRAINT in str(exc):
            raise CarNotAvailable from exc
        raise

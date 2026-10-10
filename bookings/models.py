from django.conf import settings
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import (
    DateRangeField,
    RangeBoundary,
    RangeOperators,
)
from django.db import models
from django.db.models import F, Func, Q

BLOCKING_STATUSES = ["pending", "confirmed", "active"]


class DateRange(Func):
    function = "DATERANGE"
    output_field = DateRangeField()


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    class PaymentStatus(models.TextChoices):
        UNPAID = "unpaid", "Unpaid"
        PAID = "paid", "Paid"
        REFUNDED = "refunded", "Refunded"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="bookings",
    )
    car = models.ForeignKey(
        "fleet.Car", on_delete=models.PROTECT, related_name="bookings"
    )
    start_date = models.DateField()
    end_date = models.DateField()  # return day, not counted as rented
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.PENDING
    )
    payment_status = models.CharField(
        max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID
    )
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(end_date__gt=F("start_date")),
                name="booking_end_after_start",
            ),
            ExclusionConstraint(
                name="booking_no_overlap_per_car",
                expressions=[
                    (
                        DateRange("start_date", "end_date", RangeBoundary()),
                        RangeOperators.OVERLAPS,
                    ),
                    ("car", RangeOperators.EQUAL),
                ],
                condition=Q(status__in=BLOCKING_STATUSES),
            ),
        ]

        def __str__(self):
            return f"Booking {self.pk}: car {self.car_id}"

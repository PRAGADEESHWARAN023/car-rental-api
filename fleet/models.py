from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class Car(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        MAINTENANCE = "maintenance", "Maintenance"
        RETIRED = "retired", "Retired"

    registration_number = models.CharField(max_length=20, unique=True)
    make = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    daily_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.AVAILABLE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(daily_price__gt=0),
                name="car_daily_price_positive",
            ),
        ]

    def __str__(self):
        return f"{self.make} {self.model} ({self.registration_number})"

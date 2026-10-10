import pytest
from django.db import IntegrityError, transaction

from fleet.models import Car


def make_car(**overrides):
    data = {
        "registration_number": "TN01AB1234",
        "make": "Toyota",
        "model": "Innova",
        "daily_price": "2500.00",
    }
    data.update(overrides)
    return Car.objects.create(**data)


@pytest.mark.django_db
def test_car_defaults_to_available():
    assert make_car().status == Car.Status.AVAILABLE


@pytest.mark.django_db
def test_registration_number_must_be_unique():
    make_car()
    with pytest.raises(IntegrityError), transaction.atomic():
        make_car()


@pytest.mark.django_db
def test_database_rejects_zero_price():
    with pytest.raises(IntegrityError), transaction.atomic():
        make_car(registration_number="TN02CD5678", daily_price="0")

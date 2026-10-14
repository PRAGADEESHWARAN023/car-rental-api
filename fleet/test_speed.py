from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError

from fleet.models import Car

pytestmark = pytest.mark.django_db

User = get_user_model()


def seed(*args):
    out = StringIO()
    call_command("seed_demo", *args, stdout=out)
    return out.getvalue()


def test_seed_creates_demo_data_and_can_run_twice():
    seed("--force")
    seed("--force")
    assert Car.objects.count() == 4
    assert User.objects.count() == 2
    assert User.objects.get(email="staff@demo.example").role == User.Role.STAFF


def test_seed_refuses_to_run_with_debug_off_unless_forced():
    with pytest.raises(CommandError):
        seed()


def test_seed_prints_a_generated_password_that_really_works():
    output = seed("--force")
    password = output.split("password (shown once): ")[1].split()[0]
    assert User.objects.get(email="customer@demo.example").check_password(password)


def test_seed_uses_the_password_from_the_environment(monkeypatch):
    monkeypatch.setenv("SEED_DEMO_PASSWORD", "chosen-demo-pass-123")
    output = seed("--force")
    assert "shown once" not in output
    assert User.objects.get(email="staff@demo.example").check_password(
        "chosen-demo-pass-123"
    )

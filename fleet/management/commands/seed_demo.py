import os
import secrets

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from fleet.models import Car

User = get_user_model()

DEMO_USERS = [
    ("staff@demo.example", User.Role.STAFF),
    ("customer@demo.example", User.Role.CUSTOMER),
]
DEMO_CARS = [
    ("TN01DM0001", "Toyota", "Innova", "2500.00", Car.Status.AVAILABLE),
    ("TN01DM0002", "Maruti", "Swift", "1200.00", Car.Status.AVAILABLE),
    ("TN01DM0003", "Hyundai", "Creta", "2000.00", Car.Status.AVAILABLE),
    ("TN01DM0004", "Honda", "City", "1800.00", Car.Status.MAINTENANCE),
]


class Command(BaseCommand):
    help = "Create demo users and cars. Safe to run more than once."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force", action="store_true", help="Allow seeding while DEBUG is off."
        )

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["force"]:
            raise CommandError("DEBUG is off, so seeding is refused. Use --force.")
        env_password = os.environ.get("SEED_DEMO_PASSWORD")
        password = env_password or secrets.token_urlsafe(12)
        for email, role in DEMO_USERS:
            if User.objects.filter(email=email).exists():
                continue
            User.objects.create_user(email=email, password=password, role=role)
            self.stdout.write(f"Created {role} {email}")
            if not env_password:
                self.stdout.write(f"  password (shown once): {password}")
        for registration, make, model, price, status in DEMO_CARS:
            Car.objects.get_or_create(
                registration_number=registration,
                defaults={
                    "make": make,
                    "model": model,
                    "daily_price": price,
                    "status": status,
                },
            )
        self.stdout.write(self.style.SUCCESS("Demo data is ready."))

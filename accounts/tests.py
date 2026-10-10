import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_create_user_hashes_password_and_defaults_to_customer():
    user = User.objects.create_user(email="a@example.com", password="s3cret-pass")
    assert user.role == User.Role.CUSTOMER
    assert user.password != "s3cret-pass"
    assert user.check_password("s3cret-pass")


def test_create_user_requires_email():
    with pytest.raises(ValueError):
        User.objects.create_user(email="", password="x")


@pytest.mark.django_db
def test_create_superuser_gets_admin_role():
    admin = User.objects.create_superuser(email="b@example.com", password="s3cret-pass")
    assert admin.role == User.Role.ADMIN
    assert admin.is_staff and admin.is_superuser

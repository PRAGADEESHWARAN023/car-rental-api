import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def fast_password_hashing(settings):
    """Real hashers are slow on purpose; tests don't need that."""
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@pytest.fixture(autouse=True)
def clear_cache():
    """Rate-limit counters live in the cache; every test starts from zero."""
    cache.clear()
    yield
    cache.clear()

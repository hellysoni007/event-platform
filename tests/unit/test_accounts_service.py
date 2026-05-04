import pytest

from accounts.services import normalize_email


@pytest.mark.unit
def test_normalize_email():
    assert normalize_email("  Test@Example.COM ") == "test@example.com"

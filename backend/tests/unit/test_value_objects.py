from __future__ import annotations

import pytest

from app.domain.value_objects.email import Email
from app.domain.value_objects.phone import Phone


class TestEmail:
    def test_valid_email(self) -> None:
        email = Email("test@example.com")
        assert email.value == "test@example.com"

    def test_valid_email_with_plus(self) -> None:
        email = Email("test+label@example.com")
        assert email.value == "test+label@example.com"

    def test_valid_email_with_dots(self) -> None:
        email = Email("test.user@example.co.uk")
        assert email.value == "test.user@example.co.uk"

    def test_lowercase_normalization(self) -> None:
        email = Email("TEST@EXAMPLE.COM")
        assert email.value == "test@example.com"

    def test_strip_whitespace(self) -> None:
        email = Email("  test@example.com  ")
        assert email.value == "test@example.com"

    def test_invalid_email_no_at(self) -> None:
        with pytest.raises(ValueError, match="Invalid email"):
            Email("invalid-email")

    def test_invalid_email_no_domain(self) -> None:
        with pytest.raises(ValueError, match="Invalid email"):
            Email("user@.com")

    def test_invalid_email_empty(self) -> None:
        with pytest.raises(ValueError, match="Invalid email"):
            Email("")

    def test_invalid_email_spaces(self) -> None:
        with pytest.raises(ValueError, match="Invalid email"):
            Email("user @ example.com")

    def test_domain_property(self) -> None:
        email = Email("user@gmail.com")
        assert email.domain == "gmail.com"

    def test_local_part_property(self) -> None:
        email = Email("john.doe@company.com")
        assert email.local_part == "john.doe"

    def test_string_representation(self) -> None:
        email = Email("test@example.com")
        assert str(email) == "test@example.com"

    def test_equality_same_value(self) -> None:
        email1 = Email("test@example.com")
        email2 = Email("test@example.com")
        assert email1 == email2

    def test_equality_with_string(self) -> None:
        email = Email("test@example.com")
        assert email == "test@example.com"

    def test_hash(self) -> None:
        email1 = Email("test@example.com")
        email2 = Email("test@example.com")
        assert hash(email1) == hash(email2)

    def test_immutability(self) -> None:
        email = Email("test@example.com")
        with pytest.raises(AttributeError):
            email.value = "changed@example.com"


class TestPhone:
    def test_valid_phone(self) -> None:
        phone = Phone("+1234567890")
        assert phone.value == "+1234567890"

    def test_valid_us_phone(self) -> None:
        phone = Phone("+14155552671")
        assert phone.value == "+14155552671"

    def test_phone_strips_formatting(self) -> None:
        phone = Phone("(555) 123-4567")
        assert phone.value == "5551234567"

    def test_phone_with_spaces(self) -> None:
        phone = Phone("+1 555 123 4567")
        assert phone.value == "+15551234567"

    def test_phone_with_dashes(self) -> None:
        phone = Phone("555-123-4567")
        assert phone.value == "5551234567"

    def test_phone_with_dots(self) -> None:
        phone = Phone("555.123.4567")
        assert phone.value == "5551234567"

    def test_short_phone(self) -> None:
        with pytest.raises(ValueError, match="Invalid phone"):
            Phone("123")

    def test_very_long_phone(self) -> None:
        with pytest.raises(ValueError, match="Invalid phone"):
            Phone("+12345678901234567890")

    def test_phone_with_letters(self) -> None:
        with pytest.raises(ValueError, match="Invalid phone"):
            Phone("abc-def-ghij")

    def test_empty_phone(self) -> None:
        with pytest.raises(ValueError, match="Invalid phone"):
            Phone("")

    def test_country_code(self) -> None:
        phone = Phone("+14155552671", country_code="US")
        assert phone.country_code == "US"

    def test_string_representation(self) -> None:
        phone = Phone("5551234567")
        assert str(phone) == "5551234567"

    def test_equality_same_value(self) -> None:
        phone1 = Phone("+14155552671")
        phone2 = Phone("+14155552671")
        assert phone1 == phone2

    def test_equality_with_string(self) -> None:
        phone = Phone("555-123-4567")
        assert phone == "5551234567"

    def test_hash(self) -> None:
        phone1 = Phone("+14155552671")
        phone2 = Phone("+14155552671")
        assert hash(phone1) == hash(phone2)

    def test_immutability(self) -> None:
        phone = Phone("+1234567890")
        with pytest.raises(AttributeError):
            phone.value = "+0987654321"

import re

from pydantic import BaseModel, Field, field_validator

PHONE_PATTERN = re.compile(r"^233\d{9}$")


def normalize_phone(raw: str) -> str:
    """Accepts 0244123456 or 233244123456 and returns the 233 format."""
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 10 and digits.startswith("0"):
        digits = "233" + digits[1:]
    if not PHONE_PATTERN.match(digits):
        raise ValueError("Enter a valid Ghana phone number, e.g. 0244123456")
    return digits


class _PhoneModel(BaseModel):
    phone: str

    @field_validator("phone")
    @classmethod
    def _normalize_phone(cls, value: str) -> str:
        return normalize_phone(value)


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RegisterIn(_PhoneModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: str | None = None
    password: str = Field(min_length=8, max_length=128)
    accept_terms: bool = Field(default=False, strict=True, validate_default=True)

    @field_validator("accept_terms")
    @classmethod
    def _must_accept(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("You must accept the Terms and Privacy Policy to register")
        return value

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        value = value.strip().lower()
        if len(value) > 255 or not EMAIL_PATTERN.match(value):
            raise ValueError("Enter a valid email address")
        return value


class VerifyIn(_PhoneModel):
    code: str = Field(pattern=r"^\d{6}$")


class PhoneIn(_PhoneModel):
    pass


class ResetIn(_PhoneModel):
    code: str = Field(pattern=r"^\d{6}$")
    new_password: str = Field(min_length=8, max_length=128)


class LoginIn(_PhoneModel):
    password: str = Field(min_length=1, max_length=128)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

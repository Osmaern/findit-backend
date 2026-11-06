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


class RegisterIn(_PhoneModel):
    full_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8, max_length=128)


class VerifyIn(_PhoneModel):
    code: str = Field(pattern=r"^\d{6}$")


class PhoneIn(_PhoneModel):
    pass


class LoginIn(_PhoneModel):
    password: str = Field(min_length=1, max_length=128)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

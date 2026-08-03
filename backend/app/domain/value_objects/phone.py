from __future__ import annotations

import re
from dataclasses import dataclass

_PHONE_PATTERN = re.compile(r"^\+?1?\d{9,15}$")


@dataclass(frozen=True)
class Phone:
    value: str
    country_code: str = ""

    def __init__(self, value: str, country_code: str = "") -> None:
        cleaned = re.sub(r"[\s\-\(\)\.]", "", value)
        if not _PHONE_PATTERN.match(cleaned):
            raise ValueError(f"Invalid phone number: {value}")
        object.__setattr__(self, "value", cleaned)
        object.__setattr__(self, "country_code", country_code)

    @property
    def is_mobile(self) -> bool:
        return len(self.value) >= 10 and self.value.startswith(("6", "7", "8", "9"))

    @property
    def formatted(self) -> str:
        if len(self.value) == 10:
            return f"({self.value[:3]}) {self.value[3:6]}-{self.value[6:]}"
        return self.value

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Phone):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == re.sub(r"[\s\-\(\)\.]", "", other)
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.value)

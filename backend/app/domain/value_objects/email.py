from __future__ import annotations

import re
from dataclasses import dataclass

_EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


@dataclass(frozen=True)
class Email:
    value: str

    def __init__(self, value: str) -> None:
        stripped = value.strip().lower()
        if not _EMAIL_PATTERN.match(stripped):
            raise ValueError(f"Invalid email address: {value}")
        object.__setattr__(self, "value", stripped)

    @property
    def domain(self) -> str:
        return self.value.split("@")[1]

    @property
    def local_part(self) -> str:
        return self.value.split("@")[0]

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Email):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other.strip().lower()
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.value)

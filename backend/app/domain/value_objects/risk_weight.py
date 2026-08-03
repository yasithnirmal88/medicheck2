from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskWeight:
    value: float
    label: str
    severity: str

    @property
    def is_positive(self) -> bool:
        return self.value > 0

    @property
    def is_negative(self) -> bool:
        return self.value < 0

    @property
    def is_neutral(self) -> bool:
        return self.value == 0

    def __post_init__(self) -> None:
        if self.severity not in ("none", "mild", "moderate", "severe", "critical"):
            object.__setattr__(self, "severity", "none")

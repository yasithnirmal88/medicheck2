from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BodySystemModule(ABC):
    code: str = ""
    name: str = ""
    description: str = ""
    icon: str = ""
    color: str = ""
    is_active: bool = True
    version: str = "1.0.0"

    @abstractmethod
    def get_questions(self) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    def get_risk_rules(self) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    def get_risk_indicators(self) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    def get_conditions(self) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    def get_recommendations(self) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    def get_lab_tests(self) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    def get_default_scoring_weights(self) -> dict[str, float]:
        pass

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.domain.entities.question import Question, QuestionType


def _to_int(value: Any) -> int | None:
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


class ValidationEngine:
    async def validate(
        self, question: Question, response_value: dict[str, Any]
    ) -> list[str]:
        errors: list[str] = []

        # Required check
        if question.is_required and self._is_empty(response_value):
            errors.append(f"Question '{question.code}' is required")

        if self._is_empty(response_value):
            return errors

        validation_rules = question.validation_rules or {}
        qtype = question.question_type

        # Type-specific validation
        if qtype == QuestionType.NUMERIC:
            errors.extend(self._validate_numeric(response_value, validation_rules))
        elif qtype == QuestionType.DECIMAL:
            errors.extend(self._validate_decimal(response_value, validation_rules))
        elif qtype == QuestionType.SLIDER:
            errors.extend(self._validate_slider(response_value, validation_rules))
        elif qtype == QuestionType.DATE:
            errors.extend(self._validate_date(response_value))
        elif qtype == QuestionType.TIME:
            errors.extend(self._validate_time(response_value))
        elif qtype == QuestionType.SINGLE_CHOICE:
            errors.extend(
                self._validate_single_choice(response_value, validation_rules)
            )
        elif qtype in (QuestionType.MULTIPLE_CHOICE, QuestionType.MULTI_SELECT):
            errors.extend(
                self._validate_multiple_choice(response_value, validation_rules)
            )
        elif qtype == QuestionType.FREE_TEXT:
            errors.extend(self._validate_text(response_value, validation_rules))
        elif qtype == QuestionType.FILE_UPLOAD:
            errors.extend(self._validate_file(response_value, validation_rules))

        # Min/Max length
        if "min_length" in validation_rules or "max_length" in validation_rules:
            val = response_value.get("value", "")
            if isinstance(val, str):
                min_len = validation_rules.get("min_length")
                max_len = validation_rules.get("max_length")
                if min_len is not None and len(val) < min_len:
                    errors.append(f"Minimum length is {min_len}")
                if max_len is not None and len(val) > max_len:
                    errors.append(f"Maximum length is {max_len}")

        # Regex validation
        pattern = validation_rules.get("pattern")
        if pattern and isinstance(response_value.get("value"), str):
            import re

            if not re.match(pattern, response_value["value"]):
                errors.append("Value does not match required pattern")

        return errors

    def _is_empty(self, value: dict[str, Any]) -> bool:
        if not value:
            return True
        v = value.get("value")
        if v is None:
            return True
        if isinstance(v, str) and v.strip() == "":
            return True
        if isinstance(v, list):
            return len(v) == 0
        return False

    def _validate_numeric(
        self, value: dict[str, Any], rules: dict[str, Any]
    ) -> list[str]:
        errors = []
        num = _to_int(value.get("value"))
        if num is None:
            errors.append("Value must be a valid integer")
            return errors
        min_v = rules.get("min")
        max_v = rules.get("max")
        if min_v is not None and num < min_v:
            errors.append(f"Value must be at least {min_v}")
        if max_v is not None and num > max_v:
            errors.append(f"Value must be at most {max_v}")
        return errors

    def _validate_decimal(
        self, value: dict[str, Any], rules: dict[str, Any]
    ) -> list[str]:
        errors = []
        v = value.get("value")
        num = _to_float(v)
        if num is None:
            errors.append("Value must be a valid decimal number")
            return errors
        min_v = rules.get("min")
        max_v = rules.get("max")
        decimal_places = rules.get("decimal_places")
        if min_v is not None and num < min_v:
            errors.append(f"Value must be at least {min_v}")
        if max_v is not None and num > max_v:
            errors.append(f"Value must be at most {max_v}")
        if decimal_places is not None and len(str(v).split(".")[-1]) > decimal_places:
            errors.append(f"Maximum {decimal_places} decimal places allowed")
        return errors

    def _validate_slider(
        self, value: dict[str, Any], rules: dict[str, Any]
    ) -> list[str]:
        errors = []
        num = _to_float(value.get("value"))
        if num is None:
            errors.append("Value must be a valid number")
            return errors
        min_v = rules.get("min", 0)
        max_v = rules.get("max", 100)
        if num < min_v or num > max_v:
            errors.append(f"Value must be between {min_v} and {max_v}")
        return errors

    def _validate_date(self, value: dict[str, Any]) -> list[str]:
        errors = []
        v = value.get("value")
        if isinstance(v, str):
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                errors.append("Date must be in YYYY-MM-DD format")
        return errors

    def _validate_time(self, value: dict[str, Any]) -> list[str]:
        errors = []
        v = value.get("value")
        if isinstance(v, str):
            try:
                datetime.strptime(v, "%H:%M")
            except ValueError:
                errors.append("Time must be in HH:MM format")
        return errors

    def _validate_single_choice(
        self, value: dict[str, Any], rules: dict[str, Any]
    ) -> list[str]:
        errors = []
        allowed = rules.get("allowed_values", [])
        v = value.get("value")
        if allowed and v not in allowed:
            errors.append("Value must be one of the allowed options")
        return errors

    def _validate_multiple_choice(
        self, value: dict[str, Any], rules: dict[str, Any]
    ) -> list[str]:
        errors = []
        v = value.get("value", [])
        if not isinstance(v, list):
            errors.append("Value must be a list")
            return errors
        allowed = rules.get("allowed_values", [])
        if allowed:
            for item in v:
                if item not in allowed:
                    errors.append(f"'{item}' is not an allowed value")
        min_select = rules.get("min_selections")
        max_select = rules.get("max_selections")
        if min_select is not None and len(v) < min_select:
            errors.append(f"Select at least {min_select} options")
        if max_select is not None and len(v) > max_select:
            errors.append(f"Select at most {max_select} options")
        return errors

    def _validate_text(
        self, value: dict[str, Any], _rules: dict[str, Any] | None = None
    ) -> list[str]:
        errors = []
        v = value.get("value", "")
        if not isinstance(v, str):
            errors.append("Value must be text")
        return errors

    def _validate_file(self, value: dict[str, Any], rules: dict[str, Any]) -> list[str]:
        errors = []
        allowed_types = rules.get("allowed_types", [])
        max_size_mb = rules.get("max_size_mb", 10)
        v = value.get("value", {})
        if allowed_types and v.get("mime_type") not in allowed_types:
            errors.append(f"File type must be one of: {', '.join(allowed_types)}")
        if v.get("size_mb") and v["size_mb"] > max_size_mb:
            errors.append(f"File size must be less than {max_size_mb}MB")
        return errors

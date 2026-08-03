from __future__ import annotations

from datetime import date, datetime
from typing import Any


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


class DependencyEvaluator:
    @staticmethod
    def evaluate(
        condition_type: str,
        condition_value: dict[str, Any],
        answer_value: Any,
        user_attributes: dict[str, Any] | None = None,
    ) -> bool:
        if answer_value is None:
            return False

        expected = condition_value.get("value")
        expected_min = condition_value.get("min")
        expected_max = condition_value.get("max")
        expected_set = condition_value.get("values", [])

        if condition_type == "equals":
            return str(answer_value) == str(expected)

        if condition_type == "not_equals":
            return str(answer_value) != str(expected)

        if condition_type == "in":
            values = expected_set if expected_set else [expected]
            return str(answer_value) in [str(v) for v in values]

        if condition_type == "not_in":
            values = expected_set if expected_set else [expected]
            return str(answer_value) not in [str(v) for v in values]

        if condition_type in ("greater_than", "gt") and expected is not None:
            return _to_float(answer_value) > _to_float(expected)

        if condition_type in ("less_than", "lt") and expected is not None:
            return _to_float(answer_value) < _to_float(expected)

        if condition_type in ("gte", "greater_than_or_equal") and expected is not None:
            return _to_float(answer_value) >= _to_float(expected)

        if condition_type in ("lte", "less_than_or_equal") and expected is not None:
            return _to_float(answer_value) <= _to_float(expected)

        if condition_type == "range" and expected_min is not None and expected_max is not None:
            val = _to_float(answer_value)
            return val >= _to_float(expected_min) and val <= _to_float(expected_max)

        if condition_type == "has_any":
            if isinstance(answer_value, list):
                return any(
                    str(v) in [str(x) for x in expected_set] for v in answer_value
                )
            return False

        if condition_type == "has_all":
            if isinstance(answer_value, list):
                return all(
                    str(v) in [str(x) for x in answer_value] for v in expected_set
                )
            return False

        if condition_type == "is_empty":
            return answer_value is None or answer_value == "" or answer_value == []

        if condition_type == "is_not_empty":
            return (
                answer_value is not None and answer_value != "" and answer_value != []
            )

        if condition_type == "computed":
            return DependencyEvaluator._evaluate_computed(
                condition_value, answer_value, user_attributes
            )

        return False

    @staticmethod
    def _evaluate_computed(
        condition_value: dict[str, Any],
        answer_value: Any,
        user_attributes: dict[str, Any] | None = None,
    ) -> bool:
        field = condition_value.get("field", "")
        operator = condition_value.get("operator", "eq")
        threshold = condition_value.get("threshold")

        if field == "bmi" and user_attributes:
            weight = (
                answer_value
                if condition_value.get("use_answer")
                else user_attributes.get("weight")
            )
            height = user_attributes.get("height")
            if weight and height:
                bmi = float(weight) / (float(height) / 100) ** 2
                return DependencyEvaluator._compare(bmi, operator, threshold)

        if field == "age" and user_attributes:
            dob = user_attributes.get("date_of_birth")
            if dob:
                if isinstance(dob, str):
                    dob = datetime.fromisoformat(dob).date()
                age = DependencyEvaluator._calculate_age(dob)
                return DependencyEvaluator._compare(age, operator, threshold)

        return False

    @staticmethod
    def _compare(value: float, operator: str, threshold: Any) -> bool:
        try:
            t = float(threshold)
            if operator in ("eq", "=="):
                return value == t
            if operator in ("gt", ">"):
                return value > t
            if operator in ("gte", ">="):
                return value >= t
            if operator in ("lt", "<"):
                return value < t
            if operator in ("lte", "<="):
                return value <= t
            if operator == "range":
                return value >= min(t, float(threshold)) and value <= max(
                    t, float(threshold)
                )
            return False
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _calculate_age(dob: date) -> int:
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

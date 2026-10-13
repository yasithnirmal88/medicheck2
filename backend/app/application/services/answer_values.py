from __future__ import annotations

from collections.abc import Sequence
from typing import Any

_AFFIRMATIVE_STRINGS = {"yes", "true", "t", "y", "1"}


def coerce_float(value: Any) -> float | None:
    """Best-effort numeric coercion for persistence + activation checks.

    ``bool`` is handled explicitly (before the ``int`` branch) so that
    ``True``/``False`` map to ``1.0``/``0.0`` rather than being treated as
    arbitrary integers.
    """
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            return None
    return None


def match_option(options: Sequence[Any], raw: Any) -> Any | None:
    """Return the option matching ``raw`` (by ``value`` or ``code``), else None.

    YES/NO questions arrive from the UI as booleans (``True``/``False``) while
    seeded options use the canonical ``"yes"``/``"no"`` values, so booleans get
    an extra canonical mapping. Matching is textual to stay type-tolerant.
    """
    if raw is None:
        return None
    text = str(raw)
    for option in options:
        if str(getattr(option, "value", None)) == text or str(
            getattr(option, "code", None)
        ) == text:
            return option
    if isinstance(raw, bool):
        target = "yes" if raw else "no"
        for option in options:
            opt_value = str(getattr(option, "value", "") or "").lower()
            opt_code = str(getattr(option, "code", "") or "").lower()
            if opt_value == target or opt_code == target:
                return option
    return None


def is_affirmative(
    *,
    score_value: Any = None,
    numeric_value: Any = None,
    value: Any = None,
    response_value: Any = None,
) -> bool:
    """Whether a stored answer represents a positive/affirmative finding.

    Question-level indicator links must only activate on affirmative answers
    (e.g. "yes" for a YES/NO question); negative or empty answers ("no",
    ``False``, ``0``, ``""``) must never activate the linked indicator.
    """
    score_num = coerce_float(score_value)
    if score_num is not None and score_num > 0:
        return True

    numeric_num = coerce_float(numeric_value)
    if numeric_num is not None:
        return numeric_num > 0

    if value is None and isinstance(response_value, dict):
        value = response_value.get("value")

    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return float(value) > 0
    if isinstance(value, str):
        text = value.strip().lower()
        if text in _AFFIRMATIVE_STRINGS:
            return True
        try:
            return float(text) > 0
        except ValueError:
            return False
    return False

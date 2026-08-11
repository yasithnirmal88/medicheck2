"""Phase 5 — Multilingual intake language support.

The language layer is an INTERFACE layer only. Sinhala/Tamil/English all
resolve to the SAME canonical MediCheck indicator IDs — the clinical knowledge
graph is never fragmented by language. A localized phrase and an English phrase
that describe the same clinical concept map to one indicator_id.

This module provides:
- the bounded set of supported intake languages (en/si/ta);
- normalization (accepts aliases like "en-US", "sin", "tam" → canonical codes);
- deterministic script-based language detection (Sinhala U+0D80–0DFF,
  Tamil U+0B80–0BFF) with a safe fallback to the selected/default language.

Automatic detection is best-effort: when uncertain, the system falls back to
the user-selected or default language rather than silently inventing one.
"""

from __future__ import annotations

from dataclasses import dataclass

# Bounded vocabulary for Phase 5. Additional languages can be added here later
# without touching the intake pipeline (they flow through the same abstraction).
LANGUAGE_EN = "en"
LANGUAGE_SI = "si"
LANGUAGE_TA = "ta"
DEFAULT_INTAKE_LANGUAGE = LANGUAGE_EN

SUPPORTED_INTAKE_LANGUAGES: tuple[str, ...] = (LANGUAGE_EN, LANGUAGE_SI, LANGUAGE_TA)

# Human-readable labels for UI selectors (kept here so backend + docs agree).
LANGUAGE_LABELS: dict[str, str] = {
    LANGUAGE_EN: "English",
    LANGUAGE_SI: "Sinhala",
    LANGUAGE_TA: "Tamil",
}

# Accepted aliases → canonical code. Lets the API accept common variants
# ("en-US", "sin", "tam", "si-LK"...) without coupling to a locale library.
_LANGUAGE_ALIASES: dict[str, str] = {
    "en": LANGUAGE_EN, "eng": LANGUAGE_EN, "en-us": LANGUAGE_EN, "en-gb": LANGUAGE_EN,
    "si": LANGUAGE_SI, "sin": LANGUAGE_SI, "si-lk": LANGUAGE_SI, "sinh": LANGUAGE_SI, "sinhala": LANGUAGE_SI,
    "ta": LANGUAGE_TA, "tam": LANGUAGE_TA, "ta-lk": LANGUAGE_TA, "tam": LANGUAGE_TA, "tamil": LANGUAGE_TA,
}

# Unicode script ranges for deterministic detection.
_SINHALA_RANGE = (0x0D80, 0x0DFF)
_TAMIL_RANGE = (0x0B80, 0x0BFF)


@dataclass(frozen=True)
class LanguageDetectionResult:
    """Outcome of language detection.

    ``detected`` is the script-detected language when confident, else None.
    ``resolved`` is the final language to use (detected if confident, else the
    selected/default). ``was_detected`` indicates automatic detection was used.
    """
    detected: str | None
    resolved: str
    was_detected: bool


def normalize_language(value: str | None) -> str:
    """Normalize a language string to a canonical supported code.

    Returns the default language for None/empty/unsupported values so callers
    never receive an invalid language code. Use ``is_supported_language`` to
    distinguish "explicitly unsupported" from "defaulted".
    """
    if not value:
        return DEFAULT_INTAKE_LANGUAGE
    key = value.strip().lower()
    if key in _LANGUAGE_ALIASES:
        return _LANGUAGE_ALIASES[key]
    return DEFAULT_INTAKE_LANGUAGE


def is_supported_language(value: str | None) -> bool:
    """True when ``value`` normalizes to a genuinely supported language."""
    if not value:
        return False
    key = value.strip().lower()
    return key in _LANGUAGE_ALIASES


def detect_language(text: str) -> str | None:
    """Deterministic script-based detection. Returns None when uncertain.

    Detection is by Unicode script proportion: if a non-Latin supported script
    appears meaningfully in the text, that language is returned. English is
    never "detected" (it is the default fallback) so we never override an
    explicit user selection with a low-signal guess.
    """
    if not text:
        return None
    sinhal = 0
    tamil = 0
    total = 0
    for ch in text:
        cp = ord(ch)
        if ch.isspace() or ch in ".,;:!?-_/()[]{}\"'":
            continue
        total += 1
        if _SINHALA_RANGE[0] <= cp <= _SINHALA_RANGE[1]:
            sinhal += 1
        elif _TAMIL_RANGE[0] <= cp <= _TAMIL_RANGE[1]:
            tamil += 1
    if total == 0:
        return None
    # Require a meaningful proportion to avoid false detection on stray chars.
    if sinhal / total >= 0.25:
        return LANGUAGE_SI
    if tamil / total >= 0.25:
        return LANGUAGE_TA
    return None


def resolve_language(text: str, selected: str | None = None) -> LanguageDetectionResult:
    """Resolve the final intake language.

    Preference: confident automatic detection → user-selected → default.
    Detection never silently overrides a confident script signal, but an
    uncertain detection falls back to the selected/default language.
    """
    detected = detect_language(text)
    if detected is not None:
        return LanguageDetectionResult(detected=detected, resolved=detected, was_detected=True)
    resolved = normalize_language(selected)
    return LanguageDetectionResult(detected=None, resolved=resolved, was_detected=False)

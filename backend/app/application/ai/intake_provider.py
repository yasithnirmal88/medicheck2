"""AI clinical-intake provider abstraction (Phase 3).

Mirrors the Phase 1/2 provider pattern: the application service depends on the
``AIClinicalIntakeProvider`` Protocol, not on any concrete vendor SDK. The
default development provider is deterministic (no network, no external API
key) so tests run without credentials.

A real vendor provider can be added later by implementing the Protocol and
selecting it via ``settings.ai_provider`` — no change to the service layer is
required. Phase 3 ships only the stub provider; no third-party AI packages are
installed.

The stub performs deterministic, rule-based extraction:
- keyword/phrase matching against the supplied indicator catalog,
- negation detection (polarity="negative"),
- uncertainty detection (certainty="uncertain", lower confidence),
- temporality detection ("used to" → historical, "sometimes" → recurring),
- candidate mapping to existing indicator IDs ONLY (no invented IDs),
- informational clarification generation on ambiguity.

It never diagnoses, scores, sets severity, or activates indicators.
"""

from __future__ import annotations

import re
from typing import Any, Protocol, runtime_checkable

from app.application.dtos.intake_dtos import IntakeRequestContext
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

#: Negation cues. If one precedes the matched concept within a small window,
#: the observation polarity is "negative" and the candidate is dropped.
#: Phase 5 — multilingual cues (English/Sinhala/Tamil).
_NEGATION_CUES = (
    "no ", "not ", "don't", "dont", "doesn't", "doesnt", "didn't", "didnt",
    "haven't", "havent", "never", "without", "denies", "deny", "absent",
    "free of", "no longer", "stopped",
    # Sinhala
    "නෑ", "නැහැ", "නොමැත", "නැති", "නැත", "නොවේ", "කිසිවක්",
    # Tamil
    "இல்லை", "இல்ல", "கிடையாது", "இல்லையென",
)

#: Uncertainty cues → certainty="uncertain", confidence reduced.
#: Phase 5 — multilingual cues.
_UNCERTAINTY_CUES = (
    "maybe", "might", "perhaps", "i think", "sometimes feel", "not sure",
    "wondering", "wonder if", "could be", "seems like", "i guess",
    "possibly", "unclear", "not certain",
    # Sinhala
    "වගේ", "යම්", "බොහොම", "දැඩි", "හිතනවා", "දන්නෙ නෑ",
    # Tamil
    "தான்", "என்று", "நினைக்கிறேன்", "தெரியவில்லை",
)

#: Temporality cues. Phase 5 — multilingual.
_HISTORICAL_CUES = (
    "used to", "previously", "in the past", "before", "had a history of",
    "history of", "formerly", "ago",
    # Sinhala
    "කලින්", "බලන්න", "පෙර", "අතීතයේ",
    # Tamil
    "முன்பு", "முன்னதாக", "கடந்த",
)
_RECENT_CUES = (
    "recently", "lately", "past few", "last week", "last month", "this week",
    # Sinhala
    "මෑතක", "මීට", "මේ", "පසුගිය",
    # Tamil
    "சமீபமாக", "இப்போது",
)
_RECURRING_CUES = (
    "sometimes", "occasionally", "every now and then", "on and off",
    "from time to time", "intermittent", "now and then",
    # Sinhala
    "සමහරවිට", "කිට්ටුවට", "ක්ෂණික",
    # Tamil
    "சில நேரம்", "இடைக்கிடை",
)

#: Patient-language synonyms for common indicator-name keywords. Lets the
#: deterministic stub map everyday wording (e.g. "tired") to indicator names
#: (e.g. "Exertional Fatigue") without an external NLP dependency. This is a
#: bounded map, not a clinical knowledge base.
#:
#: Phase 5 — multilingual synonyms. Sinhala/Tamil phrases map to the SAME
#: canonical keyword (and thus the SAME indicator). The language layer is an
#: interface layer: localized input never fragments the clinical graph.
_SYNONYMS: dict[str, tuple[str, ...]] = {
    "fatigue": (
        "tired", "tiredness", "exhausted", "exhaustion", "no energy", "low energy", "weariness",
        # Sinhala
        "මහන්සියි", "මහන්සි", "වෙහෙස", "වෙහෙසට පත්", "උණුසුම් දැනෙනවා",
        # Tamil
        "சோர்வு", "களைப்பு", "அயர்ச்சி",
    ),
    "exertional": (
        "exertion", "exerting", "climbing stairs", "walking upstairs", "stairs", "on exertion", "during exercise", "activity",
        # Sinhala
        "පඩි", "පඩි නගිද්දී", "පඩි නැග්ගාම", "ව්යායාම",
        # Tamil
        "படிகள்", "படியேற", "உடற்பயிற்சி",
    ),
    "dyspnea": (
        "short of breath", "shortness of breath", "breathless", "breathlessness", "can't breathe", "cannot breathe",
        # Sinhala
        "හුස්ම ගන්න අමාරුයි", "හුස්ම", "හුස්ම ගන්න", "පණුවෙනවා",
        # Tamil
        "மூச்சு", "மூச்சு வாங்க", "மூச்சுத் திணறல்",
    ),
    "dizziness": (
        "dizzy", "lightheaded", "light-headed", "faint", "fainting", "vertigo",
        # Sinhala
        "ඔලුව කැරකෙනවා", "කැරකෙනවා", "මුලාවෙනවා",
        # Tamil
        "தலைச்சுற்றல்", "தலை கறங்க",
    ),
    "syncope": ("fainted", "fainting", "passed out", "blackout"),
    "edema": ("swelling", "swollen", "puffy", "fluid retention"),
    "palpitations": ("palpitation", "racing heart", "pounding heart", "irregular heartbeat", "fluttering heart"),
    "chest": ("chest pain", "chest discomfort", "chest pressure", "chest tightness"),
    "angina": ("chest pain", "chest discomfort", "chest pressure"),
    "hypertension": ("high blood pressure", "blood pressure"),
    "nocturia": ("frequent urination", "waking to urinate", "peeing at night", "urinating at night"),
    "proteinuria": ("foamy urine", "bubbly urine", "frothy urine"),
    "hematuria": ("blood in urine", "red urine", "pink urine", "bloody urine"),
    "pruritus": ("itching", "itchy", "scratch"),
    "diabetes": ("high blood sugar", "sugar problem"),
}

#: Build a reverse lookup: patient-term → canonical keyword present in indicator
#: names. Used to expand keyword matching for the stub.
_PATIENT_TERM_TO_KEYWORD: dict[str, str] = {}
for _kw, _terms in _SYNONYMS.items():
    for _t in _terms:
        _PATIENT_TERM_TO_KEYWORD[_t] = _kw

_DURATION_RE = re.compile(
    r"\bfor\s+(?P<d>(?:a\s+|an\s+)?(?:few|several|couple of|one|two|three|four|five|six|seven|eight|nine|ten|"
    r"\d+)\s+)?(?P<u>days?|weeks?|months?|years?)\b",
    re.IGNORECASE,
)
_FREQUENCY_RE = re.compile(
    r"\b(?P<f>daily|weekly|monthly|every\s+(?:day|night|morning|evening))\b",
    re.IGNORECASE,
)


@runtime_checkable
class AIClinicalIntakeProvider(Protocol):
    """Extracts structured observations + candidate indicators from intake text.

    Implementations MUST:
    - return a JSON string parseable by ``parse_provider_json``;
    - only cite ``indicator_id`` values present in ``context.catalog``;
    - never diagnose, score, set severity, or invent indicators;
    - raise ``AIIntakeProviderError`` on any failure so the service falls back.

    The returned string is parsed + validated by the service; raw output is
    never trusted.
    """

    async def extract_candidates(self, context: IntakeRequestContext) -> str: ...


class AIIntakeProviderError(RuntimeError):
    """Raised when an intake provider cannot produce a usable response.

    Lets the service map any provider failure to a single safe fallback — the
    intake is never broken and the standard questionnaire still works.
    """


class StubClinicalIntakeProvider:
    """Deterministic local provider — the default.

    Uses the supplied indicator catalog (already bounded) and the patient
    message. No network calls, no invented indicators, no diagnoses.
    """

    name = "stub"

    async def extract_candidates(self, context: IntakeRequestContext) -> str:
        try:
            return _stub_extract(context)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("stub intake provider failed: %s", exc)
            raise AIIntakeProviderError("stub intake provider failure") from exc


def _stub_extract(context: IntakeRequestContext) -> str:
    import json

    text = context.patient_message.lower()
    observations: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    clarifications: list[dict[str, Any]] = []

    matched_indicator_ids: set[str] = set()

    for entry in context.catalog.entries:
        phrase = entry.name.lower()
        # Build a set of representative keywords from the indicator name.
        keywords = [w for w in re.split(r"[/_\-\s]+", phrase) if len(w) >= 4]
        if not keywords:
            continue
        # Match if any significant keyword appears in the text, directly or via
        # the bounded patient-language synonym map.
        hit_kw = None
        hit_term = None
        for kw in keywords:
            if kw in text:
                hit_kw = kw
                hit_term = kw
                break
            for pterm, canonical in _PATIENT_TERM_TO_KEYWORD.items():
                if canonical == kw and pterm in text:
                    hit_kw = kw
                    hit_term = pterm
                    break
            if hit_kw:
                break
        if hit_kw is None:
            continue

        # Locate a concept span: prefer the keyword's surrounding clause.
        span = _span_around(text, hit_term or hit_kw)
        polarity = _polarity(text, hit_term or hit_kw)
        certainty, conf_mod = _certainty(text)
        temporality = _temporality(text)

        # Concept label derived from the indicator name (human-readable).
        concept = entry.name
        obs_conf = max(0.0, min(1.0, 0.6 + conf_mod))

        obs = {
            "source_text": span,
            "normalized_concept": concept,
            "observation_type": "symptom",
            "certainty": certainty,
            "temporality": temporality,
            "polarity": polarity,
            "severity_description": None,
            "duration": _duration(text),
            "frequency": _frequency(text),
            "context": None,
            "body_system": entry.body_system_id,
            "confidence": round(obs_conf, 2),
        }
        observations.append(obs)

        # Negative observations do not produce positive candidate indicators.
        if polarity == "positive":
            cand_conf = max(0.0, min(1.0, 0.55 + conf_mod))
            candidates.append(
                {
                    "indicator_id": entry.indicator_id,
                    "confidence": round(cand_conf, 2),
                    "observation_ids": [obs["source_text"]],
                    "reason": (
                        f"The reported description may correspond to the "
                        f"clinical indicator \u201c{entry.name}\u201d."
                    ),
                    "uncertainty": None if certainty != "uncertain" else "patient expressed uncertainty",
                    "source": "ai_extraction",
                }
            )
            matched_indicator_ids.add(entry.indicator_id)

    # If the text mentions something ambiguous and we matched at least one
    # indicator, add an informational clarification (non-diagnostic).
    # Phase 5: localized to the patient's language when possible.
    if observations and not candidates:
        clarifications.append(
            {
                "text": _localized_clarification(context.language),
                "source": "ai_generated",
                "observation_id": observations[0]["source_text"],
                "linked_indicator_id": None,
                "linked_question_id": None,
            }
        )

    payload = {
        "observations": observations,
        "candidates": candidates,
        "clarifications": clarifications,
    }
    return json.dumps(payload)


def _span_around(text: str, keyword: str, window: int = 12) -> str:
    """Return a short verbatim span around the first occurrence of keyword."""
    idx = text.find(keyword)
    if idx < 0:
        return keyword
    words = text.split()
    # Re-derive word index approximately via character split.
    start = max(0, idx - window)
    end = min(len(text), idx + len(keyword) + window)
    return text[start:end].strip()


def _polarity(text: str, keyword: str) -> str:
    """Detect negation near the matched keyword."""
    idx = text.find(keyword)
    if idx < 0:
        return "positive"
    prefix = text[max(0, idx - 40) : idx]
    for cue in _NEGATION_CUES:
        if cue in prefix or cue in text[idx : idx + 30]:
            return "negative"
    return "positive"


def _certainty(text: str) -> tuple[str, float]:
    for cue in _UNCERTAINTY_CUES:
        if cue in text:
            return "uncertain", -0.15
    return "reported", 0.0


def _temporality(text: str) -> str:
    for cue in _HISTORICAL_CUES:
        if cue in text:
            return "historical"
    for cue in _RECURRING_CUES:
        if cue in text:
            return "recurring"
    for cue in _RECENT_CUES:
        if cue in text:
            return "recent"
    return "current"


def _duration(text: str) -> str | None:
    m = _DURATION_RE.search(text)
    if not m:
        return None
    d = (m.group("d") or "").strip()
    unit = m.group("u")
    if d:
        return f"{d}{unit}".replace("  ", " ").strip()
    return unit


def _frequency(text: str) -> str | None:
    m = _FREQUENCY_RE.search(text)
    return m.group("f") if m else None


def _localized_clarification(language: str) -> str:
    """Informational clarification in the patient's language (non-diagnostic).

    Always informational: asks when/how-long/how-often. Never suggests an
    answer, never diagnoses. Falls back to English.
    """
    if language == "si":
        return "මේ කවදාද වෙන්නේ කියලා සහ කොච්චර කාලයක් තියෙනවද කියලා විස්තර කරන්න පුළුවන්ද?"
    if language == "ta":
        return "இது எப்போது நிகழ்கிறது மற்றும் எவ்வளவு காலமாக உள்ளது என விளக்கலாமா?"
    return "Can you describe when this happens and how long it has been going on?"


def get_intake_provider() -> AIClinicalIntakeProvider:
    """Return the configured AI intake provider.

    Defaults to the deterministic stub provider. A real vendor provider can be
    selected by setting ``AI_PROVIDER`` and implementing the Protocol here.
    """
    name = (settings.ai_provider or "stub").strip().lower()
    if name == "stub":
        return StubClinicalIntakeProvider()
    logger.info(
        "AI provider '%s' not implemented for intake in Phase 3; using stub", name
    )
    return StubClinicalIntakeProvider()

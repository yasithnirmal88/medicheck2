"""Phase 1 AI explanation contracts (input + output).

These DTOs are the ONLY data that crosses into and out of the AI explanation
layer. They deliberately exclude authentication tokens, unrelated patient
records, database internals, and any field the AI does not need to explain an
already-generated deterministic report.

The deterministic CDSE / ReportService remain the source of truth; the AI only
explains their output. See MEDICHECK_AI_BASELINE.md §12-13 and
MEDICHECK_AI_PHASE1_REPORT.md.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Phase 7 — Health literacy levels + AI quality status
# ---------------------------------------------------------------------------


class LiteracyLevel(str, Enum):
    """Patient-facing explanation complexity. The deterministic result is
    identical at every level; only communication changes."""

    SIMPLE = "simple"
    STANDARD = "standard"
    DETAILED = "detailed"


class AIQualityStatus(str, Enum):
    """Internal classification of an AI response lifecycle outcome.

    ``valid`` — provider returned parseable, allow-list-valid output.
    ``fallback`` — provider unavailable or timed out; safe fallback used.
    ``validation_failed`` — provider output rejected by allow-list validation.
    ``provider_unavailable`` — no provider configured / network error.
    ``evidence_unavailable`` — explanation succeeded but no evidence was found.
    """

    VALID = "valid"
    FALLBACK = "fallback"
    VALIDATION_FAILED = "validation_failed"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    EVIDENCE_UNAVAILABLE = "evidence_unavailable"
    BUDGET_EXCEEDED = "budget_exceeded"


# ---------------------------------------------------------------------------
# Phase 7 — Source breakdown for "Show the source" transparency
# ---------------------------------------------------------------------------


class SourceBreakdownItem(BaseModel):
    """A single traceable link in the evidence chain shown to the patient."""

    clinical_finding: str
    contributing_answer_refs: list[str] = Field(default_factory=list)
    knowledge_graph_relationship: str = ""
    evidence_ids: list[str] = Field(default_factory=list)
    deterministic_score: float | None = None
    trace_id: str | None = None


# ---------------------------------------------------------------------------
# Input contract: the minimal report context sent to the AI provider.
# ---------------------------------------------------------------------------


class IndicatorContext(BaseModel):
    id: str
    key: str = ""
    name: str
    description: str | None = None
    body_system_id: str | None = None
    severity: str | None = None
    evidence_strength: str | None = None
    score: float | None = None
    evidence_count: int | None = None


class ConditionContext(BaseModel):
    id: str
    code: str | None = None
    name: str
    description: str | None = None
    body_system_id: str | None = None
    severity: str | None = None
    score: float | None = None
    confidence: float | None = None


class RecommendationContext(BaseModel):
    id: str
    title: str
    text: str = ""
    category: str | None = None
    priority: int | None = None
    urgency: str | None = None
    evidence_level: str | None = None


class LaboratoryTestContext(BaseModel):
    id: str
    name: str
    description: str | None = None
    reason: str | None = None


class BodySystemContext(BaseModel):
    body_system_id: str | None = None
    name: str | None = None
    category: str | None = None
    score: float | None = None


class EvidenceContext(BaseModel):
    id: str
    title: str
    source: str | None = None
    url: str | None = None
    evidence_level: str | None = None
    summary: str | None = None


class RetrievedEvidenceContext(EvidenceContext):
    """Phase 2: an evidence record retrieved via the knowledge graph.

    Adds the deterministic retrieval metadata (relevance tier/score, the
    entity it was linked to, a bounded excerpt) so the AI and the patient can
    tell WHY this evidence was supplied. The ``id`` is the only citation id the
    AI is ever allowed to reference; the output validator enforces this.
    """

    relevance: float = 0.0
    retrieval_tier: int = 0  # 1=indicator-direct, 2=condition-transitive, 3=rec-transitive
    linked_entity_type: str = ""  # "indicator" | "condition" | "recommendation"
    linked_entity_id: str = ""
    excerpt: str = ""
    publication_year: int | None = None


class ReportExplanationContext(BaseModel):
    """Minimal, PHI-scrubbed context derived from the deterministic report.

    Every entity id in this context is the allow-list the AI may reference in
    its output. The output validator (see ``AIExplanationResponse``) rejects
    any id not present here.
    """

    trace_id: str | None = None
    severity: str | None = None
    body_systems: list[BodySystemContext] = Field(default_factory=list)
    activated_indicators: list[IndicatorContext] = Field(default_factory=list)
    possible_conditions: list[ConditionContext] = Field(default_factory=list)
    recommendations: list[RecommendationContext] = Field(default_factory=list)
    laboratory_tests: list[LaboratoryTestContext] = Field(default_factory=list)
    evidence: list[RetrievedEvidenceContext] = Field(default_factory=list)
    # True when the retrieval service found >=1 eligible evidence record. When
    # False the AI must state that no supporting evidence was available rather
    # than fabricating any.
    evidence_available: bool = False
    prompt_version: str = ""
    # Phase 7: language + literacy level for personalized communication.
    # Language resolves to the SAME canonical indicator IDs (Phase 5 principle).
    language: str = "en"
    literacy_level: LiteracyLevel = LiteracyLevel.STANDARD

    model_config = {"from_attributes": True}

    @property
    def allowed_indicator_ids(self) -> set[str]:
        return {i.id for i in self.activated_indicators}

    @property
    def allowed_recommendation_ids(self) -> set[str]:
        return {r.id for r in self.recommendations}

    @property
    def allowed_condition_ids(self) -> set[str]:
        return {c.id for c in self.possible_conditions}

    @property
    def allowed_evidence_ids(self) -> set[str]:
        return {e.id for e in self.evidence}


# ---------------------------------------------------------------------------
# Output contract: the validated structured explanation returned to the patient.
# ---------------------------------------------------------------------------


class KeyFinding(BaseModel):
    title: str
    explanation: str
    source_indicator_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)

    @field_validator("title", "explanation")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("finding title/explanation must not be empty")
        return v.strip()


class RecommendationExplanation(BaseModel):
    recommendation_id: str
    explanation: str
    evidence_ids: list[str] = Field(default_factory=list)

    @field_validator("explanation")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("recommendation explanation must not be empty")
        return v.strip()


class AIExplanationResponse(BaseModel):
    """Validated AI explanation. Raw LLM output is never trusted directly.

    The ``_validate_referenced_ids`` validator enforces the safety boundary:
    any indicator or recommendation id referenced by the AI MUST already exist
    in the supplied deterministic context. Hallucinated ids are rejected.
    """

    summary: str
    key_findings: list[KeyFinding] = Field(default_factory=list)
    severity_explanation: str = ""
    recommendation_explanations: list[RecommendationExplanation] = Field(
        default_factory=list
    )
    evidence_notes: list[str] = Field(default_factory=list)
    limitations: str = ""
    disclaimer: str
    available: bool = True
    prompt_version: str = ""
    trace_id: str | None = None
    # Phase 2 traceability / transparency: the evidence actually retrieved and
    # supplied to the AI, returned to the patient so citations are verifiable.
    retrieved_evidence: list[RetrievedEvidenceContext] = Field(default_factory=list)
    evidence_available: bool = True
    # Phase 7: language + literacy level of this explanation.
    language: str = "en"
    literacy_level: LiteracyLevel = LiteracyLevel.STANDARD
    # Phase 7: AI quality status (valid/fallback/validation_failed/...).
    quality_status: AIQualityStatus = AIQualityStatus.VALID
    # Phase 7: "Show the source" — traceable chain per finding.
    source_breakdown: list[SourceBreakdownItem] = Field(default_factory=list)
    # Phase 7: AI transparency notice (patient-facing).
    transparency_notice: str = ""
    # Phase 7: audit metadata (provider/model/prompt_version for governance).
    provider: str = ""
    model: str = ""

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def _validate_referenced_ids(self) -> "AIExplanationResponse":
        # The allow-lists are injected by the service via context. When this
        # model is constructed directly (e.g. the unavailable fallback) there
        # is nothing to validate, so we only enforce when sets were attached.
        allowed_ind = getattr(self, "_allowed_indicator_ids", None)
        allowed_rec = getattr(self, "_allowed_recommendation_ids", None)
        allowed_ev = getattr(self, "_allowed_evidence_ids", None)
        if allowed_ind is not None:
            for kf in self.key_findings:
                bad = [i for i in kf.source_indicator_ids if i not in allowed_ind]
                if bad:
                    raise ValueError(
                        f"AI referenced unknown indicator id(s): {bad}"
                    )
        if allowed_rec is not None:
            for re_ in self.recommendation_explanations:
                if re_.recommendation_id not in allowed_rec:
                    raise ValueError(
                        f"AI referenced unknown recommendation id: "
                        f"{re_.recommendation_id}"
                    )
        # Anti-hallucination: every cited evidence_id MUST be in the retrieved
        # allow-list. Hallucinated citations (e.g. "EV-999") are rejected.
        if allowed_ev is not None:
            for kf in self.key_findings:
                bad = [e for e in kf.evidence_ids if e not in allowed_ev]
                if bad:
                    raise ValueError(
                        f"AI referenced unsupplied evidence id(s): {bad}"
                    )
            for re_ in self.recommendation_explanations:
                bad = [e for e in re_.evidence_ids if e not in allowed_ev]
                if bad:
                    raise ValueError(
                        f"AI referenced unsupplied evidence id(s): {bad}"
                    )
        return self

    def bind_context(
        self,
        *,
        allowed_indicator_ids: set[str],
        allowed_recommendation_ids: set[str],
        allowed_evidence_ids: set[str] | None = None,
    ) -> "AIExplanationResponse":
        """Attach the deterministic allow-lists so the validator can run.

        Called by the service after parsing raw provider output. The evidence
        allow-list is the set of ids actually retrieved — the only citations
        the AI is permitted to use.
        """
        object.__setattr__(
            self, "_allowed_indicator_ids", allowed_indicator_ids
        )
        object.__setattr__(
            self, "_allowed_recommendation_ids", allowed_recommendation_ids
        )
        object.__setattr__(
            self, "_allowed_evidence_ids", allowed_evidence_ids or set()
        )
        # Re-run the cross-field validation now that allow-lists exist.
        return self._validate_referenced_ids()

    @field_validator("summary", "disclaimer")
    @classmethod
    def _bounded_text(cls, v: str, info: Any) -> str:
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} must not be empty")
        if len(v) > 5000:
            raise ValueError(f"{info.field_name} exceeds maximum length")
        return v.strip()

    @field_validator("evidence_notes")
    @classmethod
    def _bounded_notes(cls, v: list[str]) -> list[str]:
        if len(v) > 50:
            raise ValueError("too many evidence_notes")
        for n in v:
            if not isinstance(n, str) or len(n) > 2000:
                raise ValueError("evidence_note malformed")
        return v


#: Explicit diagnostic-claim patterns. Bare words like "diagnosis" are
#: deliberately NOT matched — legitimate non-diagnostic phrasing ("not a
#: diagnosis", "AI did not diagnose") must pass.
_DIAGNOSTIC_CLAIM_RE = re.compile(
    r"\b(you have|you've got|youve got|diagnosed with|diagnosis of|"
    r"confirmed condition|confirmed diagnosis|"
    r"disease (is )?(getting worse|progressing|resolved)|"
    r"will develop|chance of developing)\b",
    re.IGNORECASE,
)

#: Negation cues that neutralize a claim match ("does not mean you have a
#: disease" is explicitly non-diagnostic and must pass).
_NEGATION_RE = re.compile(
    r"\b(not|does not|doesn['\u2019]t|do not|don['\u2019]t|never|"
    r"no longer|without|isn['\u2019]t|aren['\u2019]t|cannot|"
    r"can['\u2019]t|neither|nor)\b",
    re.IGNORECASE,
)

#: Sinhala diagnostic-claim patterns. Narrow by design: the subject "ඔබට"
#: ("to you") plus a "have/exists" verb within a short window is the
#: canonical "you have X" claim form an LLM emits; bare "තියෙනවා"
#: ("exists") alone is NOT matched (e.g. "questions තියෙනවා නම්" is
#: innocuous). "තහවුරු" ("confirmed") forms are matched directly.
_SI_CLAIM_RE = re.compile(
    r"ඔබට.{0,40}(තියෙනවා|තියෙයි|ඇත|ඇති)|තහවුරු(යි|ව|කර|කළ)",
)

#: Sinhala negation cues (superset of the Phase 5 intake cues). Sinhala is
#: SOV: negators usually FOLLOW the claim ("...තියෙනවා නොවේ"), so both
#: sides of a match are checked (see _SIDE_RULES).
_SI_NEGATION_RE = re.compile(
    r"(නෑ|නැහැ|නොමැත|නැති|නැත|නොව|නොහැක|නොකිය)",
)

#: Tamil diagnostic-claim patterns. Same narrow subject+verb structure:
#: "உங்களுக்கு" ("to you") plus a "have/exists" verb, or an explicit
#: "disease confirmed" phrase.
_TA_CLAIM_RE = re.compile(
    r"உங்களுக்கு.{0,40}(உள்ளது|இருக்கிறது|உள்ளன|இருக்கின்றன)|"
    r"நோய்.{0,20}உறுதி|உறுதிப்படுத்தப்பட்ட",
)

#: Tamil negation cues (superset of the Phase 5 intake cues). Covers the
#: இல்லை-family ("not have/exist"), அல்ல ("is not"), and -ஆது verb negations
#: ("சொல்லாது" = "does not say" — the form the "does not say you have a
#: disease" disclaimer uses).
_TA_NEGATION_RE = re.compile(
    r"(இல்லை|இல்ல|கிடையாது|இல்லையென|அல்ல|ாது)",
)

#: (claim pattern, negation pattern, prefix window, suffix window).
#: English keeps its exact legacy behaviour (prefix-only). Sinhala/Tamil
#: also check a suffix window because their negators typically follow the
#: claim (SOV order), sometimes across a subordinate clause.
_SIDE_RULES = (
    (_SI_CLAIM_RE, _SI_NEGATION_RE, 80, 80),
    (_TA_CLAIM_RE, _TA_NEGATION_RE, 80, 80),
)


def screen_diagnostic_claims(*texts: str | None) -> None:
    """Reject provider free text that reads as a diagnosis.

    Raises ``ValueError`` when a diagnostic claim appears WITHOUT a nearby
    negation. Negated statements ("this does not mean you have a disease")
    pass. Covers English plus Sinhala and Tamil (subject+verb claim forms);
    other languages and romanized (Latin-script) Sinhala/Tamil rely on prompt
    binding + allow-list validation (documented limitation).
    """
    for text in texts:
        if not text:
            continue
        # English (legacy, prefix-only) — byte-identical behaviour.
        for match in _DIAGNOSTIC_CLAIM_RE.finditer(text):
            prefix = text[max(0, match.start() - 60):match.start()]
            if _NEGATION_RE.search(prefix):
                continue
            raise ValueError(
                "AI explanation reads as a diagnosis, not an explanation"
            )
        # Sinhala / Tamil (bidirectional negation window).
        for claim_re, neg_re, pre, post in _SIDE_RULES:
            for match in claim_re.finditer(text):
                start = match.start()
                window = text[max(0, start - pre):match.end() + post]
                if neg_re.search(window):
                    continue
                raise ValueError(
                    "AI explanation reads as a diagnosis, not an explanation"
                )


# Standard fallback returned when the AI is unavailable or invalid. The
# clinical report itself remains fully available to the patient.
UNAVAILABLE_FALLBACK = AIExplanationResponse(
    summary=(
        "We couldn't generate an AI explanation for this report right now. "
        "Your clinical assessment below is unaffected and still available."
    ),
    key_findings=[],
    severity_explanation="",
    recommendation_explanations=[],
    evidence_notes=[],
    limitations=(
        "The AI explanation service is currently unavailable. This does not "
        "affect your clinical assessment, which was produced by MediCheck's "
        "deterministic clinical decision-support engine."
    ),
    disclaimer=(
        "This AI-generated explanation is based on your MediCheck assessment "
        "and does not constitute a diagnosis. The underlying assessment is "
        "generated by the deterministic clinical engine."
    ),
    available=False,
    evidence_available=False,
    quality_status=AIQualityStatus.PROVIDER_UNAVAILABLE,
    transparency_notice=(
        "Your clinical assessment was calculated by MediCheck's "
        "deterministic clinical decision engine. AI was used only to "
        "explain and communicate the results. AI did not diagnose a "
        "disease, calculate your clinical score, determine severity, "
        "create your recommendations, or modify your assessment."
    ),
    provider="stub",
    model="",
)

# Standard message the AI/stub must use when retrieval found no eligible
# evidence, so the patient is never led to believe supporting evidence exists.
NO_EVIDENCE_AVAILABLE_MESSAGE = (
    "No supporting evidence was available from the MediCheck evidence "
    "repository for this explanation."
)

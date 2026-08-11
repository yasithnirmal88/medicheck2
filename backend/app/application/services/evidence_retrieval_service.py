"""Phase 2 — Evidence-Grounded Retrieval service.

Reads the deterministic assessment result and retrieves eligible, approved
clinical evidence from MediCheck's knowledge graph, then ranks and bounds it
for the AI context.

Design (verified against the actual source, not the baseline's conceptual
model):

Evidence store in use:
- ``EvidenceReferenceModel`` (``evidence_references``) — the seeded, approved
  clinical evidence (guidelines). Fields: id, title, url, source,
  evidence_level, summary, question_id. Has ``SoftDeleteMixin`` (``deleted_at``)
  and ``TimestampMixin``. It has NO ``status`` / ``is_active`` column, so
  eligibility = ``deleted_at IS NULL`` (not soft-deleted).
- ``MedicalEvidenceModel`` (``medical_evidence``) — a richer parallel entity
  with a draft/published lifecycle, but it is NOT seeded and NOT wired into the
  indicator→evidence link graph. It is therefore NOT used for Phase 2
  retrieval. (Documented as a known limitation / future wiring point.)

Knowledge-graph relationships (link tables in ``links.py``):
- ``IndicatorEvidenceLinkModel`` (indicator ↔ evidence, ``active`` flag) — the
  primary grounding edge.
- ``IndicatorConditionLinkModel``, ``ConditionRecommendationLinkModel``,
  ``IndicatorRecommendationLinkModel``, ``ConditionLaboratoryTestLinkModel``,
  ``BodySystemConditionLinkModel`` — used to reach evidence transitively.
- There is NO direct condition↔evidence or recommendation↔evidence link table.
  Conditions and recommendations reach evidence via their linked indicators.

Retrieval is READ-ONLY and deterministic. The LLM never decides relevance.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.ai_dtos import RetrievedEvidenceContext
from app.core.config import settings
from app.core.logging import get_logger
from app.infrastructure.persistence.models.evidence_reference import (
    EvidenceReferenceModel,
)
from app.infrastructure.persistence.models.links import (
    ConditionRecommendationLinkModel,
    IndicatorConditionLinkModel,
    IndicatorEvidenceLinkModel,
    IndicatorRecommendationLinkModel,
)

logger = get_logger(__name__)

# Retrieval tiers. Lower number = higher priority (more directly grounded).
TIER_INDICATOR = 1
TIER_CONDITION = 2
TIER_RECOMMENDATION = 3

# Evidence-level → numeric weight. Higher = stronger evidence. Levels observed
# in the seed are single letters A–D; the CMS service also uses "Level I" etc.
# Unknown levels get a neutral weight so ranking never errors.
_EVIDENCE_LEVEL_WEIGHT: dict[str, float] = {
    "A": 1.0,
    "B": 0.8,
    "C": 0.6,
    "D": 0.4,
    "LEVEL I": 1.0,
    "LEVEL II": 0.8,
    "LEVEL III": 0.6,
    "LEVEL IV": 0.4,
    "LEVEL V": 0.3,
}


def _level_weight(level: str | None) -> float:
    if not level:
        return 0.5
    return _EVIDENCE_LEVEL_WEIGHT.get(level.strip().upper(), 0.5)


@dataclass
class _Candidate:
    evidence: EvidenceReferenceModel
    tier: int
    linked_entity_type: str
    linked_entity_id: str
    entity_label: str = ""  # indicator/condition/recommendation name for text relevance
    _score: float | None = None

    def score(self) -> float:
        if self._score is None:
            self._score = _rank_score(self)
        return self._score


def _rank_score(c: _Candidate) -> float:
    """Deterministic relevance score in [0, 1].

    Components:
    - tier weight (direct indicator evidence ranks highest)
    - evidence-level weight (A > B > C ...)
    - recency proxy (EvidenceReferenceModel has no publication date; use
      created_at as a weak tiebreaker)
    - text relevance: keyword overlap between the evidence title and the linked
      entity label (deterministic, not semantic)
    """
    tier_w = {TIER_INDICATOR: 0.9, TIER_CONDITION: 0.7, TIER_RECOMMENDATION: 0.6}[c.tier]
    level_w = _level_weight(c.evidence.evidence_level)
    recency = 0.0
    created = getattr(c.evidence, "created_at", None)
    if isinstance(created, datetime):
        # 0.05 for anything within ~5 years, scaled down otherwise. Weak only.
        # SQLite may store naive datetimes; normalise both sides to naive UTC.
        cdt = created.replace(tzinfo=None) if created.tzinfo else created
        now_naive = datetime.now(UTC).replace(tzinfo=None)
        days = (now_naive - cdt).days
        recency = max(0.0, 0.05 - days / 365 / 20)
    text_w = _text_overlap(c.evidence.title, c.entity_label)
    return round(tier_w * 0.6 + level_w * 0.25 + recency + text_w * 0.1, 4)


_WORD_RE = re.compile(r"[a-z0-9]+")


def _tokens(text: str | None) -> set[str]:
    if not text:
        return set()
    return {t for t in _WORD_RE.findall(text.lower()) if len(t) > 2}


def _text_overlap(a: str | None, b: str | None) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / min(len(ta), len(tb))


def _excerpt(summary: str | None, max_chars: int) -> str:
    if not summary:
        return ""
    s = summary.strip()
    if len(s) <= max_chars:
        return s
    return s[: max_chars - 1].rstrip() + "…"


@dataclass
class RetrievalResult:
    """Structured retrieval result returned to the AIExplanationService."""

    evidence: list[RetrievedEvidenceContext] = field(default_factory=list)

    @property
    def available(self) -> bool:
        return len(self.evidence) > 0

    @property
    def evidence_ids(self) -> list[str]:
        return [e.id for e in self.evidence]


class EvidenceRetrievalService:
    """Retrieves, filters, ranks, and bounds approved evidence for a report.

    All retrieval is derived from the caller's authorised deterministic result
    (activated indicators / conditions / recommendations). A user can never
    receive evidence from another patient's assessment because the seed
    indicators/conditions come from that user's own AssessmentResultModel.
    """

    def __init__(
        self,
        session: AsyncSession,
        *,
        evidence_limit: int | None = None,
        per_entity_cap: int | None = None,
        excerpt_max_chars: int | None = None,
    ) -> None:
        self.session = session
        # Config overrides default to the global settings; tests inject
        # explicit values so they never mutate global Pydantic settings.
        self.evidence_limit = (
            evidence_limit
            if evidence_limit is not None
            else max(1, int(settings.ai_rag_evidence_limit))
        )
        self.per_entity_cap = (
            per_entity_cap
            if per_entity_cap is not None
            else max(1, int(settings.ai_rag_per_entity_cap))
        )
        self.excerpt_max_chars = (
            excerpt_max_chars
            if excerpt_max_chars is not None
            else max(50, int(settings.ai_rag_excerpt_max_chars))
        )

    async def retrieve(
        self,
        *,
        indicator_ids: list[str],
        condition_ids: list[str],
        recommendation_ids: list[str],
        indicator_labels: dict[str, str] | None = None,
        condition_labels: dict[str, str] | None = None,
        recommendation_labels: dict[str, str] | None = None,
    ) -> RetrievalResult:
        """Return the bounded, ranked, deduplicated evidence list.

        Args are the ids from the deterministic result. Labels (names) are
        used only as a deterministic text-relevance tiebreaker.
        """
        ind_labels = indicator_labels or {}
        cond_labels = condition_labels or {}
        rec_labels = recommendation_labels or {}

        candidates: list[_Candidate] = []

        # Tier 1: evidence directly linked to activated indicators.
        if indicator_ids:
            ind_ev = await self._indicator_evidence(indicator_ids)
            for ind_id, evs in ind_ev.items():
                for ev in evs:
                    candidates.append(
                        _Candidate(
                            evidence=ev,
                            tier=TIER_INDICATOR,
                            linked_entity_type="indicator",
                            linked_entity_id=ind_id,
                            entity_label=ind_labels.get(ind_id, ""),
                        )
                    )

        # Tier 2: evidence via conditions → their linked indicators → evidence.
        if condition_ids:
            cond_to_inds = await self._conditions_to_indicators(condition_ids)
            all_ind_ids = {i for inds in cond_to_inds.values() for i in inds}
            if all_ind_ids:
                cond_ev = await self._indicator_evidence(list(all_ind_ids))
                seen_per_cond: dict[str, set[str]] = {}
                for cond_id, ind_ids in cond_to_inds.items():
                    seen_per_cond.setdefault(cond_id, set())
                    for ind_id in ind_ids:
                        for ev in cond_ev.get(ind_id, []):
                            if ev.id in seen_per_cond[cond_id]:
                                continue
                            seen_per_cond[cond_id].add(ev.id)
                            candidates.append(
                                _Candidate(
                                    evidence=ev,
                                    tier=TIER_CONDITION,
                                    linked_entity_type="condition",
                                    linked_entity_id=cond_id,
                                    entity_label=cond_labels.get(cond_id, ""),
                                )
                            )

        # Tier 3: evidence via recommendations → linked indicators → evidence.
        if recommendation_ids:
            rec_to_inds = await self._recommendations_to_indicators(
                recommendation_ids
            )
            all_ind_ids = {i for inds in rec_to_inds.values() for i in inds}
            if all_ind_ids:
                rec_ev = await self._indicator_evidence(list(all_ind_ids))
                seen_per_rec: dict[str, set[str]] = {}
                for rec_id, ind_ids in rec_to_inds.items():
                    seen_per_rec.setdefault(rec_id, set())
                    for ind_id in ind_ids:
                        for ev in rec_ev.get(ind_id, []):
                            if ev.id in seen_per_rec[rec_id]:
                                continue
                            seen_per_rec[rec_id].add(ev.id)
                            candidates.append(
                                _Candidate(
                                    evidence=ev,
                                    tier=TIER_RECOMMENDATION,
                                    linked_entity_type="recommendation",
                                    linked_entity_id=rec_id,
                                    entity_label=rec_labels.get(rec_id, ""),
                                )
                            )

        return self._select(candidates)

    # --- graph traversal (batched to avoid N+1) ---

    async def _indicator_evidence(
        self, indicator_ids: list[str]
    ) -> dict[str, list[EvidenceReferenceModel]]:
        """Active links → non-soft-deleted evidence, batched."""
        if not indicator_ids:
            return {}
        q = (
            select(EvidenceReferenceModel, IndicatorEvidenceLinkModel.indicator_id)
            .join(
                IndicatorEvidenceLinkModel,
                IndicatorEvidenceLinkModel.evidence_id == EvidenceReferenceModel.id,
            )
            .where(
                IndicatorEvidenceLinkModel.indicator_id.in_(indicator_ids),
                IndicatorEvidenceLinkModel.active.is_(True),
                EvidenceReferenceModel.deleted_at.is_(None),
            )
        )
        r = await self.session.execute(q)
        out: dict[str, list[EvidenceReferenceModel]] = {}
        for ev, ind_id in r.all():
            out.setdefault(ind_id, []).append(ev)
        return out

    async def _conditions_to_indicators(
        self, condition_ids: list[str]
    ) -> dict[str, list[str]]:
        if not condition_ids:
            return {}
        q = select(
            IndicatorConditionLinkModel.condition_id,
            IndicatorConditionLinkModel.indicator_id,
        ).where(
            IndicatorConditionLinkModel.condition_id.in_(condition_ids),
            IndicatorConditionLinkModel.active.is_(True),
        )
        r = await self.session.execute(q)
        out: dict[str, list[str]] = {}
        for cond_id, ind_id in r.all():
            out.setdefault(cond_id, []).append(ind_id)
        return out

    async def _recommendations_to_indicators(
        self, recommendation_ids: list[str]
    ) -> dict[str, list[str]]:
        """Recommendations reach indicators via two link tables:
        IndicatorRecommendationLinkModel (direct) and
        ConditionRecommendationLinkModel → IndicatorConditionLinkModel.
        Both are followed, active links only.
        """
        if not recommendation_ids:
            return {}
        direct = await self.session.execute(
            select(
                IndicatorRecommendationLinkModel.recommendation_id,
                IndicatorRecommendationLinkModel.indicator_id,
            ).where(
                IndicatorRecommendationLinkModel.recommendation_id.in_(
                    recommendation_ids
                ),
                IndicatorRecommendationLinkModel.active.is_(True),
            )
        )
        out: dict[str, list[str]] = {}
        for rec_id, ind_id in direct.all():
            out.setdefault(rec_id, []).append(ind_id)

        # Transitive via conditions.
        cond_links = await self.session.execute(
            select(
                ConditionRecommendationLinkModel.recommendation_id,
                ConditionRecommendationLinkModel.condition_id,
            ).where(
                ConditionRecommendationLinkModel.recommendation_id.in_(
                    recommendation_ids
                ),
                ConditionRecommendationLinkModel.active.is_(True),
            )
        )
        rec_to_conds: dict[str, list[str]] = {}
        for rec_id, cond_id in cond_links.all():
            rec_to_conds.setdefault(rec_id, []).append(cond_id)
        all_conds = {c for cs in rec_to_conds.values() for c in cs}
        if all_conds:
            cond_to_inds = await self._conditions_to_indicators(list(all_conds))
            for rec_id, cond_ids in rec_to_conds.items():
                for cond_id in cond_ids:
                    for ind_id in cond_to_inds.get(cond_id, []):
                        if ind_id not in out.get(rec_id, []):
                            out.setdefault(rec_id, []).append(ind_id)
        return out

    # --- selection: dedup, rank, cap, limit ---

    def _select(self, candidates: list[_Candidate]) -> RetrievalResult:
        if not candidates:
            return RetrievalResult()

        limit = max(1, int(self.evidence_limit))
        per_entity_cap = max(1, int(self.per_entity_cap))
        max_chars = max(50, int(self.excerpt_max_chars))

        # Deduplicate by evidence id, keeping the BEST (lowest tier / highest
        # score) candidate for each evidence id.
        best: dict[str, _Candidate] = {}
        for c in candidates:
            existing = best.get(c.evidence.id)
            if existing is None or c.score() > existing.score():
                best[c.evidence.id] = c

        ranked = sorted(best.values(), key=lambda c: c.score(), reverse=True)

        # Per-linked-entity cap so one indicator cannot monopolise the budget.
        entity_count: dict[str, int] = {}
        selected: list[_Candidate] = []
        for c in ranked:
            key = f"{c.linked_entity_type}:{c.linked_entity_id}"
            if entity_count.get(key, 0) >= per_entity_cap:
                continue
            entity_count[key] = entity_count.get(key, 0) + 1
            selected.append(c)
            if len(selected) >= limit:
                break

        evidence = [
            RetrievedEvidenceContext(
                id=c.evidence.id,
                title=c.evidence.title,
                source=c.evidence.source,
                url=c.evidence.url,
                evidence_level=c.evidence.evidence_level,
                summary=c.evidence.summary,
                excerpt=_excerpt(c.evidence.summary, max_chars),
                relevance=c.score(),
                retrieval_tier=c.tier,
                linked_entity_type=c.linked_entity_type,
                linked_entity_id=c.linked_entity_id,
            )
            for c in selected
        ]
        return RetrievalResult(evidence=evidence)

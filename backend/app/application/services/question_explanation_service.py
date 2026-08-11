"""Phase 7 — "Why was I asked this?" question explanation service.

Uses EXISTING knowledge-graph relationships to explain why a question was
included in an assessment. The AI must NOT invent medical relationships —
it only surfaces links that already exist in the knowledge graph:

    question → indicator (QuestionIndicatorLinkModel)
    indicator → condition (IndicatorConditionLinkModel)
    question → evidence (EvidenceReferenceModel.question_id)

Ownership: the caller must own the session. A patient can only ask about
questions in their own assessment.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.infrastructure.persistence.models.assessment_answer import (
    AssessmentAnswerModel,
)
from app.infrastructure.persistence.models.assessment_session import (
    AssessmentSessionModel,
)
from app.infrastructure.persistence.models.clinical_indicator import (
    ClinicalIndicatorModel,
)
from app.infrastructure.persistence.models.evidence_reference import (
    EvidenceReferenceModel,
)
from app.infrastructure.persistence.models.links import (
    IndicatorConditionLinkModel,
    QuestionIndicatorLinkModel,
)
from app.infrastructure.persistence.models.possible_condition import (
    PossibleConditionModel,
)
from app.infrastructure.persistence.models.question import QuestionModel

logger = get_logger(__name__)

# Language-localized phrases for question explanation.
_Q_PHRASES: dict[str, dict[str, str]] = {
    "explanation_unavailable": {
        "en": "Explanation unavailable.",
        "si": "පැහැදිලි කිරීම ලබා ගත නොහැක.",
        "ta": "விளக்கம் கிடைக்கவில்லை.",
    },
    "prefix": {
        "en": "This question was included because",
        "si": "මෙම ප්‍රශ්නය ඇතුළත් කළ ඇත්තේ මන්ද",
        "ta": "இந்தக் கேள்வி சேர்க்கப்பட்டதற்கு காரணம்",
    },
    "can_be_relevant": {
        "en": "can be relevant when assessing certain health indicators.",
        "si": "යම් සෞඛ්‍ය දර්ශක ඇගයීමේදී අදාළ විය හැක.",
        "ta": "சில சுகாதார குறிகாட்டிகளை மதிப்பிடும்போது தொடர்புடையதாக இருக்கலாம்.",
    },
    "linked_to_condition": {
        "en": "These indicators are linked to possible conditions considered by the engine.",
        "si": "මෙම දර්ශක යන්ත්‍රය විසින් සලකා බැලූ හැකි තත්ත්වයන් හා සම්බන්ධ වේ.",
        "ta": "இந்தக் குறிகாட்டிகள் எந்திரம் கருத்தில் கொண்ட சாத்தியமான நிலைகளுடன் இணைக்கப்பட்டுள்ளன.",
    },
}


def _qt(key: str, language: str) -> str:
    lang = language if language in ("en", "si", "ta") else "en"
    return _Q_PHRASES.get(key, {}).get(lang, _Q_PHRASES.get(key, {}).get("en", key))


class QuestionExplanationService:
    """Explains why a question was asked, using existing knowledge-graph links."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def explain_question(
        self,
        *,
        session_id: str,
        question_id: str,
        user_id: str,
        language: str = "en",
    ) -> dict:
        """Return a knowledge-graph-grounded explanation of why a question
        was asked. Raises ValueError if the session is not found or not
        owned by the caller, or if the question was not part of the session.
        """
        # Ownership check: session must belong to caller.
        sess = await self.session.get(AssessmentSessionModel, session_id)
        if not sess or sess.user_id != user_id:
            raise ValueError("session not found")

        # Validate question was actually asked in this session.
        answer_q = select(AssessmentAnswerModel).where(
            AssessmentAnswerModel.session_id == session_id,
            AssessmentAnswerModel.question_id == question_id,
        )
        answer = (
            await self.session.execute(answer_q)
        ).scalars().first()
        if not answer:
            raise ValueError("question not found in this assessment")

        # Load the question text.
        question = await self.session.get(QuestionModel, question_id)
        question_text = question.text if question else question_id

        # Knowledge graph: question → indicators.
        link_q = select(QuestionIndicatorLinkModel).where(
            QuestionIndicatorLinkModel.question_id == question_id,
            QuestionIndicatorLinkModel.active.is_(True),
        )
        links = (await self.session.execute(link_q)).scalars().all()
        indicator_ids = [l.indicator_id for l in links]

        indicators: list[dict] = []
        conditions: list[dict] = []
        evidence: list[dict] = []

        if indicator_ids:
            ind_rows = await self.session.execute(
                select(ClinicalIndicatorModel).where(
                    ClinicalIndicatorModel.id.in_(indicator_ids)
                )
            )
            for ind in ind_rows.scalars().all():
                indicators.append(
                    {
                        "id": ind.id,
                        "name": ind.name,
                        "body_system_id": ind.body_system_id,
                    }
                )

            # indicator → conditions.
            cond_link_q = select(IndicatorConditionLinkModel).where(
                IndicatorConditionLinkModel.indicator_id.in_(indicator_ids),
                IndicatorConditionLinkModel.active.is_(True),
            )
            cond_links = (
                await self.session.execute(cond_link_q)
            ).scalars().all()
            cond_ids = [c.condition_id for c in cond_links]
            if cond_ids:
                cond_rows = await self.session.execute(
                    select(PossibleConditionModel).where(
                        PossibleConditionModel.id.in_(cond_ids)
                    )
                )
                for cond in cond_rows.scalars().all():
                    conditions.append(
                        {"id": cond.id, "name": cond.name}
                    )

        # question → evidence (direct link).
        ev_q = select(EvidenceReferenceModel).where(
            EvidenceReferenceModel.question_id == question_id
        )
        ev_rows = (await self.session.execute(ev_q)).scalars().all()
        for ev in ev_rows:
            evidence.append(
                {
                    "id": ev.id,
                    "title": ev.title,
                    "source": ev.source,
                    "url": ev.url,
                    "evidence_level": ev.evidence_level,
                }
            )

        # Build the explanation text strictly from the knowledge graph.
        if not indicators:
            return {
                "question_id": question_id,
                "question_text": question_text,
                "explanation": _qt("explanation_unavailable", language),
                "linked_indicators": [],
                "linked_conditions": [],
                "evidence": [],
                "available": False,
                "language": language,
            }

        ind_names = ", ".join(i["name"] for i in indicators)
        explanation_parts = [
            _qt("prefix", language),
            " ",
            ind_names,
            " ",
            _qt("can_be_relevant", language),
        ]
        if conditions:
            explanation_parts.append(" ")
            explanation_parts.append(_qt("linked_to_condition", language))
        explanation = "".join(explanation_parts)

        return {
            "question_id": question_id,
            "question_text": question_text,
            "explanation": explanation,
            "linked_indicators": indicators,
            "linked_conditions": conditions,
            "evidence": evidence,
            "available": True,
            "language": language,
        }

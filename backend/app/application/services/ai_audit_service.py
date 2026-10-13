"""Phase 7 — AI interaction audit service.

Records metadata (not PHI) about every AI explanation lifecycle. The audit
record lets administrators trace: which provider/model/prompt_version
generated a given explanation, for which session/trace, in which language and
literacy level, and whether it succeeded or fell back.

No raw patient information is stored — only reference ids and hashes.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.infrastructure.persistence.models.ai_interaction_audit import (
    AIInteractionAuditModel,
)

logger = get_logger(__name__)


def _hash_context(context_dict: dict[str, Any]) -> str:
    """SHA-256 hash of the canonical JSON of the context. Only entity ids,
    scores, and structural data are included — never free-text PHI."""
    canonical = json.dumps(context_dict, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _hash_output(output_str: str) -> str:
    return hashlib.sha256(output_str.encode("utf-8")).hexdigest()


class AIAuditService:
    """Writes AI interaction audit records. Never raises — audit failure must
    not break the explanation flow."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record(
        self,
        *,
        trace_id: str | None,
        session_id: str | None,
        request_type: str,
        provider: str,
        model: str,
        prompt_version: str,
        language: str,
        literacy_level: str,
        input_context: dict[str, Any] | None = None,
        output_str: str | None = None,
        status: str = "valid",
        status_reason: str | None = None,
    ) -> None:
        try:
            audit = AIInteractionAuditModel(
                trace_id=trace_id,
                session_id=session_id,
                request_type=request_type,
                provider=provider,
                model=model or "",
                prompt_version=prompt_version or "",
                language=language or "en",
                literacy_level=literacy_level or "standard",
                input_context_hash=(
                    _hash_context(input_context) if input_context else None
                ),
                output_hash=_hash_output(output_str) if output_str else None,
                status=status,
                status_reason=status_reason,
            )
            self.session.add(audit)
            await self.session.commit()
        except Exception as exc:
            logger.warning("AI audit record failed: %s", exc)
            await self.session.rollback()

    async def get_governance_summary(
        self,
    ) -> dict[str, Any]:
        """Aggregate AI quality metrics for the CMS governance dashboard.

        Returns de-identified counts only — no session_id, trace_id, or
        patient-identifying data. CMS-authorized callers only.
        """
        total_q = select(func.count(AIInteractionAuditModel.id))
        total = (await self.session.execute(total_q)).scalar() or 0

        by_status_q = (
            select(
                AIInteractionAuditModel.status,
                func.count(AIInteractionAuditModel.id),
            )
            .group_by(AIInteractionAuditModel.status)
        )
        status_rows = (await self.session.execute(by_status_q)).all()
        by_status = {row[0]: row[1] for row in status_rows}

        by_language_q = (
            select(
                AIInteractionAuditModel.language,
                func.count(AIInteractionAuditModel.id),
            )
            .group_by(AIInteractionAuditModel.language)
        )
        lang_rows = (await self.session.execute(by_language_q)).all()
        by_language = {row[0]: row[1] for row in lang_rows}

        by_provider_q = (
            select(
                AIInteractionAuditModel.provider,
                func.count(AIInteractionAuditModel.id),
            )
            .group_by(AIInteractionAuditModel.provider)
        )
        provider_rows = (await self.session.execute(by_provider_q)).all()
        by_provider = {row[0]: row[1] for row in provider_rows}

        by_prompt_q = (
            select(
                AIInteractionAuditModel.prompt_version,
                func.count(AIInteractionAuditModel.id),
            )
            .group_by(AIInteractionAuditModel.prompt_version)
        )
        prompt_rows = (await self.session.execute(by_prompt_q)).all()
        by_prompt_version = {row[0]: row[1] for row in prompt_rows}

        fallback = by_status.get("fallback", 0)
        validation_failed = by_status.get("validation_failed", 0)
        provider_unavailable = by_status.get("provider_unavailable", 0)
        evidence_unavailable = by_status.get("evidence_unavailable", 0)
        valid = by_status.get("valid", 0)
        successful = valid + evidence_unavailable
        fallback_rate = (fallback / total * 100) if total else 0.0
        validation_failure_rate = (
            validation_failed / total * 100 if total else 0.0
        )

        return {
            "total_requests": total,
            "successful_explanations": successful,
            "fallback_count": fallback,
            "fallback_rate_pct": round(fallback_rate, 2),
            "validation_failure_count": validation_failed,
            "validation_failure_rate_pct": round(
                validation_failure_rate, 2
            ),
            "provider_unavailable_count": provider_unavailable,
            "evidence_unavailable_count": evidence_unavailable,
            "by_status": by_status,
            "by_language": by_language,
            "by_provider": by_provider,
            "by_prompt_version": by_prompt_version,
        }

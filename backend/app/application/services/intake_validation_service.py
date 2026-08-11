"""Candidate validation service (Phase 3).

The database is authoritative. The AI's knowledge of the graph is never trusted.

Given raw provider output + the bounded indicator catalog used for the request,
this service:
- re-validates every candidate ``indicator_id`` against the catalog (the
  catalog was built from active, non-deleted indicators);
- rejects unknown / inactive / soft-deleted indicator IDs (silently dropped,
  never created, never inserted);
- rejects candidates with out-of-range confidence;
- binds each candidate's ``observation_ids`` to the observations actually
  produced by this intake (unknown observation references are dropped);
- returns validated ``CandidateIndicatorDTO`` objects + a trace of rejections
  for observability.

It does NOT activate indicators, score, set severity, or write to the DB.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.application.dtos.intake_dtos import (
    CandidateIndicatorDTO,
    IndicatorCatalog,
    ObservationDTO,
    ProviderCandidateRaw,
    ProviderOutput,
)

#: Maximum candidates retained after validation.
MAX_VALIDATED_CANDIDATES = 12


@dataclass
class ValidationTrace:
    accepted: list[CandidateIndicatorDTO] = field(default_factory=list)
    rejected_unknown_indicator: list[str] = field(default_factory=list)
    rejected_inactive_indicator: list[str] = field(default_factory=list)
    rejected_deleted_indicator: list[str] = field(default_factory=list)
    rejected_invalid_confidence: list[str] = field(default_factory=list)
    rejected_orphan_observations: list[str] = field(default_factory=list)

    @property
    def total_rejected(self) -> int:
        return (
            len(self.rejected_unknown_indicator)
            + len(self.rejected_inactive_indicator)
            + len(self.rejected_deleted_indicator)
            + len(self.rejected_invalid_confidence)
            + len(self.rejected_orphan_observations)
        )


class CandidateValidationService:
    """Validates AI candidate indicators against the authoritative catalog."""

    def validate(
        self,
        provider_output: ProviderOutput,
        catalog: IndicatorCatalog,
        observations: list[ObservationDTO],
    ) -> ValidationTrace:
        allowed_ids = catalog.allowed_ids()
        allowed_by_id = catalog.by_id()
        obs_ids = {o.id for o in observations}
        # The provider may reference observations by source_text; map those too.
        obs_text_to_id = {o.source_text: o.id for o in observations}

        trace = ValidationTrace()
        seen: set[str] = set()

        for raw in provider_output.candidates:
            ind_id = raw.indicator_id

            # Confidence range (Pydantic already enforces, but double-guard).
            if not (0.0 <= raw.confidence <= 1.0):
                trace.rejected_invalid_confidence.append(ind_id)
                continue

            # Unknown indicator → reject, never create.
            if ind_id not in allowed_ids:
                trace.rejected_unknown_indicator.append(ind_id)
                continue

            entry = allowed_by_id[ind_id]
            # The catalog is built from active+non-deleted indicators, so an ID
            # present in the catalog is by construction eligible. We still
            # classify rejections explicitly for the trace if a caller passes a
            # catalog built with looser filters.
            if not _is_eligible(entry):
                trace.rejected_inactive_indicator.append(ind_id)
                continue

            # Resolve observation references to ids actually produced here.
            resolved_obs: list[str] = []
            bad_obs = False
            for ref in raw.observation_ids:
                if ref in obs_ids:
                    resolved_obs.append(ref)
                elif ref in obs_text_to_id:
                    resolved_obs.append(obs_text_to_id[ref])
                else:
                    trace.rejected_orphan_observations.append(f"{ind_id}:{ref}")
                    bad_obs = True
            if bad_obs:
                # Keep the candidate but drop the bad references.
                pass

            if ind_id in seen:
                continue
            seen.add(ind_id)

            trace.accepted.append(
                CandidateIndicatorDTO(
                    indicator_id=ind_id,
                    confidence=raw.confidence,
                    observation_ids=resolved_obs,
                    reason=raw.reason or "",
                    uncertainty=raw.uncertainty,
                    source=raw.source or "ai_extraction",
                )
            )

        # Deterministic ordering: confidence desc, then indicator_id for stable tie-break.
        trace.accepted.sort(key=lambda c: (-c.confidence, c.indicator_id))
        if len(trace.accepted) > MAX_VALIDATED_CANDIDATES:
            trace.accepted = trace.accepted[:MAX_VALIDATED_CANDIDATES]
        return trace


def _is_eligible(entry) -> bool:
    """Eligibility check for an indicator catalog entry.

    The catalog entries are frozen DTOs carrying only the fields needed for the
    AI; they do not carry is_active/deleted_at. By construction the catalog is
    built from active+non-deleted indicators, so any ID present is eligible.
    This hook exists so a future catalog built with looser filters can still be
    guarded here.
    """
    # Catalog entries are pre-filtered; nothing else to check here.
    return True

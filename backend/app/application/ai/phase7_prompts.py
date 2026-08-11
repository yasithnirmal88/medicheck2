"""Phase 7 — Versioned prompt for personalized risk communication.

Extends Phase 1/2 explanation with multilingual + health-literacy awareness.
The safety intent is unchanged: the AI is an EXPLANATION layer only. It must
not diagnose, score, set severity, create recommendations, invent evidence,
or introduce clinical facts not present in the supplied deterministic context.

Phase 7 additions:
- Multilingual: explanations may be produced in EN/SI/TA. Translation must
  never change clinical meaning (possible ≠ confirmed, risk ≠ diagnosis).
- Health literacy: Simple / Standard / Detailed complexity. The deterministic
  result is identical at every level; only communication changes.
- Source transparency: every explanation cites the deterministic finding,
  contributing answers, knowledge-graph relationship, and evidence ids.
- AI transparency notice: the patient is told AI explains, not decides.
"""

from __future__ import annotations

#: Phase 7 prompt version. Bumped from Phase 2 ("2.0").
PHASE7_PROMPT_VERSION = "3.0-personalized"

#: Standard AI transparency notice text (patient-facing). The deterministic
#: engine is the clinical authority; AI only explains.
AI_TRANSPARENCY_NOTICE = (
    "Your clinical assessment was calculated by MediCheck's deterministic "
    "clinical decision engine. AI was used only to explain and communicate "
    "the results. AI did not diagnose a disease, calculate your clinical "
    "score, determine severity, create your recommendations, or modify your "
    "assessment."
)

#: SDG 3.4 disclaimer — supports earlier identification of risk indicators,
#: does not prevent disease.
SDG_3_4_DISCLAIMER = (
    "This assessment supports earlier identification of risk indicators "
    "associated with non-communicable diseases (SDG 3.4). It does not "
    "prevent disease and is not a diagnosis."
)

"""Phase 7 — Personalized, multilingual, literacy-aware explanation provider.

Extends the Phase 1 ``StubExplanationProvider`` with:
- **Language awareness** (EN/SI/TA): the same deterministic result produces
  equivalent explanations across languages. Translation never converts
  "possible" → "confirmed", "monitor" → "urgent", or "risk indicator" →
  "diagnosis".
- **Health-literacy levels** (Simple / Standard / Detailed): the deterministic
  result is identical at every level; only communication complexity changes.
- **Source breakdown**: every finding cites the deterministic finding,
  contributing answer refs, knowledge-graph relationship, evidence ids, and
  the trace_id.
- **AI transparency notice**: the patient is told AI explains, not decides.

This is a deterministic local provider — no network calls, no invented
entities. It builds the explanation strictly from the supplied context.
"""

from __future__ import annotations

import json
from typing import Any

from app.application.ai.phase7_prompts import (
    AI_TRANSPARENCY_NOTICE,
    PHASE7_PROMPT_VERSION,
    SDG_3_4_DISCLAIMER,
)
from app.application.dtos.ai_dtos import (
    LiteracyLevel,
    ReportExplanationContext,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Multilingual phrase tables. The SAME clinical concept is expressed in three
# languages. Critical: none of these translations upgrade certainty.
# possible → confirmed, monitor → urgent, risk → diagnosis are FORBIDDEN.
# ---------------------------------------------------------------------------

_PHRASES: dict[str, dict[str, str]] = {
    "assessment_measured": {
        "en": "Your assessment measured several health indicators across your body systems.",
        "si": "ඔබගේ ඇගයීම ඔබගේ ශරීර පද්ධති හරහා සෞඛ්‍ය දර්ශක කිහිපයක් මැනිණි.",
        "ta": "உங்கள் மதிப்பீடு உங்கள் உடல் அமைப்புகள் குறுக்கே பல சுகாதார குறிகாட்டிகளை அளந்தது.",
    },
    "not_diagnosis": {
        "en": "These are assessment signals, not confirmed diagnoses.",
        "si": "මේවා ඇගයීම් සංඥා වන අතර තහවරු කළ රෝග විනිශ්චය නොවේ.",
        "ta": "இவை மதிப்பீட்டு சைகைகளே, உறுதிப்படுத்தப்பட்ட நோய் கண்டறிதல்கள் அல்ல.",
    },
    "possible_condition": {
        "en": "Possible condition considered by the engine",
        "si": "යන්ත්‍රය විසින් සැලකිල්ලට ගත් හැකි තත්ත්වයක්",
        "ta": "எந்திரம் கருத்தில் கொண்ட சாத்தியமான நிலை",
    },
    "risk_indicator": {
        "en": "Risk indicator",
        "si": "අවදානම් දර්ශකය",
        "ta": "ஆபத்து குறிகாட்டி",
    },
    "finding_requiring_attention": {
        "en": "Finding requiring attention",
        "si": "අවධානය අවශ්‍ය සොයාගැනීමක්",
        "ta": "கவனம் தேவையான கண்டுபிடிப்பு",
    },
    "no_evidence": {
        "en": "No supporting evidence was available from the MediCheck evidence repository for this explanation.",
        "si": "මෙම පැහැදිලි කිරීම සඳහා MediCheck සාක්ෂි ගබඩාවෙන් සහාය සාක්ෂි ලබා ගත නොහැකි විය.",
        "ta": "இந்த விளக்கத்திற்கான MediCheck சான்று களஞ்சியத்திலிருந்து ஆதரவு சான்று கிடைக்கவில்லை.",
    },
    "why_asked_prefix": {
        "en": "This question was included because",
        "si": "මෙම ප්‍රශ්නය ඇතුළත් කළ ඇත්තේ මන්ද",
        "ta": "இந்தக் கேள்வி சேர்க்கப்பட்டதற்கு காரணம்",
    },
    "can_be_relevant": {
        "en": "can be relevant when assessing certain health indicators.",
        "si": "යම් සෞඛ්‍ය දර්ශක ඇගයීමේදී අදාළ විය හැක.",
        "ta": "சில சுகாதார குறிகாட்டிகளை மதிப்பிடும்போது தொடர்புடையதாக இருக்கலாம்.",
    },
}


def _t(key: str, language: str) -> str:
    """Look up a localized phrase. Falls back to English if the language
    is not available — never falls back to an invented translation."""
    lang = language if language in ("en", "si", "ta") else "en"
    return _PHRASES.get(key, {}).get(lang, _PHRASES.get(key, {}).get("en", key))


class PersonalizedExplanationProvider:
    """Deterministic local provider for Phase 7.

    Builds a valid explanation JSON strictly from the supplied context,
    adapted to the requested language and literacy level. Never calls a
    network service and never invents entities.
    """

    name = "personalized-stub"
    prompt_version = PHASE7_PROMPT_VERSION

    async def explain(self, context: ReportExplanationContext) -> str:
        try:
            lang = context.language or "en"
            level = context.literacy_level or LiteracyLevel.STANDARD

            evidence_by_indicator: dict[str, list[Any]] = {}
            for ev in context.evidence:
                if ev.linked_entity_type == "indicator":
                    evidence_by_indicator.setdefault(
                        ev.linked_entity_id, []
                    ).append(ev)

            evidence_by_rec: dict[str, list[Any]] = {}
            for ev in context.evidence:
                if ev.linked_entity_type == "recommendation":
                    evidence_by_rec.setdefault(
                        ev.linked_entity_id, []
                    ).append(ev)

            body_names = [
                b.name or b.body_system_id or "body system"
                for b in context.body_systems
            ]
            body_summary = ", ".join(body_names) or _t(
                "no_body_systems", lang
            ) if body_names else "no specific body systems flagged"

            cond_names = ", ".join(
                c.name for c in context.possible_conditions
            ) or "none"

            n_findings = len(context.activated_indicators)

            # --- Summary (literacy-adapted) ---
            if level == LiteracyLevel.SIMPLE:
                summary = _simple_summary(lang, n_findings, body_names)
            elif level == LiteracyLevel.DETAILED:
                summary = _detailed_summary(
                    lang,
                    n_findings,
                    body_summary,
                    cond_names,
                    context,
                )
            else:
                summary = _standard_summary(
                    lang, n_findings, body_summary, cond_names
                )

            # --- Key findings ---
            findings = []
            source_breakdown = []
            for ind in context.activated_indicators:
                linked = evidence_by_indicator.get(ind.id, [])
                finding_text = _indicator_explanation(
                    ind, lang, level, has_evidence=bool(linked)
                )
                findings.append(
                    {
                        "title": ind.name or _t("risk_indicator", lang),
                        "explanation": finding_text,
                        "source_indicator_ids": [ind.id],
                        "evidence_ids": [ev.id for ev in linked],
                    }
                )
                source_breakdown.append(
                    {
                        "clinical_finding": ind.name or ind.id,
                        "contributing_answer_refs": [],
                        "knowledge_graph_relationship": (
                            "Indicator → Possible Condition"
                            if context.possible_conditions
                            else "Indicator (activated)"
                        ),
                        "evidence_ids": [ev.id for ev in linked],
                        "deterministic_score": ind.score,
                        "trace_id": context.trace_id,
                    }
                )

            # --- Recommendation explanations ---
            rec_exps = []
            for r in context.recommendations:
                linked = evidence_by_rec.get(r.id, [])
                rec_exps.append(
                    {
                        "recommendation_id": r.id,
                        "explanation": _recommendation_explanation(
                            r, lang, level, has_evidence=bool(linked)
                        ),
                        "evidence_ids": [ev.id for ev in linked],
                    }
                )

            # --- Severity explanation ---
            severity_text = _severity_explanation(
                context.severity, lang, level
            )

            # --- Evidence notes ---
            evidence_notes: list[str] = []
            if context.evidence_available and context.evidence:
                for ev in context.evidence[:5]:
                    note = ev.title
                    if ev.evidence_level:
                        note += f" (evidence level {ev.evidence_level})"
                    if ev.source:
                        note += f" — {ev.source}"
                    evidence_notes.append(note)
            else:
                evidence_notes.append(_t("no_evidence", lang))

            limitations = _limitations(lang, level)
            disclaimer = _disclaimer(lang)

            payload: dict[str, Any] = {
                "summary": summary,
                "key_findings": findings,
                "severity_explanation": severity_text,
                "recommendation_explanations": rec_exps,
                "evidence_notes": evidence_notes,
                "limitations": limitations,
                "disclaimer": disclaimer,
                "transparency_notice": AI_TRANSPARENCY_NOTICE,
                "source_breakdown": source_breakdown,
                "language": lang,
                "literacy_level": level.value,
                "prompt_version": self.prompt_version,
            }
            return json.dumps(payload)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("personalized explanation provider failed: %s", exc)
            from app.application.ai.provider import AIProviderError

            raise AIProviderError("personalized provider failure") from exc


# ---------------------------------------------------------------------------
# Literacy-level-adapted text generators
# ---------------------------------------------------------------------------


def _simple_summary(lang: str, n_findings: int, body_names: list[str]) -> str:
    if lang == "si":
        base = "ඔබගේ පිළවිතුරු කිහිපයක් අවධානය අවශ්‍ය විය හැකි සලකුණු පෙන්වයි. මෙයින් අදහස් වන්නේ ඔට රෝගයක් ඇති බව නොවේ."
    elif lang == "ta":
        base = "உங்கள் பதில்கள் சில அடையாளங்களைக் காட்டுகின்றன, அவை கவனம் தேவைப்படலாம். இதன் பொருள் நீங்கள் நோயால் பாதிக்கப்பட்டுள்ளீர்கள் என்பது அல்ல."
    else:
        base = (
            "Your answers showed some signs that may need more attention. "
            "This does not mean you have a disease."
        )
    if n_findings > 0 and body_names:
        if lang == "en":
            base += f" The assessment looked at {len(body_names)} area(s) of your health."
    return base


def _standard_summary(
    lang: str, n_findings: int, body_summary: str, cond_names: str
) -> str:
    if lang == "si":
        return (
            f"ඔබගේ ඇගයීම {n_findings} සොයාගැනීම් හඳුනාගත්තා: {body_summary}. "
            f"යන්ත්‍රය විසින් සලකා බැලූ හැකි තත්ත්ව: {cond_names}. "
            "මේවා ඇගයීම් සංඥා වන අතර තහවරු කළ රෝග විනිශ්චය නොවේ."
        )
    if lang == "ta":
        return (
            f"உங்கள் மதிப்பீடு {n_findings} கண்டுபிடிப்புகளை அடையாளம் கண்டது: {body_summary}. "
            f"எந்திரம் கருத்தில் கொண்ட சாத்தியமான நிலைகள்: {cond_names}. "
            "இவை மதிப்பீட்டு சைகைகளே, உறுதிப்படுத்தப்பட்ட நோய் கண்டறிதல்கள் அல்ல."
        )
    return (
        f"Your assessment flagged {n_findings} finding(s) across: {body_summary}. "
        f"Possible condition(s) considered by the engine: {cond_names}. "
        "These are assessment signals, not confirmed diagnoses."
    )


def _detailed_summary(
    lang: str,
    n_findings: int,
    body_summary: str,
    cond_names: str,
    context: ReportExplanationContext,
) -> str:
    standard = _standard_summary(lang, n_findings, body_summary, cond_names)
    n_recs = len(context.recommendations)
    n_ev = len(context.evidence)
    if lang == "en":
        detail = (
            f" {n_recs} recommendation(s) were generated by the deterministic engine. "
            f"{n_ev} evidence record(s) were retrieved for citation. "
            f"Trace ID: {context.trace_id or 'N/A'}. "
        )
    elif lang == "si":
        detail = (
            f" තීරණාත්මක යන්ත්‍රය විසින් {n_recs} නිර්දේශ නිපදවන ලදී. "
            f"{n_ev} සාක්ෂි වාර්තා උපුටා ගන්නා ලදී. "
            f"ලුහුඩු හැඳුනුම්කාරකය: {context.trace_id or 'N/A'}."
        )
    else:
        detail = (
            f" தீர்மானகருவி எந்திரம் {n_recs} பரிந்துரைகளை உருவாக்கியது. "
            f"{n_ev} சான்று பதிவுகள் மீட்கப்பட்டன. "
            f"கண்காணிப்பு அடையாளம்: {context.trace_id or 'N/A'}."
        )
    return standard + detail + (" " + SDG_3_4_DISCLAIMER if lang == "en" else "")


def _indicator_explanation(
    ind: Any,
    lang: str,
    level: LiteracyLevel,
    has_evidence: bool = False,
) -> str:
    name = ind.name or "This finding"
    if level == LiteracyLevel.SIMPLE:
        if lang == "si":
            base = f"{name} යනු ඔබගේ පිළවිතුරු මත පදනම් වූ සලකුණකි. එය රෝගයක් නොවේ."
        elif lang == "ta":
            base = f"{name} என்பது உங்கள் பதில்களின் அடிப்படையிலான ஒரு அடையாளம். அது நோய் அல்ல."
        else:
            base = f"{name} is a sign based on your answers. It is not a disease."
        return base

    parts = [name]
    if ind.severity:
        if lang == "si":
            parts.append(f"{ind.severity} බරපතරතාවයක් ඇත")
        elif lang == "ta":
            parts.append(f"{ind.severity} தீவிரத்தன்மை கொண்டது")
        else:
            parts.append(f"is rated {ind.severity} severity")
    else:
        if lang == "si":
            parts.append("ඇගයීම මගින් හඳුනාගන්නා ලදී")
        elif lang == "ta":
            parts.append("மதிப்பீட்டால் அடையாளம் காணப்பட்டது")
        else:
            parts.append("was flagged by the assessment")
    if ind.evidence_strength and level == LiteracyLevel.DETAILED:
        parts.append(f"(evidence strength {ind.evidence_strength})")

    if lang == "si":
        base = " ".join(parts) + ". එය ඔබගේ පිළවිතුරු වලින් ලැබුණු සංඥාවකි, තහවරු කළ තත්ත්වයක් නොවේ."
    elif lang == "ta":
        base = " ".join(parts) + ". இது உங்கள் பதில்களிலிருந்து வந்த சைகை, உறுதிப்படுத்தப்பட்ட நிலை அல்ல."
    else:
        base = (
            " ".join(parts)
            + ". It is a signal from your answers, not a confirmed condition."
        )
    if has_evidence:
        if lang == "si":
            base += " පහත MediCheck සාක්ෂි ගබඩාවෙන් ලැබුණු සහාය සාක්ෂි උපුටා දක්වා ඇත."
        elif lang == "ta":
            base += " கீழே MediCheck சான்று களஞ்சியத்திலிருந்து ஆதரவு சான்று மேற்கோளிடப்பட்டுள்ளது."
        else:
            base += " Supporting evidence from the MediCheck evidence repository is cited below."
    return base


def _recommendation_explanation(
    rec: Any,
    lang: str,
    level: LiteracyLevel,
    has_evidence: bool = False,
) -> str:
    text = rec.text or rec.title or "Recommended follow-up."
    if level == LiteracyLevel.SIMPLE:
        if lang == "si":
            return f"නිර්දේශය: {text}"
        elif lang == "ta":
            return f"பரிந்துரை: {text}"
        return f"Recommendation: {text}"
    if lang == "si":
        base = text + (" මෙම නිර්දේශය MediCheck සාක්ෂි මගින් සහාය දක්වයි." if has_evidence else "")
    elif lang == "ta":
        base = text + (" இந்தப் பரிந்துரை MediCheck சான்றுகளால் ஆதரிக்கப்படுகிறது." if has_evidence else "")
    else:
        base = text + (
            " This recommendation is supported by supplied MediCheck evidence."
            if has_evidence
            else ""
        )
    return base


def _severity_explanation(
    severity: str | None, lang: str, level: LiteracyLevel
) -> str:
    if not severity:
        if lang == "si":
            return "මෙම වාර්තාවට මුළලු බරපතරතා කාණ්ඩයක් ලබා දී නොමැත."
        elif lang == "ta":
            return "இந்த அறிக்கைக்கு ஒட்டுமொத்த தீவிரத்தன்மை வகை வழங்கப்படவில்லை."
        return "No overall severity category was assigned to this report."
    table_en = {
        "Normal": "Findings are within normal range.",
        "Monitor": "Findings are worth monitoring over time.",
        "Needs Attention": "Findings need attention and possible follow-up.",
        "Recommend Screening": "The assessment suggests screening may be appropriate.",
        "Urgent Medical Review": "The assessment suggests urgent medical review.",
    }
    if lang == "en" or lang not in ("si", "ta"):
        return table_en.get(
            severity,
            f"The reported severity category is '{severity}'. It is an assessment label, not a diagnosis.",
        )
    # For si/ta, we keep the severity label in English (it's a deterministic
    # category) but explain in the local language that it is an assessment
    # label, not a diagnosis.
    if lang == "si":
        return f"බරපතරතා කාණ්ඩය: {severity}. එය ඇගයීම් ලේබලයකි, රෝග විනිශ්චයක් නොවේ."
    return f"தீவிரத்தன்மை வகை: {severity}. அது மதிப்பீட்டு லேபிள், நோய் கண்டறிதல் அல்ல."


def _limitations(lang: str, level: LiteracyLevel) -> str:
    if level == LiteracyLevel.SIMPLE:
        if lang == "si":
            return "මෙම පැහැදිලි කිරීම ඔබට රෝගයක් ඇති බව නොකියයි. සැලකිල්ලක් අවශ්‍ය නම් වෛද්‍යවරයෙකු හමුවීම වඩාත් සුදුසුය."
        elif lang == "ta":
            return "இந்த விளக்கம் உங்களுக்கு நோய் உள்ளது எனச் சொல்லாது. கவலை இருந்தால் மருத்துவரைச் சந்திப்பது நல்லது."
        return "This explanation does not mean you have a disease. If concerned, see a clinician."
    if lang == "si":
        return (
            "මෙම පැහැදිලි කිරීම තීරණාත්මක ඇගයීම විසින් සොයාගත් දෑ විස්තර කරයි. "
            "එය විනිශ්චයක් නොවන අතර යුතුකම් ඇති වෛද්‍යවරයෙකු විසින් ඇගයීමක් ආදේශනය නොකරයි."
        )
    if lang == "ta":
        return (
            "இந்த விளக்கம் தீர்மானகருவி மதிப்பீடு கண்டுபிடித்தவற்றை விவரிக்கிறது. "
            "இது ஒரு நோய் கண்டறிதல் அல்ல, தகுதியுள்ள மருத்துவரின் மதிப்பீட்டை மாற்றாது."
        )
    return (
        "This explanation describes what the deterministic assessment found. "
        "It is not a diagnosis and does not replace evaluation by a qualified clinician."
    )


def _disclaimer(lang: str) -> str:
    if lang == "si":
        return (
            "මෙම AI මගින් නිපදවන ලද පැහැදිලි කිරීම ඔබගේ MediCheck ඇගයීම මත පදනම් වී ඇත. "
            "එය විනිශ්චයක් සඑරයි නොවේ. යටින් ඇති ඇගයීම තීරණාත්මක වෛද්‍ය යන්ත්‍රය මගින් නිපදවයි."
        )
    if lang == "ta":
        return (
            "இந்த AI உருவாக்கிய விளக்கம் உங்கள் MediCheck மதிப்பீட்டின் அடிப்படையில் அமைந்தது. "
            "இது நோய் கண்டறிதல் அல்ல. அடிப்படை மதிப்பீடு தீர்மானகருவி மருத்துவ எந்திரத்தால் உருவாக்கப்படுகிறது."
        )
    return (
        "This AI-generated explanation is based on your MediCheck assessment "
        "and does not constitute a diagnosis. The underlying assessment is "
        "generated by the deterministic clinical engine."
    )

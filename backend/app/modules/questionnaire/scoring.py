from __future__ import annotations

from typing import Any

from app.domain.value_objects.risk_weight import RiskWeight


class ScoringEngine:
    def __init__(self) -> None:
        self._weights: dict[str, RiskWeight] = {}

    def register_weight(
        self, code: str, value: float, label: str = "", severity: str = "none"
    ) -> None:
        self._weights[code] = RiskWeight(value=value, label=label, severity=severity)

    def calculate_option_score(self, score_value: float) -> float:
        return score_value

    def calculate_group_score(
        self,
        answers: list[dict[str, Any]],
        scoring_weights: dict[str, float],
    ) -> dict[str, Any]:
        total_score = 0.0
        max_possible = 0.0
        answer_details = []

        for answer in answers:
            question_id = answer.get("question_id", "")
            weight = scoring_weights.get(question_id, 1.0)
            score = answer.get("score_value", 0.0)
            weighted_score = score * weight
            total_score += weighted_score
            max_possible += weight

            answer_details.append(
                {
                    "question_id": question_id,
                    "question_code": answer.get("question_code", ""),
                    "score": score,
                    "weight": weight,
                    "weighted_score": weighted_score,
                }
            )

        percentage = (total_score / max_possible * 100) if max_possible > 0 else 0.0
        return {
            "total_score": total_score,
            "max_possible": max_possible,
            "percentage": round(percentage, 2),
            "answer_details": answer_details,
        }

    def calculate_body_system_score(
        self,
        group_scores: dict[str, dict[str, Any]],
        system_scoring_weight: float,
    ) -> dict[str, Any]:
        total_score = 0.0
        total_max = 0.0

        for _group_id, score_data in group_scores.items():
            total_score += score_data.get("total_score", 0.0) * system_scoring_weight
            total_max += score_data.get("max_possible", 0.0) * system_scoring_weight

        percentage = (total_score / total_max * 100) if total_max > 0 else 0.0
        severity = self._determine_severity(percentage)

        return {
            "total_score": round(total_score, 2),
            "max_possible": round(total_max, 2),
            "percentage": round(percentage, 2),
            "severity": severity,
            "group_scores": group_scores,
        }

    def calculate_overall_score(
        self,
        system_scores: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        total_score = 0.0
        total_max = 0.0
        system_details = []

        for system_code, score_data in system_scores.items():
            total_score += score_data.get("total_score", 0.0)
            total_max += score_data.get("max_possible", 0.0)
            system_details.append(
                {
                    "system_code": system_code,
                    "score": score_data.get("total_score", 0.0),
                    "percentage": score_data.get("percentage", 0.0),
                    "severity": score_data.get("severity", "none"),
                }
            )

        overall_percentage = (total_score / total_max * 100) if total_max > 0 else 0.0
        overall_severity = self._determine_severity(overall_percentage)

        return {
            "overall_score": round(total_score, 2),
            "overall_percentage": round(overall_percentage, 2),
            "overall_severity": overall_severity,
            "system_details": system_details,
        }

    def _determine_severity(self, percentage: float) -> str:
        if percentage >= 80:
            return "critical"
        if percentage >= 60:
            return "severe"
        if percentage >= 40:
            return "moderate"
        if percentage >= 20:
            return "mild"
        return "none"

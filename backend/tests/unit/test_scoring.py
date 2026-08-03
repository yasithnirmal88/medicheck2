from __future__ import annotations

from app.modules.questionnaire.scoring import ScoringEngine


class TestScoringEngine:
    def setup_method(self) -> None:
        self.se = ScoringEngine()

    def test_calculate_option_score(self) -> None:
        assert self.se.calculate_option_score(0.0) == 0.0
        assert self.se.calculate_option_score(2.5) == 2.5
        assert self.se.calculate_option_score(-1.0) == -1.0

    def test_register_weight(self) -> None:
        self.se.register_weight("RISK_HIGH", 3.0, "High Risk", "severe")
        assert "RISK_HIGH" in self.se._weights
        assert self.se._weights["RISK_HIGH"].value == 3.0
        assert self.se._weights["RISK_HIGH"].severity == "severe"

    def test_calculate_group_score_single_answer(self) -> None:
        result = self.se.calculate_group_score(
            [{"question_id": "q1", "question_code": "BP_SYS", "score_value": 2.0}],
            {"q1": 1.0},
        )
        assert result["total_score"] == 2.0
        assert result["max_possible"] == 1.0
        assert result["percentage"] == 200.0
        assert len(result["answer_details"]) == 1

    def test_calculate_group_score_multiple_answers(self) -> None:
        answers = [
            {"question_id": "q1", "question_code": "BP_SYS", "score_value": 2.0},
            {"question_id": "q2", "question_code": "BP_DIA", "score_value": 1.0},
            {"question_id": "q3", "question_code": "HR", "score_value": 0.0},
        ]
        weights = {"q1": 1.5, "q2": 1.0, "q3": 0.5}
        result = self.se.calculate_group_score(answers, weights)
        expected_total = 2.0 * 1.5 + 1.0 * 1.0 + 0.0 * 0.5
        expected_max = 1.5 + 1.0 + 0.5
        assert result["total_score"] == expected_total
        assert result["max_possible"] == expected_max

    def test_calculate_group_score_no_positive_scores(self) -> None:
        result = self.se.calculate_group_score(
            [{"question_id": "q1", "question_code": "SAFE", "score_value": 0.0}],
            {"q1": 1.0},
        )
        assert result["total_score"] == 0.0
        assert result["max_possible"] == 1.0
        assert result["percentage"] == 0.0

    def test_calculate_group_score_empty_answers(self) -> None:
        result = self.se.calculate_group_score([], {})
        assert result["total_score"] == 0.0
        assert result["max_possible"] == 0.0
        assert result["percentage"] == 0.0

    def test_calculate_body_system_score(self) -> None:
        group_scores = {
            "g1": {"total_score": 10.0, "max_possible": 20.0},
            "g2": {"total_score": 5.0, "max_possible": 10.0},
        }
        result = self.se.calculate_body_system_score(group_scores, 1.0)
        assert result["total_score"] == 15.0
        assert result["max_possible"] == 30.0
        assert result["percentage"] == 50.0

    def test_body_system_score_with_weight(self) -> None:
        group_scores = {
            "g1": {"total_score": 10.0, "max_possible": 20.0},
        }
        result = self.se.calculate_body_system_score(group_scores, 0.5)
        assert result["total_score"] == 5.0
        assert result["max_possible"] == 10.0

    def test_body_system_score_no_groups(self) -> None:
        result = self.se.calculate_body_system_score({}, 1.0)
        assert result["total_score"] == 0.0
        assert result["max_possible"] == 0.0
        assert result["percentage"] == 0.0

    def test_calculate_overall_score(self) -> None:
        system_scores = {
            "CVS": {"total_score": 10.0, "max_possible": 20.0, "percentage": 50.0, "severity": "moderate"},
            "RESP": {"total_score": 2.0, "max_possible": 10.0, "percentage": 20.0, "severity": "mild"},
        }
        result = self.se.calculate_overall_score(system_scores)
        assert result["overall_score"] == 12.0
        assert result["overall_percentage"] == 40.0
        assert len(result["system_details"]) == 2

    def test_overall_score_empty(self) -> None:
        result = self.se.calculate_overall_score({})
        assert result["overall_score"] == 0.0
        assert result["overall_percentage"] == 0.0

    def test_negative_weights(self) -> None:
        answers = [{"question_id": "q1", "question_code": "NEG", "score_value": -1.0}]
        result = self.se.calculate_group_score(answers, {"q1": 1.0})
        assert result["total_score"] == -1.0
        assert result["max_possible"] == 1.0
        assert result["percentage"] == -100.0

    def test_zero_weights(self) -> None:
        answers = [{"question_id": "q1", "question_code": "ZERO", "score_value": 5.0}]
        result = self.se.calculate_group_score(answers, {"q1": 0.0})
        assert result["total_score"] == 0.0

    def test_maximum_weights(self) -> None:
        answers = [{"question_id": "q1", "question_code": "MAX", "score_value": 100.0}]
        result = self.se.calculate_group_score(answers, {"q1": 100.0})
        assert result["total_score"] == 10000.0
        assert result["max_possible"] == 100.0

    def test_severity_thresholds(self) -> None:
        assert self.se._determine_severity(0) == "none"
        assert self.se._determine_severity(10) == "none"
        assert self.se._determine_severity(20) == "mild"
        assert self.se._determine_severity(30) == "mild"
        assert self.se._determine_severity(40) == "moderate"
        assert self.se._determine_severity(50) == "moderate"
        assert self.se._determine_severity(60) == "severe"
        assert self.se._determine_severity(70) == "severe"
        assert self.se._determine_severity(80) == "critical"
        assert self.se._determine_severity(100) == "critical"

    def test_score_aggregation_multiple_conditions(self) -> None:
        group1 = self.se.calculate_group_score(
            [{"question_id": "q1", "question_code": "C1", "score_value": 2.0}],
            {"q1": 1.0},
        )
        group2 = self.se.calculate_group_score(
            [{"question_id": "q2", "question_code": "C2", "score_value": 3.0}],
            {"q2": 1.0},
        )
        system = self.se.calculate_body_system_score({"g1": group1, "g2": group2}, 1.0)
        overall = self.se.calculate_overall_score({"SYS": system})
        assert overall["overall_score"] == 5.0

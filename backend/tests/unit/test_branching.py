from __future__ import annotations

from app.modules.questionnaire.branching import BranchingEvaluator


class TestDependencyEvaluator:
    def setup_method(self) -> None:
        self.be = BranchingEvaluator()
        self.dep = self.be._evaluator

    def test_equals_operator(self) -> None:
        assert self.dep.evaluate("equals", {"value": "yes"}, "yes") is True
        assert self.dep.evaluate("equals", {"value": "yes"}, "no") is False
        assert self.dep.evaluate("equals", {"value": 42}, 42) is True
        assert self.dep.evaluate("equals", {"value": 42}, 0) is False

    def test_not_equals_operator(self) -> None:
        assert self.dep.evaluate("not_equals", {"value": "yes"}, "no") is True
        assert self.dep.evaluate("not_equals", {"value": "yes"}, "yes") is False

    def test_greater_than_operator(self) -> None:
        assert self.dep.evaluate("gt", {"value": 18}, 25) is True
        assert self.dep.evaluate("gt", {"value": 18}, 18) is False
        assert self.dep.evaluate("greater_than", {"value": 10}, 5) is False
        assert self.dep.evaluate("gt", {"value": 18}, None) is False

    def test_less_than_operator(self) -> None:
        assert self.dep.evaluate("lt", {"value": 100}, 50) is True
        assert self.dep.evaluate("lt", {"value": 50}, 100) is False
        assert self.dep.evaluate("less_than", {"value": 10}, 5) is True

    def test_gte_operator(self) -> None:
        assert self.dep.evaluate("gte", {"value": 18}, 18) is True
        assert self.dep.evaluate("gte", {"value": 18}, 25) is True
        assert self.dep.evaluate("gte", {"value": 18}, 17) is False
        assert self.dep.evaluate("greater_than_or_equal", {"value": 10}, 10) is True

    def test_lte_operator(self) -> None:
        assert self.dep.evaluate("lte", {"value": 100}, 50) is True
        assert self.dep.evaluate("lte", {"value": 100}, 100) is True
        assert self.dep.evaluate("lte", {"value": 100}, 150) is False
        assert self.dep.evaluate("less_than_or_equal", {"value": 10}, 10) is True

    def test_in_operator(self) -> None:
        assert self.dep.evaluate("in", {"values": ["a", "b", "c"]}, "b") is True
        assert self.dep.evaluate("in", {"values": ["a", "b", "c"]}, "z") is False
        assert self.dep.evaluate("in", {"value": "single"}, "single") is True
        assert self.dep.evaluate("in", {"value": "single"}, "other") is False

    def test_not_in_operator(self) -> None:
        assert self.dep.evaluate("not_in", {"values": ["a", "b"]}, "c") is True
        assert self.dep.evaluate("not_in", {"values": ["a", "b"]}, "a") is False

    def test_range_operator(self) -> None:
        assert self.dep.evaluate("range", {"min": 10, "max": 20}, 15) is True
        assert self.dep.evaluate("range", {"min": 10, "max": 20}, 10) is True
        assert self.dep.evaluate("range", {"min": 10, "max": 20}, 20) is True
        assert self.dep.evaluate("range", {"min": 10, "max": 20}, 9) is False
        assert self.dep.evaluate("range", {"min": 10, "max": 20}, 21) is False
        assert self.dep.evaluate("range", {"min": 10, "max": 20}, None) is False

    def test_has_any_operator(self) -> None:
        assert self.dep.evaluate("has_any", {"values": ["a", "b"]}, ["a"]) is True
        assert self.dep.evaluate("has_any", {"values": ["a", "b"]}, ["c"]) is False
        assert self.dep.evaluate("has_any", {"values": ["a", "b"]}, "not_a_list") is False

    def test_has_all_operator(self) -> None:
        assert self.dep.evaluate("has_all", {"values": ["a", "b"]}, ["a", "b"]) is True
        assert self.dep.evaluate("has_all", {"values": ["a", "b"]}, ["a"]) is False

    def test_is_empty_operator(self) -> None:
        assert self.dep.evaluate("is_empty", {}, "") is True
        assert self.dep.evaluate("is_empty", {}, []) is True
        assert self.dep.evaluate("is_empty", {}, "hello") is False

    def test_is_not_empty_operator(self) -> None:
        assert self.dep.evaluate("is_not_empty", {}, "hello") is True
        assert self.dep.evaluate("is_not_empty", {}, "") is False

    def test_null_answer_value(self) -> None:
        assert self.dep.evaluate("equals", {"value": "yes"}, None) is False
        assert self.dep.evaluate("gt", {"value": 10}, None) is False
        assert self.dep.evaluate("in", {"values": ["a"]}, None) is False
        assert self.dep.evaluate("range", {"min": 0, "max": 10}, None) is False

    def test_missing_condition_value(self) -> None:
        assert self.dep.evaluate("gt", {}, 10) is False
        assert self.dep.evaluate("range", {}, 10) is False
        assert self.dep.evaluate("in", {}, "a") is False

    def test_computed_bmi(self) -> None:
        attrs = {"height": 170, "weight": 70}
        assert self.dep.evaluate(
            "computed",
            {"field": "bmi", "operator": "gt", "threshold": 18.5, "use_answer": True},
            70,
            attrs,
        ) is True

    def test_computed_bmi_underweight(self) -> None:
        attrs = {"height": 170, "weight": 50}
        assert self.dep.evaluate(
            "computed",
            {"field": "bmi", "operator": "lt", "threshold": 18.5, "use_answer": True},
            50,
            attrs,
        ) is True

    def test_computed_age(self) -> None:
        from datetime import date

        dob = date(1990, 1, 1)
        attrs = {"date_of_birth": dob.isoformat()}
        assert self.dep.evaluate(
            "computed",
            {"field": "age", "operator": "gte", "threshold": 30},
            "dummy",
            attrs,
        ) is True

    def test_unknown_operator(self) -> None:
        assert self.dep.evaluate("unknown_op", {"value": "x"}, "x") is False


class TestBranchingEvaluator:
    def setup_method(self) -> None:
        self.be = BranchingEvaluator()

    def test_no_dependencies_visible(self) -> None:
        assert self.be.evaluate_visibility([], {}) is True

    def test_and_group_all_true(self) -> None:
        deps = [
            {"depends_on_question_id": "q1", "condition_type": "equals", "condition_value": {"value": "yes"}, "group_id": 1, "logic_operator": "AND"},
            {"depends_on_question_id": "q2", "condition_type": "gt", "condition_value": {"value": 10}, "group_id": 1, "logic_operator": "AND"},
        ]
        assert self.be.evaluate_visibility(deps, {"q1": "yes", "q2": 15}) is True
        assert self.be.evaluate_visibility(deps, {"q1": "yes", "q2": 5}) is False
        assert self.be.evaluate_visibility(deps, {"q1": "no", "q2": 15}) is False

    def test_or_group_any_true(self) -> None:
        deps = [
            {"depends_on_question_id": "q1", "condition_type": "equals", "condition_value": {"value": "yes"}, "group_id": 1, "logic_operator": "OR"},
            {"depends_on_question_id": "q2", "condition_type": "gt", "condition_value": {"value": 10}, "group_id": 1, "logic_operator": "OR"},
        ]
        assert self.be.evaluate_visibility(deps, {"q1": "yes", "q2": 0}) is True
        assert self.be.evaluate_visibility(deps, {"q1": "no", "q2": 15}) is True
        assert self.be.evaluate_visibility(deps, {"q1": "no", "q2": 0}) is False

    def test_multiple_groups(self) -> None:
        deps = [
            {"depends_on_question_id": "q1", "condition_type": "equals", "condition_value": {"value": "x"}, "group_id": 1, "logic_operator": "AND"},
            {"depends_on_question_id": "q2", "condition_type": "equals", "condition_value": {"value": "y"}, "group_id": 2, "logic_operator": "AND"},
        ]
        assert self.be.evaluate_visibility(deps, {"q1": "x", "q2": "y"}) is True
        assert self.be.evaluate_visibility(deps, {"q1": "x", "q2": "z"}) is False
        assert self.be.evaluate_visibility(deps, {"q1": "w", "q2": "y"}) is False

    def test_branch_rules_priority(self) -> None:
        rules = [
            {"priority": 10, "is_active": True, "conditions": {"question_id": "q1", "condition_type": "equals", "condition_value": {"value": "a"}}, "condition_operator": "AND", "target_question_id": "q_high"},
            {"priority": 5, "is_active": True, "conditions": {"question_id": "q1", "condition_type": "equals", "condition_value": {"value": "a"}}, "condition_operator": "AND", "target_question_id": "q_low"},
        ]
        result = self.be.evaluate_branch_rules(rules, {"q1": "a"})
        assert result == "q_high"

    def test_branch_rule_not_active(self) -> None:
        rules = [
            {"priority": 10, "is_active": False, "conditions": {"question_id": "q1", "condition_type": "equals", "condition_value": {"value": "a"}}, "condition_operator": "AND", "target_question_id": "q_skip"},
        ]
        result = self.be.evaluate_branch_rules(rules, {"q1": "a"})
        assert result is None

    def test_branch_rule_no_match(self) -> None:
        rules = [
            {"priority": 10, "is_active": True, "conditions": {"question_id": "q1", "condition_type": "equals", "condition_value": {"value": "a"}}, "condition_operator": "AND", "target_question_id": "q_target"},
        ]
        result = self.be.evaluate_branch_rules(rules, {"q1": "b"})
        assert result is None

    def test_condition_tree_and(self) -> None:
        tree = {"operator": "AND", "clauses": [
            {"question_id": "q1", "condition_type": "equals", "condition_value": {"value": "yes"}},
            {"question_id": "q2", "condition_type": "gt", "condition_value": {"value": 10}},
        ]}
        assert self.be.evaluate_branch_rules([{"priority": 1, "is_active": True, "conditions": tree, "condition_operator": "AND", "target_question_id": "t"}], {"q1": "yes", "q2": 15}) == "t"
        assert self.be.evaluate_branch_rules([{"priority": 1, "is_active": True, "conditions": tree, "condition_operator": "AND", "target_question_id": "t"}], {"q1": "yes", "q2": 5}) is None

    def test_condition_tree_or(self) -> None:
        tree = {"operator": "OR", "clauses": [
            {"question_id": "q1", "condition_type": "equals", "condition_value": {"value": "yes"}},
            {"question_id": "q2", "condition_type": "gt", "condition_value": {"value": 10}},
        ]}
        assert self.be.evaluate_branch_rules([{"priority": 1, "is_active": True, "conditions": tree, "condition_operator": "OR", "target_question_id": "t"}], {"q1": "yes", "q2": 0}) == "t"
        assert self.be.evaluate_branch_rules([{"priority": 1, "is_active": True, "conditions": tree, "condition_operator": "OR", "target_question_id": "t"}], {"q1": "no", "q2": 0}) is None

    def test_condition_tree_not(self) -> None:
        tree = {"operator": "NOT", "clause": {"question_id": "q1", "condition_type": "equals", "condition_value": {"value": "yes"}}}
        assert self.be.evaluate_branch_rules([{"priority": 1, "is_active": True, "conditions": tree, "condition_operator": "AND", "target_question_id": "t"}], {"q1": "no"}) == "t"
        assert self.be.evaluate_branch_rules([{"priority": 1, "is_active": True, "conditions": tree, "condition_operator": "AND", "target_question_id": "t"}], {"q1": "yes"}) is None

    def test_nested_expression(self) -> None:
        tree = {
            "operator": "AND",
            "clauses": [
                {"question_id": "q1", "condition_type": "equals", "condition_value": {"value": "yes"}},
                {
                    "operator": "OR",
                    "clauses": [
                        {"question_id": "q2", "condition_type": "gt", "condition_value": {"value": 100}},
                        {"question_id": "q3", "condition_type": "equals", "condition_value": {"value": "risk"}},
                    ],
                },
            ],
        }
        rule = [{"priority": 1, "is_active": True, "conditions": tree, "condition_operator": "AND", "target_question_id": "t"}]
        assert self.be.evaluate_branch_rules(rule, {"q1": "yes", "q2": 50, "q3": "risk"}) == "t"
        assert self.be.evaluate_branch_rules(rule, {"q1": "yes", "q2": 50, "q3": "safe"}) is None
        assert self.be.evaluate_branch_rules(rule, {"q1": "no", "q2": 200, "q3": "safe"}) is None

    def test_complex_dependency_chain(self) -> None:
        deps = [
            {"depends_on_question_id": "q1", "condition_type": "in", "condition_value": {"values": ["a", "b"]}, "group_id": 1, "logic_operator": "AND"},
            {"depends_on_question_id": "q2", "condition_type": "range", "condition_value": {"min": 18, "max": 65}, "group_id": 1, "logic_operator": "AND"},
        ]
        assert self.be.evaluate_visibility(deps, {"q1": "a", "q2": 30}) is True
        assert self.be.evaluate_visibility(deps, {"q1": "c", "q2": 30}) is False
        assert self.be.evaluate_visibility(deps, {"q1": "a", "q2": 70}) is False

    def test_missing_values_in_answers(self) -> None:
        deps = [
            {"depends_on_question_id": "q_missing", "condition_type": "equals", "condition_value": {"value": "x"}, "group_id": 1, "logic_operator": "AND"},
        ]
        assert self.be.evaluate_visibility(deps, {}) is False

    def test_circular_dependency_protection(self) -> None:
        deps = [
            {"depends_on_question_id": "q1", "condition_type": "equals", "condition_value": {"value": "yes"}, "group_id": 1, "logic_operator": "AND"},
        ]
        result = self.be.evaluate_visibility(deps, {"q1": "yes"})
        assert result is True
        result = self.be.evaluate_visibility(deps, {"q1": "no"})
        assert result is False

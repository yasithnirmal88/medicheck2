from __future__ import annotations

from typing import Any

from app.modules.questionnaire.dependency_evaluator import DependencyEvaluator


class BranchingEvaluator:
    def __init__(self) -> None:
        self._evaluator = DependencyEvaluator()

    def evaluate_visibility(
        self,
        dependencies: list[dict[str, Any]],
        answers_map: dict[str, Any],
        user_attributes: dict[str, Any] | None = None,
    ) -> bool:
        if not dependencies:
            return True

        groups: dict[int, list[dict[str, Any]]] = {}
        for dep in dependencies:
            gid = dep.get("group_id", 0)
            if gid not in groups:
                groups[gid] = []
            groups[gid].append(dep)

        results = []
        for gid in sorted(groups.keys()):
            group_deps = groups[gid]
            group_operator = (
                group_deps[0].get("logic_operator", "AND") if group_deps else "AND"
            )
            group_result = self._evaluate_group(
                group_deps, group_operator, answers_map, user_attributes
            )
            results.append(group_result)

        return all(results)

    def evaluate_branch_rules(
        self,
        rules: list[dict[str, Any]],
        answers_map: dict[str, Any],
        user_attributes: dict[str, Any] | None = None,
    ) -> str | None:
        for rule in sorted(rules, key=lambda r: r.get("priority", 0), reverse=True):
            if not rule.get("is_active", True):
                continue

            condition_operator = rule.get("condition_operator", "AND")
            conditions = rule.get("conditions", {})

            if self._evaluate_condition_tree(
                conditions, condition_operator, answers_map, user_attributes
            ):
                return rule.get("target_question_id")

        return None

    def _evaluate_group(
        self,
        deps: list[dict[str, Any]],
        operator: str,
        answers_map: dict[str, Any],
        user_attributes: dict[str, Any] | None = None,
    ) -> bool:
        results = []
        for dep in deps:
            depends_on = dep.get("depends_on_question_id", "")
            answer_value = answers_map.get(depends_on)
            condition_type = dep.get("condition_type", "equals")
            condition_value = dep.get("condition_value", {})
            result = self._evaluator.evaluate(
                condition_type, condition_value, answer_value, user_attributes
            )
            results.append(result)

        if operator == "OR":
            return any(results)
        return all(results)

    def _evaluate_condition_tree(
        self,
        node: dict[str, Any],
        default_operator: str,
        answers_map: dict[str, Any],
        user_attributes: dict[str, Any] | None = None,
    ) -> bool:
        if "operator" in node and node["operator"] in ("AND", "OR", "NOT"):
            op = node["operator"]
            if op == "NOT":
                clause = node.get("clause", node.get("conditions", {}))
                return not self._evaluate_condition_tree(
                    clause, default_operator, answers_map, user_attributes
                )

            clauses = node.get("clauses", node.get("conditions", []))
            results = [
                self._evaluate_condition_tree(
                    c, default_operator, answers_map, user_attributes
                )
                for c in clauses
            ]
            if op == "OR":
                return any(results)
            return all(results)

        question_id = node.get("question_id") or node.get("question")
        if not question_id:
            return True

        condition_type = node.get("condition_type") or node.get("operator", "equals")
        condition_value = node.get("condition_value") or node.get("value", {})
        answer_value = answers_map.get(question_id)

        return self._evaluator.evaluate(
            condition_type, condition_value, answer_value, user_attributes
        )

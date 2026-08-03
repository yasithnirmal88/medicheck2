from __future__ import annotations

import ast
import operator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


class RuleEngineService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def evaluate_condition(
        self, condition: dict[str, Any], context: dict[str, Any]
    ) -> bool:
        operator_type = condition.get("operator", "eq")
        field = condition.get("field", "")
        value = condition.get("value")
        field_value = context.get(field)

        if operator_type == "exists":
            return field_value is not None
        if operator_type == "not_exists":
            return field_value is None
        if operator_type == "in":
            return field_value in (value if isinstance(value, list) else [value])
        if operator_type == "not_in":
            return field_value not in (value if isinstance(value, list) else [value])
        if operator_type == "between":
            if isinstance(value, (list, tuple)) and len(value) == 2:
                return value[0] <= field_value <= value[1]
            return False
        if operator_type == "contains":
            return value in str(field_value) if field_value else False

        ops = {
            "eq": operator.eq,
            "ne": operator.ne,
            "gt": operator.gt,
            "gte": operator.ge,
            "lt": operator.lt,
            "lte": operator.le,
        }
        return ops.get(operator_type, operator.eq)(field_value, value)

    def evaluate_expression(
        self, expression: dict[str, Any], context: dict[str, Any]
    ) -> bool:
        expr_type = expression.get("type", "condition")

        if expr_type == "condition":
            return self.evaluate_condition(expression, context)

        if expr_type == "AND":
            conditions = expression.get("conditions", [])
            return all(self.evaluate_expression(c, context) for c in conditions)

        if expr_type == "OR":
            conditions = expression.get("conditions", [])
            return any(self.evaluate_expression(c, context) for c in conditions)

        if expr_type == "NOT":
            inner = expression.get("condition")
            if inner:
                return not self.evaluate_expression(inner, context)
            return True

        if expr_type == "IF_ELSE":
            if_cond = expression.get("if")
            then_expr = expression.get("then", True)
            else_expr = expression.get("else", True)
            if if_cond and self.evaluate_expression(if_cond, context):
                return self.evaluate_expression(then_expr, context)
            return self.evaluate_expression(else_expr, context)

        return True

    def compute_variable(
        self, variable: str, context: dict[str, Any]
    ) -> Any:
        if variable == "BMI":
            weight = context.get("weight_kg", 70)
            height_cm = context.get("height_cm", 170)
            if height_cm > 0:
                height_m = height_cm / 100
                return round(weight / (height_m * height_m), 1)
            return 0

        if variable == "AGE":
            return context.get("age", 30)

        if variable == "IS_MALE":
            return context.get("sex", "").lower() == "male"

        if variable == "SMOKES":
            return context.get("smoking", "").lower() in ("daily", "occasionally")

        return context.get(variable, 0)

    def evaluate_rule(
        self, rule: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        if condition := rule.get("condition"):
            condition_met = self.evaluate_expression(condition, context)
        else:
            condition_met = True

        if not condition_met:
            return {
                "matched": False,
                "action": None,
                "confidence": 0.0,
            }

        action = rule.get("action", {})
        confidence = action.get("confidence", 1.0)

        if computed := rule.get("computed_variables"):
            for var_name, expr in computed.items():
                context[var_name] = self._compute_expression(expr, context)

        return {
            "matched": True,
            "action": action,
            "confidence": confidence,
            "context": context,
        }

    def evaluate_ruleset(
        self, rules: list[dict[str, Any]], context: dict[str, Any]
    ) -> list[dict[str, Any]]:
        results = []
        for rule in sorted(rules, key=lambda r: r.get("priority", 5)):
            result = self.evaluate_rule(rule, context)
            results.append(result)
        return results

    def simulate(
        self, rules: list[dict[str, Any]], context: dict[str, Any]
    ) -> dict[str, Any]:
        matched_rules = []
        total_confidence = 0.0
        actions = []

        for rule in sorted(rules, key=lambda r: r.get("priority", 5)):
            result = self.evaluate_rule(rule, context)
            if result["matched"]:
                matched_rules.append(
                    {
                        "name": rule.get("name", "unnamed"),
                        "priority": rule.get("priority", 5),
                        "confidence": result["confidence"],
                    }
                )
                total_confidence += result["confidence"]
                if action := result.get("action"):
                    actions.append(action)

        return {
            "matched_rules": len(matched_rules),
            "rules": matched_rules,
            "total_confidence": round(total_confidence, 2),
            "actions": actions,
            "context_used": context,
        }

    def _compute_expression(
        self, expr: str, context: dict[str, Any]
    ) -> Any:
        try:
            tree = ast.parse(expr.strip(), mode="eval")
            return self._eval_node(tree.body, context)
        except Exception:
            return None

    def _eval_node(
        self, node: ast.AST, context: dict[str, Any]
    ) -> Any:
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            return self.compute_variable(node.id, context)
        if isinstance(node, ast.BinOp):
            left = self._eval_node(node.left, context)
            right = self._eval_node(node.right, context)
            ops = {
                ast.Add: operator.add,
                ast.Sub: operator.sub,
                ast.Mult: operator.mul,
                ast.Div: operator.truediv,
                ast.FloorDiv: operator.floordiv,
                ast.Mod: operator.mod,
                ast.Pow: operator.pow,
            }
            op_func = ops.get(type(node.op))
            if op_func:
                try:
                    return op_func(left, right)
                except Exception:
                    return 0
            return 0
        if isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand, context)
            if isinstance(node.op, ast.USub):
                return -operand
            if isinstance(node.op, ast.Not):
                return not operand
            return operand
        return 0

    def detect_conflicts(
        self, rules: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        conflicts = []
        for i, r1 in enumerate(rules):
            for j, r2 in enumerate(rules):
                if i >= j:
                    continue
                if r1.get("name") == r2.get("name"):
                    continue
                c1 = r1.get("condition", {})
                c2 = r2.get("condition", {})
                a1 = r1.get("action", {})
                a2 = r2.get("action", {})

                if c1 == c2 and a1 != a2:
                    conflicts.append(
                        {
                            "rule_1": r1.get("name", f"rule_{i}"),
                            "rule_2": r2.get("name", f"rule_{j}"),
                            "reason": "Same condition, different actions",
                            "priority_1": r1.get("priority", 5),
                            "priority_2": r2.get("priority", 5),
                        }
                    )
        return conflicts

    def detect_circular_dependencies(
        self, rules: list[dict[str, Any]]
    ) -> list[list[str]]:
        graph: dict[str, list[str]] = {}
        for rule in rules:
            name = rule.get("name", "unnamed")
            deps = []
            condition = rule.get("condition", {})
            self._extract_field_refs(condition, deps)
            graph[name] = deps

        cycles = []
        visited: set[str] = set()
        rec_stack: set[str] = set()

        def dfs(node: str, path: list[str]) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path)
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:] + [neighbor])
            path.pop()
            rec_stack.discard(node)

        for node in graph:
            if node not in visited:
                dfs(node, [])

        return cycles

    def _extract_field_refs(
        self, condition: dict[str, Any], refs: list[str]
    ) -> None:
        if not condition:
            return
        if field := condition.get("field"):
            if field not in refs:
                refs.append(field)
        for sub in condition.get("conditions", []):
            self._extract_field_refs(sub, refs)
        if inner := condition.get("condition"):
            self._extract_field_refs(inner, refs)

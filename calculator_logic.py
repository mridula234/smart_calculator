"""
calculator_logic.py
────────────────────
Pure math engine — no UI dependencies.
Handles expression building, evaluation and history.
"""

import math
from typing import List, Tuple


class CalculatorLogic:
    def __init__(self):
        self.expression: str = ""
        self.history: List[Tuple[str, str]] = []   # [(expr, result), ...]
        self._just_evaluated = False

    # ── Public API ───────────────────────────
    def press(self, key: str) -> None:
        """Process a single key press (digit, operator, C, DEL, =)."""
        if key == "C":
            self._clear()
        elif key == "DEL":
            self._delete()
        elif key == "=":
            self._evaluate()
        elif key in ("+", "-", "*", "/", "%"):
            self._append_operator(key)
        elif key == ".":
            self._append_dot()
        elif key.isdigit():
            self._append_digit(key)

    def set_expression(self, expr: str) -> None:
        """Directly set the expression (e.g. from voice/gesture input)."""
        self.expression = expr
        self._just_evaluated = False

    def evaluate_preview(self) -> str:
        """Return a live result string without committing to history."""
        if not self.expression:
            return "0"
        try:
            result = self._safe_eval(self.expression)
            return self._format(result)
        except Exception:
            return "..."

    # ── Internal helpers ─────────────────────
    def _clear(self):
        self.expression = ""
        self._just_evaluated = False

    def _delete(self):
        if self.expression:
            self.expression = self.expression[:-1]
        self._just_evaluated = False

    def _evaluate(self):
        if not self.expression:
            return
        try:
            result = self._safe_eval(self.expression)
            result_str = self._format(result)
            self.history.append((self.expression, result_str))
            self.expression = result_str
            self._just_evaluated = True
        except Exception:
            self.expression = "Error"
            self._just_evaluated = True

    def _append_operator(self, op: str):
        if self._just_evaluated:
            self._just_evaluated = False
        if not self.expression:
            if op == "-":           # allow leading minus
                self.expression = "-"
            return
        if self.expression[-1] in "+-*/%":
            self.expression = self.expression[:-1]
        self.expression += op

    def _append_dot(self):
        if self._just_evaluated:
            self.expression = "0"
            self._just_evaluated = False
        # Find the last number token
        tokens = self.expression.split(any_op := self.expression)
        last = ""
        for ch in reversed(self.expression):
            if ch in "+-*/":
                break
            last = ch + last
        if "." in last:
            return
        if not self.expression or self.expression[-1] in "+-*/":
            self.expression += "0"
        self.expression += "."

    def _append_digit(self, digit: str):
        if self._just_evaluated:
            self.expression = ""
            self._just_evaluated = False
        self.expression += digit

    @staticmethod
    def _safe_eval(expr: str) -> float:
        """
        Evaluate a math expression safely.
        Only digits and basic operators are allowed — no builtins exposed.
        """
        allowed = set("0123456789+-*/.%()")
        if not all(c in allowed for c in expr):
            raise ValueError("Invalid characters in expression")
        return float(eval(expr, {"__builtins__": {}}, {}))  # noqa: S307

    @staticmethod
    def _format(value: float) -> str:
        """Return a clean string representation of a float result."""
        if not math.isfinite(value):
            return "Error"
        rounded = round(value, 10)
        if rounded == int(rounded):
            return str(int(rounded))
        return str(rounded)

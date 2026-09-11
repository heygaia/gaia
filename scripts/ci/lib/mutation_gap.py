#!/usr/bin/env python3
"""Which of a module's PR-changed lines could a test have reached?

The mutation lane reports SKIP when mutmut found no mutant with a covering
test. That single message covered two facts that need opposite responses:

* the changed lines hold nothing a test could pin — imports, constants,
  docstrings, decorators, or lines inside a decorated function (mutmut 3.7
  never mutates those, verified in its file_mutation.py) — so silence is the
  right answer; or
* the changed lines are executable code inside a function and NO test reaches
  them — a real gap that used to pass the gate.

This prints the second kind, one line number per line, so mutation.sh can
fail on them and stay quiet on the first. Sharing the AST walk with the
matrix would couple two files edited for different reasons; the walk is small.

Usage: mutation_gap.py <module.py> '<[[start,end],...]>'
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
import sys


def _is_docstring(stmt: ast.stmt) -> bool:
    return (
        isinstance(stmt, ast.Expr)
        and isinstance(stmt.value, ast.Constant)
        and isinstance(stmt.value.value, str)
    )


def _statement_lines(body: list[ast.stmt]) -> set[int]:
    """Every source line occupied by an executable statement in ``body``.

    Nested undecorated defs contribute their own bodies; nested decorated
    defs contribute nothing, for the same reason top-level ones do not. The
    ``def`` line itself is not a statement a mutant can live on.
    """
    lines: set[int] = set()
    for stmt in body:
        if isinstance(stmt, ast.FunctionDef | ast.AsyncFunctionDef):
            if not stmt.decorator_list:
                lines |= _statement_lines(_body_after_docstring(stmt.body))
            continue
        if isinstance(stmt, ast.ClassDef):
            lines |= _statement_lines(stmt.body)
            continue
        if _is_docstring(stmt):
            continue
        lines.update(range(stmt.lineno, (stmt.end_lineno or stmt.lineno) + 1))
        for child in ast.iter_child_nodes(stmt):
            nested = getattr(child, "body", None)
            if isinstance(nested, list) and nested and isinstance(nested[0], ast.stmt):
                lines |= _statement_lines(nested)
            for attr in ("orelse", "finalbody", "handlers"):
                extra = getattr(child, attr, None) or getattr(stmt, attr, None)
                if isinstance(extra, list):
                    for item in extra:
                        if isinstance(item, ast.stmt):
                            lines |= _statement_lines([item])
                        elif isinstance(item, ast.ExceptHandler):
                            lines |= _statement_lines(item.body)
    return lines


def _body_after_docstring(body: list[ast.stmt]) -> list[ast.stmt]:
    return body[1:] if body and _is_docstring(body[0]) else body


def _function_lines(tree: ast.Module) -> set[int]:
    """Executable lines that sit inside some undecorated function or method."""
    lines: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and not node.decorator_list:
            lines |= _statement_lines(_body_after_docstring(node.body))
    return lines


def executable_changed_lines(source: str, ranges: list[list[int]]) -> list[int]:
    """Changed lines a mutant could have lived on and a test could have caught."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    reachable = _function_lines(tree)
    changed = {n for start, end in ranges for n in range(start, end + 1)}
    return sorted(reachable & changed)


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: mutation_gap.py <module.py> '<ranges-json>'", file=sys.stderr)
        return 2
    path, ranges_json = argv[1], argv[2]
    try:
        ranges = json.loads(ranges_json or "[]")
    except json.JSONDecodeError as exc:
        print(f"mutation_gap: bad ranges JSON: {exc}", file=sys.stderr)
        return 2
    for line in executable_changed_lines(Path(path).read_text(encoding="utf-8"), ranges):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

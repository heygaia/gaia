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


def _statement_lines(node: ast.AST) -> set[int]:
    """Every source line occupied by an executable statement under ``node``.

    Generic over the tree rather than special-casing ``orelse``/``handlers``:
    any ``ast.stmt`` reachable without crossing a nested ``def`` or ``class``
    counts, and a docstring does not. Nested defs are skipped here because the
    walk in ``_function_lines`` visits each undecorated one on its own — and a
    decorated one contributes nothing, for the same reason top-level ones do
    not. The ``def`` line itself is not a statement a mutant can live on.
    """
    lines: set[int] = set()
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            continue
        if isinstance(child, ast.stmt) and not _is_docstring(child):
            lines.update(range(child.lineno, (child.end_lineno or child.lineno) + 1))
        lines |= _statement_lines(child)
    return lines


def _function_lines(tree: ast.Module) -> set[int]:
    """Executable lines that sit inside some undecorated function or method."""
    lines: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and not node.decorator_list:
            lines |= _statement_lines(node)
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

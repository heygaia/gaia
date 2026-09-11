"""mutation_gap.py: the line between "nothing to test here" and "untested".

The lane printed one SKIP message for both, and on one PR that turned 10 real
gaps into 39 things to read — 29 of which were imports, constants and
deletions that no test could ever pin. Each case below is a shape from that
list, and the assertion is which lines the gate must (or must not) demand a
test for.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
_SPEC = importlib.util.spec_from_file_location(
    "mutation_gap", REPO_ROOT / "scripts" / "ci" / "lib" / "mutation_gap.py"
)
assert _SPEC is not None and _SPEC.loader is not None
gap = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(gap)

SOURCE = '''\
from app.x import y          # 1
CONSTANT = "value"           # 2
                             # 3
def plain(a: int) -> int:    # 4
    """Docstring."""         # 5
    if a > 0:                # 6
        return a * 2         # 7
    return -a                # 8
                             # 9
@decorated                   # 10
def endpoint() -> None:      # 11
    do_work()                # 12
                             # 13
class Thing:                 # 14
    field: int = 1           # 15
                             # 16
    def method(self) -> str: # 17
        return str(self)     # 18
'''


def _lines(ranges: list[list[int]]) -> list[int]:
    return gap.executable_changed_lines(SOURCE, ranges)


def test_imports_and_constants_are_not_a_gap() -> None:
    assert _lines([[1, 2]]) == []


def test_a_docstring_is_not_a_gap() -> None:
    assert _lines([[5, 5]]) == []


def test_executable_lines_inside_a_plain_function_are_a_gap() -> None:
    assert _lines([[4, 8]]) == [6, 7, 8]


def test_a_method_body_counts_but_the_class_field_does_not() -> None:
    assert _lines([[14, 18]]) == [18]


def test_a_decorated_function_is_never_a_gap() -> None:
    """mutmut 3.7 skips every decorated def, so demanding a test there asks
    for a kill that cannot happen."""
    assert _lines([[10, 12]]) == []


def test_the_def_line_itself_is_not_a_gap() -> None:
    assert _lines([[4, 4]]) == []


def test_only_lines_inside_the_ranges_are_reported() -> None:
    assert _lines([[7, 7]]) == [7]


def test_unparsable_source_reports_nothing_rather_than_crashing() -> None:
    assert gap.executable_changed_lines("def broken(:\n", [[1, 1]]) == []


def test_the_cli_prints_one_line_number_per_line(tmp_path: Path, capsys) -> None:
    module = tmp_path / "m.py"
    module.write_text(SOURCE)

    assert gap.main(["mutation_gap.py", str(module), "[[4,8]]"]) == 0
    assert capsys.readouterr().out.split() == ["6", "7", "8"]

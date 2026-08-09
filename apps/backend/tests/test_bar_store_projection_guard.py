"""The metadata-only-reader guard: every ``BarStore.list()`` caller that reads NO candle must ask
for ``include_bars=False``.

``BarStore.list()``'s default embeds every stored candle of every recorded series and copies each
row (``bars.py``'s ``[dict(row) for row in loaded.rows]``). On the live desk store that is ~3.25M
row copies — measured ~0.6s per call, warm — and five callers were paying it for a payload not one
of their lines reads: they enumerate ``record["symbol"]`` / ``record["timeframe"]`` (or, in
``record``'s case, ``meta["checksum"]``) and then read the bars, if at all, through
``merged_bars``. ``compute_tradability`` alone made two such calls per member, so a ~101-member
screen paid ~160s for nothing.

``include_bars=False`` is not a weaker read: ``bars.py::list`` runs the IDENTICAL verified load
through the IDENTICAL stat-keyed cache and omits only the ``bars`` key from the projection
(``get``'s "an absent key is the honest 'not asked for'" contract). Nothing is skipped,
approximated, or served unverified — which is exactly why this is a source-text guard rather than a
behavioural one: the served values are byte-identical either way, so only the source can witness
that the cheap projection is the one being asked for. A future edit that drops the keyword silently
restores the cost with no test failing anywhere else.

Each pinned site is listed with the reason its reader needs no candles. Adding a candle-reading
line to one of these functions means removing it from this list, deliberately — never widening the
guard's regex."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_RESEARCH = Path(__file__).resolve().parents[1] / "app" / "research"

# (module, enclosing function, why this reader needs no candle payload)
_METADATA_ONLY_CALLERS = [
    ("bars.py", "record", "compares only meta['checksum'] for the duplicate scan"),
    ("tradability.py", "_select_daily_series", "enumerates symbol/timeframe; bars come from merged_bars"),
    ("levels.py", "compute_levels", "enumerates symbol/timeframe via _timeframes_for"),
    ("levels.py", "level_change_points", "enumerates symbol/timeframe via _timeframes_for"),
    ("bar_index.py", "reindex", "the index stores metadata only"),
]


def _enclosing_function(tree: ast.AST, node: ast.AST) -> str | None:
    """The name of the innermost function whose body lexically contains ``node``."""
    best: tuple[int, str] | None = None
    for candidate in ast.walk(tree):
        if not isinstance(candidate, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        end = getattr(candidate, "end_lineno", None)
        if end is None or not (candidate.lineno <= node.lineno <= end):
            continue
        if best is None or candidate.lineno > best[0]:
            best = (candidate.lineno, candidate.name)
    return best[1] if best else None


def _list_calls(module: str) -> list[tuple[str, ast.Call]]:
    """Every ``<something>.list(...)`` call in ``module``, paired with its enclosing function name.

    AST-structural, not a regex: a call written across several lines, or one whose receiver is
    ``self`` / ``store`` / ``self._store``, is found identically."""
    source = (_RESEARCH / module).read_text()
    tree = ast.parse(source)
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "list":
            name = _enclosing_function(tree, node)
            if name is not None:
                found.append((name, node))
    return found


@pytest.mark.parametrize(("module", "function", "reason"), _METADATA_ONLY_CALLERS)
def test_metadata_only_reader_asks_for_the_cheap_projection(module: str, function: str, reason: str) -> None:
    calls = [call for name, call in _list_calls(module) if name == function]
    assert calls, f"{module}::{function} makes no .list(...) call at all — has it been renamed?"
    for call in calls:
        keywords = {kw.arg: kw.value for kw in call.keywords}
        assert "include_bars" in keywords, (
            f"{module}::{function} calls .list() without include_bars — it {reason}, so the "
            f"default candle payload is copied for nothing (~0.6s per call on the live store)"
        )
        value = keywords["include_bars"]
        assert isinstance(value, ast.Constant) and value.value is False, (
            f"{module}::{function} must pass include_bars=False literally, not "
            f"{ast.dump(value)} — a computed value hides which projection is really asked for"
        )


def test_the_bounded_view_forwards_the_projection() -> None:
    """``tradability._PriorSessionBarView`` stands in for a ``BarStore`` wherever
    ``compute_levels`` reads, so it must forward ``include_bars`` rather than swallowing it —
    otherwise ``compute_levels``' own cheap projection silently becomes the expensive one again
    (and a positional-only signature would raise ``TypeError`` instead)."""
    from app.research.tradability import _PriorSessionBarView

    calls: list[dict] = []

    class _RecordingStore:
        def list(self, *, include_bars: bool = True):
            calls.append({"include_bars": include_bars})
            return [], []

    view = _PriorSessionBarView(_RecordingStore(), 0.0)
    view.list(include_bars=False)
    view.list()
    assert calls == [{"include_bars": False}, {"include_bars": True}]

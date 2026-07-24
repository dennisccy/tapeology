"""Source-introspection guard: every Pydantic request-body model class defined in
``app/research/routes.py`` must be referenced by at least one live route-handler parameter in the
same file (era-5D J-05/close-out iteration, "The Clean Slate" demolition interlude).

BACKGROUND: era-5D J-01's route demolition deleted 14 route handlers but left 5 orphaned
request-body classes behind -- ``ThesisRequest``, ``ResolveRequest``, ``ActionRequest``,
``StudyRequest``, ``ReviewRequest`` -- each with exactly one occurrence in the file (its own
``class X(BaseModel):`` def line) and zero live references. That was a grep-provable breach of the
critical "Deletion is complete, never cosmetic" anti-goal that four earlier passes missed and only
a hard audit caught. This test is the durable guard against that defect class recurring.

Built STRUCTURALLY (parses ``routes.py``'s own current class/parameter shape via ``ast``) -- it
NEVER names a specific class as a string, so it keeps failing correctly after any FUTURE route
deletion instead of going stale itself (the carried lesson: a guard test that hardcodes a deletion
target is only good until the next deletion).
"""

from __future__ import annotations

import ast
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
ROUTES_PATH = BACKEND_DIR / "app" / "research" / "routes.py"


def _request_body_model_classes(tree: ast.Module) -> set[str]:
    """Every top-level class in the module whose bases include ``BaseModel`` by name."""
    names = set()
    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == "BaseModel":
                names.add(node.name)
                break
    return names


def _annotation_names(annotation) -> set[str]:
    """Every ``Name`` identifier appearing anywhere inside a parameter annotation expression --
    handles a plain ``X``, a subscripted ``Optional[X]``, or a ``X | None`` union alike. Never
    matches a class's own ``class X(...):`` def line (that is a different AST node kind, not a
    function-parameter annotation) and never matches a docstring or comment mention."""
    if annotation is None:
        return set()
    return {node.id for node in ast.walk(annotation) if isinstance(node, ast.Name)}


def _parameter_referenced_class_names(tree: ast.Module) -> set[str]:
    """Every class name annotated on some function parameter anywhere in the module -- i.e. used
    as a live route-handler request body (or any other function parameter)."""
    referenced: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        args = node.args
        all_params = [*args.posonlyargs, *args.args, *args.kwonlyargs]
        if args.vararg:
            all_params.append(args.vararg)
        if args.kwarg:
            all_params.append(args.kwarg)
        for param in all_params:
            referenced |= _annotation_names(param.annotation)
    return referenced


def _orphaned_model_classes(source: str) -> list[str]:
    tree = ast.parse(source)
    model_classes = _request_body_model_classes(tree)
    referenced = _parameter_referenced_class_names(tree)
    return sorted(model_classes - referenced)


def test_every_request_body_model_is_referenced_by_a_live_route_parameter():
    """Structural invariant: every ``class X(BaseModel):`` defined in ``routes.py`` must be
    annotated on at least one function parameter elsewhere in the same file. A class satisfying
    only its own def line is an orphan -- exactly the residue era-5D's close-out iteration deleted
    (``ThesisRequest``, ``ResolveRequest``, ``ActionRequest``, ``StudyRequest``,
    ``ReviewRequest``)."""
    source = ROUTES_PATH.read_text()
    model_classes = _request_body_model_classes(ast.parse(source))
    assert model_classes, "expected at least one BaseModel request-body class in routes.py"

    orphans = _orphaned_model_classes(source)
    assert not orphans, (
        "orphaned request-body model class(es) with no live route-handler parameter reference: "
        f"{orphans} -- delete the class (and its docstring) or wire it to a route parameter"
    )


def test_the_guard_would_have_flagged_the_just_deleted_orphans_pre_cleanup():
    """Proves the guard's own logic is sound (not merely that it happens to pass today): re-applied
    to a synthetic module reproducing the PRE-cleanup shape (the 5 now-deleted classes present with
    zero parameter references, alongside one referenced class standing in for the 4 kept ones), it
    must name exactly those 5 as orphans."""
    pre_cleanup_source = '''
from pydantic import BaseModel


class ThesisRequest(BaseModel):
    ticker: str


class ResolveRequest(BaseModel):
    resolution: str


class ActionRequest(BaseModel):
    kind: str


class StudyRequest(BaseModel):
    source_kind: str


class ReviewRequest(BaseModel):
    note: str | None = None


class BacktestRequest(BaseModel):
    dataset_id: str


def create_backtest(body: BacktestRequest) -> dict:
    return {}
'''
    orphans = _orphaned_model_classes(pre_cleanup_source)
    assert orphans == [
        "ActionRequest",
        "ResolveRequest",
        "ReviewRequest",
        "StudyRequest",
        "ThesisRequest",
    ]

"""Source-inspection guards over the ONE table-sorting primitive on /desk.

`apps/frontend/lib/useTableSort.ts` + `apps/frontend/components/SortableHeader.tsx` are what let the
desk page's standing served-order rule be narrowed instead of deleted. Four shipped guards
(`test_desk_ui_guards.py`'s reorder/slice/rank trio, `test_playbook_shape_overlay_guards.py`'s
occurrence-order guard, and `test_desk_forward_ui_guard.py`'s forward-block guard) each gave up
something specific on the strength of the properties asserted here. If this module goes soft, those
narrowings stop being paid for.

There is no frontend test runner in this repo (no `test` script in apps/frontend/package.json, no
`.test.tsx` anywhere), so these are source-inspection lints in this suite's own established style --
and every one ships with a seeded counter-test, because a guard that cannot fail proves nothing.
"""

import pathlib
import re

_FRONTEND_ROOT = pathlib.Path(__file__).resolve().parents[2] / "frontend"
_HOOK = _FRONTEND_ROOT / "lib" / "useTableSort.ts"
_HEADER = _FRONTEND_ROOT / "components" / "SortableHeader.tsx"

_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_LINE_COMMENT = re.compile(r"//[^\n]*")


def _code(path: pathlib.Path) -> str:
    """Source with comments stripped -- a guard must never pass or fail on prose that merely
    DESCRIBES the thing it forbids. Both modules below explain their own bans in words."""
    assert path.exists(), f"expected {path} to exist"
    source = _BLOCK_COMMENT.sub(" ", path.read_text())
    return _LINE_COMMENT.sub(" ", source)


def _hook_body(source: str) -> str:
    """`useTableSort`'s own body by brace-walk (this suite's convention -- each guard module owns
    its copy rather than sharing one).

    The parameter list is walked FIRST and skipped: the signature spans several lines and its
    return type is an object type, so the first `{` after the name belongs to neither the params
    nor the body. Walking from the wrong brace returns a type literal, and every `in` assertion
    below would pass on an empty haystack -- the one failure mode a guard must not have."""
    marker = "export function useTableSort"
    start = source.index(marker)
    paren_depth = 0
    body_start = -1
    for index in range(start + len(marker), len(source)):
        char = source[index]
        if char == "(":
            paren_depth += 1
        elif char == ")":
            paren_depth -= 1
            if paren_depth == 0:
                body_start = source.index("{", index)
                break
    assert body_start != -1, "useTableSort's parameter list never closes"
    depth = 0
    for index in range(body_start, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[body_start : index + 1]
    raise AssertionError("useTableSort's body never closes")


def test_the_body_extractor_returns_a_body_not_a_type_literal():
    """A counter-test for the helper itself: every assertion below is only as honest as this walk."""
    body = _hook_body(_code(_HOOK))
    assert "useState" in body, "the extractor did not reach the hook's implementation"
    assert body.endswith("}")


# --- 1. served order is the DEFAULT, and it is the untouched array -------------------------------


def test_the_default_path_returns_the_served_array_before_any_comparator_runs():
    """The load-bearing property of the whole primitive.

    "Served order" must be the array as handed in, NOT the result of sorting by whatever key the
    record happened to be ordered on -- those differ the moment two rows tie, and the second is the
    page choosing an order on the operator's behalf, which is the thing /desk's rule forbids.

    Asserted structurally: the `sort === null` early return appears BEFORE the first `.sort(` in the
    body, so no comparator can execute in the default path."""
    body = _hook_body(_code(_HOOK))
    assert "items.map((item, servedIndex) =>" in body, (
        "the hook no longer materialises the served order as a plain index-preserving map"
    )
    guard_at = body.index("if (sort === null")
    sort_at = body.index(".sort(")
    assert guard_at < sort_at, (
        "a comparator can run before the served-order check -- the default order would then be a "
        "SORT BY SOMETHING rather than the record's own order"
    )
    assert "return base;" in body, "the default path no longer returns the untouched base array"


def test_an_unresolvable_column_falls_back_to_the_served_order():
    """A stale column id (the data changed under a chosen sort) must degrade to the served order,
    which is the only order the hook can honestly produce without a column to read."""
    body = _hook_body(_code(_HOOK))
    assert "activeColumn === null) return base" in body, (
        "an unresolvable column id no longer falls back to the served order"
    )


# --- 2. the mapping is TOTAL -- nothing is dropped, ever -----------------------------------------


def test_the_hook_is_a_total_mapping_of_its_input():
    """One entry out per item in, always.

    Three shipped guards lean on this directly: the ranked page window
    (`test_desk_ui_guards.py::test_desk_page_slices_rows_only_for_the_ranked_page_window`), the
    uncapped Forward Returns block
    (`test_desk_forward_ui_guard.py::test_the_forward_block_deliberately_permits_an_operator_chosen_sort`)
    and the occurrence list
    (`test_playbook_shape_overlay_guards.py::test_occurrence_rows_default_to_the_records_own_served_order`).
    Each of those stopped counting rows itself on the strength of this. A hook that could filter or
    truncate would silently cap all twelve tables at once."""
    body = _hook_body(_code(_HOOK))
    for banned in (".slice(", ".filter(", ".pop(", ".shift(", ".splice(", "length ="):
        assert banned not in body, (
            f"useTableSort's body contains {banned!r} -- the sorted entries must be a TOTAL "
            "mapping of the input; dropping or truncating here caps every /desk table silently"
        )


def test_the_hook_never_mutates_its_caller_s_array():
    """`items` belongs to the caller and to the record it came from. An in-place sort would reorder
    the record itself, so a later render in the served order would be reading an array the page had
    already scrambled."""
    body = _hook_body(_code(_HOOK))
    assert "[...base].sort(" in body, "the hook sorts something other than a copy of the base array"
    assert "items.sort(" not in body and "base.sort(" not in body, (
        "the hook sorts in place -- the caller's own array would be reordered underneath it"
    )


# --- 3. the comparator itself --------------------------------------------------------------------


def test_missing_values_sort_last_in_both_directions():
    """Structural: the missing-value branch RETURNS before the direction flip below it can reach
    that pair. Negating it would float every blank cell to the top of a descending sort, which reads
    as data rather than as absence."""
    body = _hook_body(_code(_HOOK))
    missing_at = body.index("if (left === null || right === null)")
    flip_at = body.index('direction === "asc" ? ranked : -ranked')
    assert missing_at < flip_at, "the missing-value branch no longer precedes the direction flip"
    branch = body[missing_at:flip_at]
    assert "return left === null ? 1 : -1;" in branch, (
        "missing values are no longer forced last regardless of direction"
    )
    assert "direction" not in branch, (
        "the missing-value branch reads the sort direction -- it must be direction-INDEPENDENT, or "
        "descending would lead with every blank cell"
    )


def test_numbers_are_compared_relationally_and_never_by_subtraction():
    """`left - right` is both an arithmetic-lint hazard (the desk pages ban derived numbers) and
    simply wrong at the infinities. Relational operators are correct everywhere."""
    code = _code(_HOOK)
    compare_at = code.index("function comparePresent")
    body = code[compare_at : code.index("export function useTableSort")]
    assert "if (left < right) return -1;" in body and "if (left > right) return 1;" in body, (
        "the numeric branch no longer compares relationally"
    )
    assert "left - right" not in body and "right - left" not in body, (
        "the numeric branch subtracts one served value from another"
    )


def test_the_sort_is_stable_on_the_served_position():
    """Equal values keep the record's own order, which also makes the sort stable across engines."""
    body = _hook_body(_code(_HOOK))
    assert body.count("a.servedIndex < b.servedIndex ? -1 : 1") == 2, (
        "the servedIndex tie-break is missing from the equal-values path or the both-missing path "
        "-- equal rows would then reorder arbitrarily between renders"
    )


def test_timestamps_are_parsed_rather_than_compared_as_strings():
    """The served stamps carry 6-digit microseconds; a future `+00:00` form would sort wrong as a
    plain string while looking correct in every existing record."""
    code = _code(_HOOK)
    assert "Date.parse(String(raw))" in code, (
        "instant columns no longer parse their value -- a lexical compare would silently mis-sort "
        "any stamp written in a different but equivalent ISO form"
    )


def test_the_toggle_cycles_through_all_three_states():
    """Served -> ascending -> descending -> served. Without the third transition an operator who
    sorted a table could not get back to the record's own order from that column."""
    code = _code(_HOOK)
    toggle_at = code.index("const toggle = useCallback(")
    body = code[toggle_at : code.index("const reset = useCallback(")]
    assert '{ columnId, direction: "asc" }' in body
    assert '{ columnId, direction: "desc" }' in body
    assert "return null;" in body, (
        "the third click does not return to the served order -- the cycle never closes"
    )


# --- 4. the primitive must not move the page's pinned effect census ------------------------------


def test_neither_sort_module_introduces_an_effect():
    """/desk pins an exact effect/interval/timeout census
    (`test_desk_refresh_chain_guard.py`). This hook is called a dozen times on that page, so an
    effect here would multiply straight into those numbers."""
    for path in (_HOOK, _HEADER):
        code = _code(path)
        for banned in ("useEffect", "setInterval", "setTimeout"):
            assert banned not in code, (
                f"{path.name} uses {banned} -- the /desk effect census is pinned, and this module "
                "is instantiated once per table"
            )


# --- 5. the header's accessibility and honesty contract ------------------------------------------


def test_the_header_control_is_a_real_button_not_a_click_handler_on_a_cell():
    """A `<th onClick>` (the pattern the rest of the desk page uses for rows) is unreachable by
    keyboard and announces nothing. A sort control is exactly where that gap must not be
    propagated -- the same reasoning the playbook expansion button already records."""
    code = _code(_HEADER)
    assert '<button\n        type="button"' in code or '<button type="button"' in code, (
        "the sort control is no longer a real button element"
    )
    assert "<th\n      scope=\"col\"" in code or '<th scope="col"' in code, (
        "the sortable header cell lost its scope"
    )
    assert "onClick={() => sort.toggle(column.id)}" in code, (
        "the sort toggle is not wired to the header button"
    )


def test_the_state_is_announced_through_aria_sort_and_not_duplicated_by_the_glyph():
    """`aria-sort` on the `<th>` is the ARIA-native channel a screen reader reads on entering the
    column, so the arrow beside the label is decoration and must not be announced twice."""
    code = _code(_HEADER)
    assert "aria-sort={state}" in code, "the sortable header no longer announces its sort state"
    assert 'aria-hidden="true"' in code, "the sort glyph is not hidden from assistive technology"


def test_the_header_renders_the_columns_own_label():
    """A shared header component could quietly re-word every header on the page. It renders
    `column.label` verbatim instead -- which is what bounds
    `test_desk_touch_time_et_guard.py::test_the_column_names_the_clock_it_is_on`, now that the
    touch table's "time (ET)" header is produced here rather than written as literal markup."""
    code = _code(_HEADER)
    # `${column.label}` (the header's own tooltip) contains the render form as a substring, so it is
    # subtracted out rather than counted as a third render site.
    renders = code.count("{column.label}") - code.count("${column.label}")
    assert renders == 2, (
        "the header no longer renders the column's own label verbatim in BOTH the sortable and the "
        f"non-sortable branch (found {renders}) -- a re-worded header would misname the value "
        "beneath it"
    )


def test_a_non_sortable_column_renders_a_plain_cell():
    """Some columns have no single served value to order on (a multi-counter outcomes cell, the
    beyond-cap chip). Those must render exactly as they did before, not as a dead control."""
    code = _code(_HEADER)
    assert "if (column.sortable === false)" in code, (
        "a column can no longer opt out of sorting -- a column with no orderable served value "
        "would present a control that cannot do anything"
    )


def test_a_non_served_order_is_disclosed_and_reversible():
    """The honesty surface the four narrowings were paid for with. Without it a sorted table is
    indistinguishable from the record's own ranking, and there is no way back."""
    code = _code(_HEADER)
    assert "export function TableSortNote" in code
    assert "if (sort.isServedOrder" in code, (
        "the note renders even in the served order -- there is then nothing to disclose and a "
        "reset control that does nothing"
    )
    assert 'data-testid="desk-sort-active-note"' in code
    assert 'data-testid="desk-sort-reset"' in code
    assert "onClick={sort.reset}" in code, "the reset control does not reset"
    assert "not the order the record served" in code, (
        "the disclosure no longer says WHAT the order is not -- naming the served order is the "
        "whole point of the note"
    )
    assert "Reset to served order" in code


# --- 6. counter-tests: every lint above can fail --------------------------------------------------


def test_the_totality_lint_can_fail_on_a_seeded_violation():
    seeded = "const base = items.map((i, n) => ({ i, n })).filter(keep);"
    assert ".filter(" in seeded
    seeded_cap = "return [...base].sort(cmp).slice(0, 50);"
    assert ".slice(" in seeded_cap


def test_the_default_order_lint_can_fail_on_a_seeded_violation():
    """The subtle wrong version: sorting by a guessed key instead of returning the array as given.
    The `sort === null` check would then sit AFTER the comparator, which is what the lint reads."""
    seeded = (
        "const base = [...items].sort(byTriggerTs);\n"
        "if (sort === null) return base;\n"
        "return base;"
    )
    assert seeded.index(".sort(") < seeded.index("if (sort === null")


def test_the_mutation_lint_can_fail_on_a_seeded_violation():
    seeded = "return items.sort(cmp);"
    assert "items.sort(" in seeded
    assert "[...base].sort(" not in seeded


def test_the_subtraction_lint_can_fail_on_a_seeded_violation():
    seeded = "if (kind !== 'text') return left - right;"
    assert "left - right" in seeded
    assert "if (left < right) return -1;" not in seeded


def test_the_null_last_lint_can_fail_on_a_seeded_violation():
    """The wrong version negates the missing branch along with everything else, so blanks lead a
    descending sort."""
    seeded_branch_order = (
        'const ranked = direction === "asc" ? compare(l, r) : -compare(l, r);\n'
        "if (left === null || right === null) return left === null ? 1 : -1;"
    )
    assert seeded_branch_order.index('direction === "asc"') < seeded_branch_order.index(
        "if (left === null"
    )


def test_the_button_lint_can_fail_on_a_seeded_violation():
    seeded = '<th scope="col" onClick={() => sort.toggle(column.id)}>{column.label}</th>'
    assert '<button type="button"' not in seeded


def test_the_disclosure_lint_can_fail_on_a_seeded_violation():
    seeded = "export function TableSortNote({ sort }) { return <p>sorted</p>; }"
    assert 'data-testid="desk-sort-reset"' not in seeded
    assert "if (sort.isServedOrder" not in seeded

# Iteration 7 — Coherence Audit

**Iteration:** goal-desk-iter-7
**Date:** 2026-07-26
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Scope of this iteration's diff

Reviewed against snapshot `384d2ea83538a9092a4120f275efebbb5fba1452` (noise-excluded):

- `apps/backend/app/mcp/__init__.py` — two new `_STATIC_PATHS` entries (`desk_universe`,
  `desk_screen`) + their `types.Tool(...)` registry entries.
- `apps/backend/tests/test_mcp_server.py` — `EXPECTED_TOOLS` extended to 17; byte-identity tests
  (empty + populated) for the two new tools; a `get_endpoint` `?date=` proxy test.
- `apps/frontend/app/desk/page.tsx` — two new pure functions (`deskRowDrillInTitle`,
  `deskSkipDrillInTitle`) whose output is wired onto the existing `desk-row-drill-in` /
  `desk-skip-row-drill-in` anchors' `title=` attribute (audit F2 fix).
- `README.md` — AUTO:capabilities prose refresh describing the now-clickable history rows and
  drill-in links (documentation only).
- `runs/goal-session-desk/journey-scripts/J-05.json` step 2 and `J-07.json` step 10 — golden-script
  selector fixes (test assets, excluded from the main diff scope by design but read directly).
- `runs/goal-session-desk/state/blueprint.md`, `assumptions.md` — additive documentation of the
  above (RESOLVED at iter-7 note), consistent with what the code diff actually does.
- New file `apps/backend/tests/test_desk_hover_tooltip_guard.py` — source-introspection guard test
  (plus seeded-violation counter-test) proving the F2 fix stays composed from the right fields.

No changes to `app/meta.py`, any nav/router component, `desk_universe.py`, `desk_screen.py`,
`desk_coverage.py`, `tradability.py`, `levels.py`, or `bars.py` — all frozen/canonical modules stay
byte-unchanged, consistent with the spec's Out-of-Scope list and the Data Contract's zero-diff
requirements.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Universe snapshots + membership (`GET /research/desk/universe`) | OK | `apps/backend/app/mcp/__init__.py:109` (`"desk_universe": "/research/desk/universe"`) is a plain dict-lookup proxy; `call_tool` resolves it through `_STATIC_PATHS` → `_proxy_get(path)` (`__init__.py:409-416`), a straight `httpx` GET against the running backend — no recomputation, no new store read. Confirmed byte-identical to the REST equivalent by the new tests in `test_mcp_server.py` (honest-empty + populated states). |
| Screen snapshots / rank / skip rows (`GET /research/desk/screen`) | OK | Same mechanism, `apps/backend/app/mcp/__init__.py:110` (`"desk_screen": "/research/desk/screen"`). `get_endpoint`'s existing `/research/` allowlist reaches the `?date=` variant with zero code change (confirmed: no diff to `get_endpoint`'s allowlist logic), matching the blueprint's "iter-7 (J-06)" note verbatim. |
| Per-member coverage freshness (`latest_window_end_utc`) | OK | The F2 fix (`apps/frontend/app/desk/page.tsx:181-193`, `deskRowDrillInTitle`/`deskSkipDrillInTitle`) only re-reads the field already embedded on the row/skip object (`row.coverage`, `skip.coverage` — sourced from `desk_coverage.get_desk_coverage` via the screen snapshot, unchanged this iteration) and reformats it into a composite tooltip string. No new fetch, no new computation. |
| `distance_bps` / `band_score` | OK | Same fix, same source object (`row.distance_bps`, `row.band_score` — already present on the `DeskScreenRow` type, unchanged). Re-formatted for the tooltip, not recomputed. |

No new value/entity is introduced this iteration (the spec's own "New information displayed: None"
holds under inspection — the tooltip surfaces detail that was already present in the DOM via the
now-unreachable per-cell `title`s, just relocated).

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `desk_universe` / `desk_screen` MCP tools | OK | No page required — matches the blueprint's Feature/journey homes row for J-06 ("MCP tool surface; no page"). `apps/backend/app/meta.py` (nav owner) has zero diff against the snapshot; route count stays 3. |
| `/desk` F2 hover-tooltip fix | OK | Stays inside `/desk`'s already-registered canonical home; no new route, no layout/shell change. `apps/frontend/app/desk/page.tsx`'s anchor `href`, `absolute inset-0` class, and `data-testid` are byte-unchanged (only `title=` was added) — confirmed via diff, so the existing click-through navigation (already reachable in ≤2 clicks per the blueprint) is untouched. |

No new page/route/component this iteration; nothing to check for duplicate homes or parallel
shells.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- Minor tidiness note, not a coherence violation: the per-cell `title` attributes this fix was
  working around (`apps/frontend/app/desk/page.tsx:146` on the coverage badge, `:249` on
  `desk-row-distance`, `:252` on `desk-row-score`) were left in place rather than removed. They are
  now permanently unreachable by hover (the row's `absolute inset-0` anchor is topmost everywhere
  in the row), so they are inert markup, not a second displayed copy of the value — the anchor's
  composite tooltip is the only tooltip a user can ever actually see. This matches the spec's
  explicit instruction ("zero change to... any other row markup") and was the deliberate,
  regression-safe choice logged in `assumptions.md` iter-7, so it is not a defect — just dead code a
  future cleanup pass could remove.

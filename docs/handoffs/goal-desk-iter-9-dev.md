# goal-desk-iter-9 Dev Handoff

**Phase:** goal-desk-iter-9
**Date:** 2026-07-27
**Agent:** developer
**Status:** complete

## What Was Built

J-08 only (the proposer-promoted journey inside `docs/goal.md`'s `AUTO:journeys` block): every
ranked `/desk` briefing row now discloses `basis_as_of` (the daily bar `compute_tradability`
actually measured its distance/class from) and `basis_age_days` (how many calendar days before the
screen's own `as_of` that bar is dated). No new page, route, Config field, or MCP tool.

- **Backend — basis fields on ranked rows only.** `apps/backend/app/research/desk_screen.py`'s
  `compute_screen` ranked-row branch (the `else` clause, was ~:310-325) now appends
  `basis_as_of` — copied VERBATIM from `result["basis_as_of"]` (already read at that point to
  resolve the reference close, so this is zero additional `compute_tradability`/`BarStore` work)
  — and `basis_age_days`, computed by a new pure-function helper, `_basis_age_days(basis_as_of,
  as_of)`, which reduces both ISO timestamps to UTC calendar dates before subtracting (never a raw
  hour delta — `basis_as_of` carries a bar's own time-of-day, `as_of` is always fixed at
  `23:59:59Z`). Skip rows are structurally untouched — the `elif result["basis_as_of"] is None`
  branch is the only other outcome and never enters the ranked-row branch. Module + function
  docstrings updated to document the new fields and their append-only-honesty contract.
- **Backend — zero-extra-call guard (TC-8).** New test
  `test_basis_fields_add_zero_extra_compute_tradability_calls` in `test_desk_screen.py`,
  instrumented exactly like the existing `test_bar_store_signature_issues_zero_bar_store_calls`
  (monkeypatches `compute_tradability` inside the `desk_screen` module namespace and counts calls):
  proves the call count equals exactly the member count, zero calls attributable to the two new
  fields.
- **Backend — goldens.** Extended `test_aapl_row_cross_checks_byte_identical_to_the_real_tradability_route`
  (TC-1/TC-2) to assert the persisted AAPL row's `basis_as_of` is byte-identical to
  `GET /research/tradability`'s own `basis_as_of`, and `basis_age_days == 4` (the fixture's real
  2026-06-18 → 2026-06-22 span). Added a dedicated pure-function test asserting goal.md's own
  worked example exactly (`_basis_age_days(...) == 12`), plus a calendar-vs-hour-delta edge-case
  test. Added `test_recording_a_freshly_computed_screen_twice_is_refused_and_basis_fields_stay_byte_identical`
  (TC-3): a real `compute_screen()` result recorded once, a second identically-pinned computation
  refused by `ScreenStore.record` (`ScreenAlreadyRecorded`, no second file), and the content already
  on disk read back byte-identical to the second (unrecorded) computation including both new
  fields. Added `test_a_legacy_row_recorded_without_basis_fields_serves_them_absent_never_backfilled`:
  proves `ScreenStore` performs no row-shape validation/enrichment — a legacy row (the shape every
  screen recorded before this iteration has) round-trips with the two keys entirely ABSENT, never
  defaulted to `null`.
- **Backend — TC-4 real-file evidence (not a pytest test — see rationale below).** Verified with
  live Bash/curl commands against the two REAL screen snapshots on disk
  (`apps/backend/.data/screen/screen-2026-06-22-3ecd45c062c7.json`,
  `screen-2026-07-25-e184a7dc2f86.json`): SHA-256 checksums captured BEFORE any code change
  (`530bb4f6...878acba`, `9c2fddf6...880068`) and re-verified AFTER the full change set and every
  verification run below — byte-identical, unchanged. A live GET against the ambient store
  (`curl http://localhost:8301/research/desk/screen` with the backend pointed at the real
  `apps/backend/.data/`) confirms the latest real screen's ranked rows serve with `basis_as_of`
  entirely absent from the JSON (`'basis_as_of' in row` is `False`), never backfilled. This is
  evidence-only, not a permanent pytest test, because the project's own hermetic-suite discipline
  (`docs/goal.md` Constraints: "the suite stays keyless on committed fixtures") means the pytest
  suite must never depend on the presence of ambient, non-committed `.data/` files (which are
  entirely gitignored) — the equivalent CONTRACT is instead pinned hermetically by
  `test_a_legacy_row_recorded_without_basis_fields_serves_them_absent_never_backfilled` above,
  using a fixture-scoped row.
- **Backend — tooltip guard extension.** `test_desk_hover_tooltip_guard.py`'s
  `test_ranked_row_drill_in_tooltip_is_built_from_distance_score_and_coverage_freshness` now also
  requires `deskRowDrillInTitle`'s source to reference `row.basis_as_of`/`row.basis_age_days`,
  mirroring its existing `distance_bps`/`band_score` needles.
- **Golden replay script + fixture-scoped rig.** New `runs/goal-session-desk/journey-scripts/J-08.json`
  (7 steps: load `/desk`, confirm the new "basis" column renders descriptive text on the latest
  screen, click into a legacy history row and confirm the honest
  "basis not recorded in this snapshot" fallback, return to Latest, confirm the page is still alive
  — the iter-4 post-match-liveness lesson). New reusable script
  `apps/backend/scripts/goal-desk-iter9-scoped-backend.sh` (never touches the ambient
  `apps/backend/.data/`: copies the WHOLE `.data/` tree — including the two real legacy screen
  snapshots and ~60 real symbols' worth of recorded bars — into a throw-away root, and points the
  five `TAPEOLOGY_*` directory env vars at the copy; mirrors the `goal-desk-iter8-baseline-diff.py`
  "copy the whole tree" recipe rather than iter-5's narrow fixture-only seed, because this
  iteration specifically needs the real legacy screens already in history). Verified with
  `--mode verify --journeys J-08` against that scoped rig on `:8301`/`:3301` (T-9 clean rebuild) —
  **PASS, 0 failed** (`reports/phase-goal-desk-iter-9-regression-replay-results.md`, screenshot at
  `reports/qa/goal-desk-iter-9-evidence/J-08-verify.png`). A fresh screen was computed once against
  that SAME scoped copy (`POST /research/desk/screen/compute` for `screen_date=2026-07-27`, 101
  members, ~100s) before recording the replay, so the "latest" view genuinely carries real
  `basis_as_of`/`basis_age_days` values (age spread observed: AAPL 3d, most large-caps 4d, MSFT 6d,
  NFLX/NVDA/META 14d — the proposer's own 2026-07-25 measurement shifted forward two real days).
- **Smoke-set regression replay (TC-13).** `--mode verify --journeys J-01,J-02,J-03,J-04,J-05,J-06,J-07`
  against the same scoped rig: **6/7 PASS, 1 SKIPPED** (J-06 has no golden script — it always has
  been backend/MCP-only with no browser UI, consistent with every prior iteration's regression
  runs). Zero failures, zero regressions
  (`reports/phase-goal-desk-iter-9-smoke-replay-results.md`).

## Files Changed

- `apps/backend/app/research/desk_screen.py` -- `_basis_age_days` helper + the ranked-row branch in
  `compute_screen` gains `basis_as_of`/`basis_age_days`; docstring updates.
- `apps/backend/tests/test_desk_screen.py` -- extended AAPL cross-check (TC-1/TC-2), new pure-fn
  calendar-diff tests, new zero-extra-call guard test (TC-8), new re-run-byte-identical test (TC-3),
  new legacy-row-honesty test.
- `apps/backend/tests/test_desk_hover_tooltip_guard.py` -- extended the ranked-row tooltip guard to
  require `basis_as_of`/`basis_age_days` references.
- `apps/frontend/lib/types.ts` -- `DeskScreenRow` gains `basis_as_of: string | null` and
  `basis_age_days: number | null`, with a doc comment on the absent-vs-null legacy nuance.
- `apps/frontend/app/desk/page.tsx` -- new "basis" column (header + `DeskRow` cell), honest
  "basis not recorded in this snapshot" fallback, `deskRowDrillInTitle` extended with the
  full-precision basis detail (never a new per-cell `title` — the iter-6/iter-7 F2 lesson applied
  proactively); two doc comments updated for accuracy.
- `apps/backend/scripts/goal-desk-iter9-scoped-backend.sh` -- new, reusable fixture-scoped rig
  (real-data copy) for this iteration's and the next lane's browser evidence.
- `runs/goal-session-desk/journey-scripts/J-08.json` -- new golden replay script.
- `reports/phase-goal-desk-iter-9-regression-replay-results.md`,
  `reports/phase-goal-desk-iter-9-smoke-replay-results.md`,
  `reports/qa/goal-desk-iter-9-evidence/*.png` -- new, replay evidence.

**Confirmed untouched (as scoped):** `apps/backend/app/research/tradability.py`, `levels.py`,
`bars.py`, `apps/frontend/components/StructureChart.tsx`, `PriceChart.tsx`, `app/engine/`,
`apps/backend/app/research/desk_routes.py` (dict pass-through, verified no `response_model` narrows
the row shape), `app/mcp/__init__.py`, `apps/backend/tests/test_mcp_server.py`,
`apps/backend/tests/test_copy_discipline.py`, any `Config` field/file, any R-1 file.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: **1346 passed, 8 skipped, 0 failed** (floor was 1341/8 — exactly +5, matching the 5 new
tests added; this pytest/plugin combo does not print its usual trailing summary line, so the count
was parsed from the `-q` progress-character stream; exit code 0 corroborates zero failures).

Also run individually before the full suite (all passed):
- `pytest tests/test_desk_screen.py -q` — 44 passed.
- `pytest tests/test_desk_hover_tooltip_guard.py tests/test_desk_ui_guards.py tests/test_copy_discipline.py tests/test_mcp_server.py tests/test_desk_screen_compute.py tests/test_desk_coverage.py -q` — all passed.

Other verification:
- `python -c "from app.config import Config; print(Config().config_fingerprint())"` → `08e471b10130e1e2` (pin unchanged).
- `git diff --stat -- app/research/tradability.py app/research/levels.py app/research/bars.py components/StructureChart.tsx components/PriceChart.tsx app/engine/` → empty (TC-16, zero diff).
- `cd apps/frontend && npx tsc --noEmit` → clean, zero type errors.
- Deterministic replay: J-08 PASS (0 failed); smoke-set J-01–J-07 6 PASS / 1 SKIP (J-06, no golden script) / 0 FAIL — see "What Was Built" above for report paths.
- Real-data TC-4 evidence: see "What Was Built" above.

## Pre-handoff verification

- **Service startup:** `scripts/dev.sh` (ambient ports 8301/3301, the deterministic per-repo
  offset) started backend + frontend cleanly twice in a row (stop, then restart — no port-conflict
  errors either time); `curl /health` → `{"status":"ok"}`; `/desk` → HTTP 200 against the ambient
  store, serving the two real legacy screens honestly (fields absent). All server processes
  (scoped rig AND both `dev.sh` runs) were stopped before finishing — confirmed via `lsof`/`pgrep`
  that no tapeology `uvicorn`/`next dev` process remains running.
- **No new dependency, no migration, no schema change** — nothing else in this checklist applies.

## Known Issues

- **TC-7's hit-test (`document.elementFromPoint` at the new basis cell's own center) is NOT
  covered by this dev pass.** `demo_runner.py`'s deterministic replay vocabulary
  (`goto`/`click`/`fill`/`expect`/`wait_for`) has no hover/JS-evaluation primitive, so this specific
  check needs the browser-qa-agent's Chrome-MCP lane (same division of labor the iter-6/iter-7 audit
  established for the ORIGINAL three-field hit-test). Structurally, the new basis `<td>` carries no
  `title` of its own (I deliberately kept the full-precision detail ONLY on the row anchor's
  existing consolidated tooltip), so there is no new per-cell-title regression risk to hit-test
  against — but the "the anchor is still topmost at the new cell's center" geometry claim itself
  still needs a live-browser confirmation now that the table has an 8th column.
- **TC-12's specific ≤2d/≥10d screenshot is NOT captured by this dev pass.** The DoD assigns it to
  browser-qa-agent explicitly ("J-08 passes via browser-qa-agent, including a screenshot..."). This
  dev pass DID verify the mechanism end-to-end on real data (age spread observed today: AAPL 3d,
  most large-caps 4d, MSFT 6d, NFLX/NVDA/META 14d — see `J-08-verify.png`), which is a genuine
  fresh-vs-stale demonstration, but does not hit the literal ≤2d threshold on today's data (freshest
  real row is 3d old). The reusable scoped-rig script
  (`apps/backend/scripts/goal-desk-iter9-scoped-backend.sh`) is available for that lane to re-copy
  fresher ambient data and/or wait for a subsequent operator top-up closer to a ≤2d reading, or to
  simply judge the observed 3d/14d spread as sufficient "fresh vs. stale" evidence — that judgment
  call belongs to the QA/evaluator lane, not this handoff.
- **The `[NEW]`-flagged demo-narrator walkthrough is explicitly a downstream showcase-step
  deliverable**, not a dev-lane one (per the plan's own final line) — not attempted here.
- **No other gaps.** Every DoD item this dev pass owns is met: basis fields on new ranked rows only
  (zero extra reads), byte-identical re-run, legacy rows honestly absent (both hermetically and on
  the real files), the "basis" column + fallback + tooltip shipped, the guard test extended, the new
  golden recorded and verified, the smoke set green, zero anti-goal violations, suite green above
  floor.

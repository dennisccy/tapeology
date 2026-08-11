# goal-playbook-iter-8 Dev Handoff

**Phase:** goal-playbook-iter-8
**Date:** 2026-08-11
**Agent:** developer
**Status:** complete

## What Was Built

J-08 — "The evidence view": a read-only, stat-cached fold of every recorded playbook signal at
ONE signature into per-(setup_id, side, measure) distribution cells beside the pooled seeded
baseline, honestly tagging low-n cells, plus the five carry items the last two ESCALATEs left
open.

### J-08 — the evidence view

- **`app/research/desk_playbook_evidence.py`** (new module):
  - `fold_evidence(store, bar_store, members, config_fingerprint, cache=None)` — the whole
    `GET /research/desk/playbook/evidence` body. Resolves the CURRENT default signature via
    `compute_playbook_input_signature` (imported verbatim, the exact function `compute_playbook`
    itself calls), walks every recorded playbook file, splits by whether that file's own
    `playbook_input_signature` matches the current default, and folds ONLY the default-signature
    files' signals/baseline anchors into `cells` — every other signature is listed under
    `other_signatures` (`dates`/`created_span`), never pooled (TC-5).
  - `cells` is the FULL declared cross product of `PLAYBOOK_SETUPS` × `("long","short")` ×
    `PLAYBOOK_SIGNAL_MEASURES` (9 × 2 × 15 = 270 rows) — every combination is always served, so a
    combination with zero recorded signals reads `n: 0` (not omitted, not a crash — the error-case
    requirement). Each cell: `signal {n, n_truncated, median_pct, p25_pct, p75_pct, mean_pct}` vs
    `baseline {n_baseline, median_pct, p25_pct, p75_pct, mean_pct}`, `below_min_n` (`signal.n <
    PLAYBOOK_MIN_N_DISCLOSURE`, i.e. `< 12`).
  - **Quantile math is new evidence-only fold math, not a second implementation of the rail.**
    `desk_forward._collect_measures` (imported verbatim, zero diff) does the ENTIRE
    truncation-exclusion / per-measure-key grouping job — I only pool the raw per-file
    forward-shaped events across every default-signature file before handing them to it. The rail's
    own `_avg_cell` produces `n`/`mean_pct`/`median_pct`/`n_truncated` but has no p25/p75 at all
    (per the plan's own explicit call-out), so `_quartile_stats` (a small new helper) adds those two
    using `statistics.quantiles(values, n=4, method="inclusive")` — ONE deterministic quantile
    method, proven against TC-1's hand-computed fixture (`[2.0, 4.0, 6.0]` → median 4.0, p25 3.0,
    p75 5.0, mean 4.0, verified against `statistics.quantiles` directly before writing the
    assertion). At `n == 1`, all four readings equal the single value (`statistics.quantiles`
    refuses fewer than two points; repeating the lone value is the only non-fabricating answer).
  - `invalidation_breached`: the FULL cross product of setups × sides × the rail's own horizon
    labels + `to_close` (9 × 2 × 5 = 90 entries), each a plain sum of per-file breach counts already
    computed by `desk_playbook._invalidation_breached` at compute time — no re-derivation of "did
    price breach the level".
  - `inspect_signature(store, signature)` — `?signature=` mode: `{signature, dates, created_span}`
    for ANY named signature (default or not) WITHOUT pooling it into any cell ("inspect, never
    pool"). Not covered by any TC in the spec; implemented per the acceptance text's literal
    description ("optional `?signature=` to inspect a non-default signature's own `dates`/
    `created_span` WITHOUT pooling it") — flagged here for the auditor since it's a good-faith
    interpretation, not test-derived.
  - **`PlaybookEvidenceCache`** — a fresh, small SQLite class mirroring `desk_meta_cache.py`'s
    contract (stat-keyed by `(path, size, mtime_ns)`, `json.dumps` WITHOUT `sort_keys` for
    byte-identical cache-hit vs. fresh-parse serving order, no `update`/`delete` method anywhere —
    structural guard-tested) rather than importing/extending `DeskMetaCache` — the plan explicitly
    calls `desk_meta_cache.py` "the copy-paste precedent", and the evidence projection's shape
    (per-file grouped forward events, not a lightweight meta-only view) doesn't fit that class's
    existing schema without widening a foundation file for one caller. Deleting the cache DB
    changes nothing about `fold_evidence`'s output, only how many files must be re-verified through
    `PlaybookStore.get` (TC-6, proven by an actual `db_path.unlink()` + fresh-cache-instance test).
  - `EVIDENCE_REGISTER` — a new descriptive string (module-level constant), the
    `PLAYBOOK_REGISTER`/`FORWARD_REGISTER` pattern verbatim. **Design note for the auditor:**
    unlike those two precedents (which DO carry "no probability, expectancy, edge, or significance
    claim" as a negated disclosure sentence and pass `find_violations` via its
    negation-clearing rule), `EVIDENCE_REGISTER` deliberately never uses ANY of the six words TC-7
    names (`probability, expectancy, edge, significance, advice, prediction`) at all — a stricter
    reading that satisfies TC-7's literal "contains no word from {...}" wording unambiguously, not
    just the `find_violations` negation-clearing reading.
- **`app/research/desk_routes.py`**: `GET /research/desk/playbook/evidence` (optional
  `?signature=`), `playbook_evidence_cache_db_path()` (env var `TAPEOLOGY_PLAYBOOK_EVIDENCE_CACHE_DB`
  else a sibling of the playbook dir — the `screen_meta_cache_db_path`/`forward_meta_cache_db_path`
  pattern verbatim, deliberately not a `Config` field), `get_playbook_evidence_cache()` (a missing
  optimisation on `sqlite3.Error`, never a failed read — the `ForwardStore._durable_meta_cache`
  rule applied at the dependency layer). Added `import sqlite3` (not previously imported in this
  file). Zero diff to any other route.
- **`apps/backend/tests/test_desk_playbook_evidence.py`** (new, 20 tests): TC-1 (hand-computed
  1h-cell aggregate), TC-2 (cache cold/warm byte-identity via `json.dumps` string equality), TC-3
  (below_min_n with populated numbers), TC-4 (truncation exclusion — a truncated leaf with
  `exit_price=999.0` proven excluded from the mean), TC-5 (two signatures, only default pools),
  TC-6 (cache-DB-deleted rebuild byte-identity), TC-7 (`find_violations(EVIDENCE_REGISTER) == []`
  plus the stricter literal-word-absence check), the full-cross-product/zero-cell error case, the
  `?signature=` inspect-mode behavior (found + unknown), the `PlaybookEvidenceCache` no-update/
  no-delete structural guard, and the wired route end to end (honest-empty body, `?signature=`
  query param). Every hand-crafted fixture record is built directly through `PlaybookStore.record`
  with `forward` leaves produced by the REAL `desk_forward._measure_from` over small synthetic bar
  lists (the `test_measure_signal_and_measure_from_produce_byte_identical_leaves` precedent) —
  never a hand-typed dict shape that could drift from what the rail actually produces.
- **`apps/backend/tests/test_desk_playbook_guards.py`**: retired the iter-4-era forward guard
  `test_desk_playbook_evidence_module_does_not_exist_yet` (the module now exists) and replaced it
  with `test_desk_playbook_evidence_module_now_exists_and_still_imports_nothing_from_detect` — the
  import-graph guard (`desk_playbook_detect.py` imports nothing named `*evidence*`) is now a LIVE
  enforcement rather than a forward one. The "pooling code never merges two signatures into one
  cell" guard is proven behaviorally (TC-5 in `test_desk_playbook_evidence.py`) rather than by a
  new source-scan regex, per this file's own documented precedent that some properties are of DATA
  a fixture proves directly, not code SHAPE a regex would usefully police (see the file's own
  updated module docstring).
- **`apps/backend/tests/test_desk_ui_guards.py`**: `_PRICE_ARITHMETIC_FIELDS` extended with
  `cell.signal.(n|n_truncated|median_pct|p25_pct|p75_pct|mean_pct)`,
  `cell.baseline.(n_baseline|median_pct|p25_pct|p75_pct|mean_pct)`,
  `breach.(breached_count|total_count)` + a matching seeded counter-test
  (`test_desk_page_price_arithmetic_guard_catches_evidence_field_arithmetic`).
- **`test_copy_discipline.py` — deliberately UNCHANGED (zero diff).** The frontend literal-string
  lint (`test_lint_frontend_source_literals_are_clean`) already globs `app/**/*.tsx`, so the new
  Playbook Evidence section's copy is covered structurally with no edit needed. `EVIDENCE_REGISTER`'s
  own copy-lint coverage lives in `test_desk_playbook_evidence.py` via the existing `find_violations`
  import — the SAME per-module precedent `PLAYBOOK_REGISTER`/`FORWARD_REGISTER` use (neither of
  which has its own assertion inside `test_copy_discipline.py` either).

### Five carry items (iter-6/iter-7 ESCALATEs)

1. **Back-scan plan 500 on malformed date — fixed.** `desk_playbook_backscan._planned_dates` now
   catches `ValueError` from `date.fromisoformat` and returns the SAME empty-plan shape the
   already-handled inverted-range case (TC-17) returns (`dates: []`, `total: 0`, `missing: 0`) —
   one `try/except` wrapping the two `fromisoformat` calls, no other change. Tests:
   `test_iter8_tc9_a_malformed_from_date_is_an_honest_empty_plan_not_a_500`,
   `..._malformed_to_date_...`, and a route-level test confirming HTTP 200 (never 500) at
   `GET .../backscan/plan?from=2026-06-2&to=...`.
   > **AUDIT ADDENDUM (goal-playbook-iter-8 audit, finding B1):** "one `try/except` … no other
   > change" was not accurate — `_planned_dates` is also called by
   > `DeskPlaybookBackscanComputeManager.trigger`, so the same change made `POST
   > .../backscan/compute` on a malformed date return `200 started:true` and append a permanent
   > `"done"` run-ledger row (verified by probe). The plan READ keeps this tolerance; the TRIGGER
   > now pre-refuses with HTTP 422 (no job, no ledger row). See
   > `docs/handoffs/goal-playbook-iter-8-audit.md` §2 B1 and §4.
2. **`journey-scripts/J-05.json` step-2 assertion fixed.** Was `{"text": "Capitulation"}` — matched
   the ROW label AND the section's own static description paragraph ("...cup-and-handle,
   capitulation, range-trade...") because `demo_runner.py`'s text matcher (`page.get_by_text`) is
   case-insensitive substring, and "capitulation" (lowercase, no punctuation) collides exactly with
   "Capitulation" (the only setup name where this collision is real — every OTHER setup label
   differs from its static-prose form by spacing/hyphenation, e.g. "Jump-Base Explosion" vs.
   "jump-base-explosion"). Fixed to
   `{"target": {"css": "[data-testid=\"desk-playbook-signal-setup\"]:has-text(\"Capitulation\")"}}`
   — scoped to the per-signal-row `<td>` (only rendered when an actual capitulation signal fires),
   using Playwright's CSS `:has-text()` extension via the `"css"` target kind `demo_runner.py`
   already supports. **Proven live, not just linted:** (a) `--mode verify` against the real scoped
   rig at 2026-06-22 (DECOR's own capitulation signal) — PASS; (b) a deliberately fixture-mismatched
   copy of the script pointed at 2026-06-23 (no capitulation signal that date) — FAIL, confirming
   the new assertion genuinely discriminates real evidence from static copy (TC-13).
3. **`journey-scripts/J-06.json` recorded (new).** 4 steps: goto `/desk` → fill `2026-06-22` →
   expect a real `Range Trade` signal row (same CSS-`:has-text()` scoping pattern) → click "RTAAA"
   → expect `desk-playbook-signal-range-trade-geometry` → click "Double Top" (NOT "DTAAA" — DTAAA
   fires BOTH an `open_high_break` signal at 09:45 AND a `double_top` signal at 11:00 in this rig,
   and the earlier-triggering row sorts first, so clicking the symbol text alone hit the wrong row
   on the first attempt; the chip text "Double Top" is unambiguous) → expect
   `desk-playbook-signal-double-extreme-geometry`. `--mode lint` clean; `--mode verify` against the
   scoped rig — PASS (see Tests Run).
4. **Owed Range Trade row re-capture — delivered.** Fresh `rm -rf apps/frontend/.next` rebuild,
   scoped rig, RTAAA row expanded — the full geometry line legible: "range 5.00 MBR wide · low zone
   touches 2 · high zone touches 2 · broke at slot 7 · crossed midrange" (captured via a
   `fullpage: true` CDP screenshot, cropped to the row — see Known Issues for why `fullpage` was
   necessary).
5. **Replay lane scoped — `qa_playbook_iter7_fixture_scoped_backend.sh` extended in place** (per
   this iteration's own instruction: extend the launcher forward, never rewrite it, so it stays the
   SINGLE mandatory launcher). Added `TAPEOLOGY_PLAYBOOK_EVIDENCE_CACHE_DB` scoping, switched the
   seed entry point to `seed_playbook_iter8_evidence_fixture.py` (below), and changed the default
   root to `playbook-iter8-fixture-qa` (a genuinely fresh root — the script's own long-standing
   rule: use a fresh root whenever the seeded composition changes). **Verified (TC-11):**
   `find apps/backend/.data -newermt "<run start>" -type f` returned ZERO files after running the
   full J-05/J-06/J-07 replay set plus the browser evidence captures above — nothing landed in the
   operator's real store.
- **`apps/backend/scripts/seed_playbook_iter8_evidence_fixture.py`** (new): reuses
  `seed_playbook_iter7_backscan_fixture.main()` verbatim, then plants TWELVE new members
  (`OHB01`..`OHB12`, the SAME canonical open_high_break-firing session `BSCAN` already uses) on a
  **fresh date, 2026-06-25** — deliberately NOT 2026-06-22. The first version of this script reused
  2026-06-22, which recorded a NEW version for that date under the (now current) 16-member
  signature and silently broke the ALREADY-PASSING J-07 golden's own "3 missing at the current
  signature" assertion (dropping it to 2) as a side effect of an unrelated fixture addition — caught
  by running the full regression sweep before finalizing, fixed by moving the evidence corpus to a
  date outside J-07's own `[2026-06-22, 2026-06-24]` range. Registers a sixteen-member universe
  snapshot and records ONE playbook compute for 2026-06-25 — the evidence fold's
  `(open_high_break, long, *)` cells clear `PLAYBOOK_MIN_N_DISCLOSURE` (12) exactly at the
  shorter-horizon measures (5m/to_close/mdd_*), while 1h/4h stay empty (the 6-bar OHB sessions
  truncate before a 1h offset) — giving TC-8's own "one well-populated cell and one below_min_n
  cell" shape in the SAME `(setup_id, side)` block, adjacent rows, with zero extra fixture work.

## Files Changed

- `apps/backend/app/research/desk_playbook_evidence.py` -- new: fold/cache/register (J-08 core)
- `apps/backend/app/research/desk_routes.py` -- wire `GET /research/desk/playbook/evidence`
- `apps/backend/app/research/desk_playbook_backscan.py` -- `_planned_dates` malformed-date fix
- `apps/backend/tests/test_desk_playbook_evidence.py` -- new, 20 tests (TC-1..TC-7 + guards + route)
- `apps/backend/tests/test_desk_playbook_backscan.py` -- 3 new malformed-date tests
- `apps/backend/tests/test_desk_playbook_guards.py` -- forward guard retired/replaced (module now exists)
- `apps/backend/tests/test_desk_ui_guards.py` -- `_PRICE_ARITHMETIC_FIELDS` extended + counter-test
- `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` -- extended: evidence cache
  scoping var, new seed entry point, fresh default root name
- `apps/backend/scripts/seed_playbook_iter8_evidence_fixture.py` -- new: evidence corpus seeding
- `apps/frontend/app/desk/page.tsx` -- new Playbook Evidence section (see frontend handoff)
- `apps/frontend/lib/api.ts` -- `fetchDeskPlaybookEvidence`
- `apps/frontend/lib/types.ts` -- `DeskPlaybookEvidence*` types
- `runs/goal-session-playbook/journey-scripts/J-06.json` -- new golden replay script
- `runs/goal-session-playbook/journey-scripts/J-05.json` -- fixed step-2 assertion

### Files changed by the FIX pass (audit B2)

Framework (vendored engine — `scripts/` is not a rendered `.claude/` mirror, so no re-render needed):

- `incredible_auto_dev/scripts/automation/store-scope/store-scope.sh` -- NEW: the require/snapshot/
  verify guard; a no-op for any project without a `store-scope.env`
- `incredible_auto_dev/scripts/automation/lib/replay-lane.sh` -- the three wrappers
- `incredible_auto_dev/scripts/automation/browser-qa-phase.sh` -- require+snapshot before both
  lanes, refusal → REL-14 token + no dispatch, verify + breach disclosure after the merge
- `incredible_auto_dev/scripts/automation/goal-iter-lean.sh` -- the same at lean depth (state
  serialized across the SPEED-2 fork boundary)
- `incredible_auto_dev/scripts/automation/run-evals.sh` -- registers the new test
- `incredible_auto_dev/tests/automation/test-store-scope-guard.sh` -- NEW: 25 assertions

Project:

- `project-extensions/store-scope/store-scope.env` + `README.md` -- NEW: protected paths + the two
  project-owned commands, and why the derived caches are deliberately excluded
- `apps/backend/scripts/assert_scoped_qa_backend.py` -- NEW: the scoped-backend assert
- `apps/backend/scripts/start_scoped_qa_backend.sh` -- NEW: the prepare command
- `apps/backend/scripts/seed_playbook_iter8_replay_rig.py` -- NEW: the rig layer that makes all
  eight required goldens replayable on one backend
- `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` -- extended forward again (new
  seed entry point, fresh default root, stale OHB-date comment corrected)
- `apps/backend/tests/test_qa_scoped_backend_guard.py` -- NEW: 5 tests for the assert classifier
- `apps/backend/tests/test_desk_playbook_evidence.py` -- +2 tests: the baseline half of the fold (T1)
- `runs/goal-session-playbook/journey-scripts/J-04.json` -- date → 2026-08-07, assertions row-scoped
- `runs/goal-session-playbook/state/iteration-state.md` -- "do not redo": the four polluted
  real-store artifacts, the guard, and the rig's new fixture coverage
- `reports/qa/goal-playbook-iter-8-store-scope-guard.md` + 10 evidence PNGs -- NEW artifacts

**No frontend source was touched in the fix pass** (`apps/frontend/**` is byte-identical to the
initial pass), so `docs/handoffs/goal-playbook-iter-8-frontend.md` still stands as written.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest -q`
Result: **2147 passed, 8 skipped, 0 failed** (iter-7 floor was 2131 passed / 8 skipped — the DoD's
own `≥ 2130` floor cleared; net +16 including the new evidence/backscan tests).
`Config().config_fingerprint()` still prints `08e471b10130e1e2` (verified directly, unchanged).

Live browser / golden-replay verification (scoped rig, `qa_playbook_iter7_fixture_scoped_backend.sh`,
:8301/:3301, `rm -rf apps/frontend/.next` rebuild first per T-9):
- `demo_runner.py --mode lint` — J-05.json, J-06.json: clean.
- `demo_runner.py --mode verify --journeys J-05,J-06,J-07` — **3/3 PASS** (evidence at
  `/tmp/j-all-evidence2/`, not committed — ephemeral dev verification, the browser-qa-agent's own
  pass produces the committed evidence).
- J-05's fixture-mismatched counter-run (2026-06-23, no capitulation signal) — **1/1 FAIL**,
  proving TC-13's discrimination.
- `GET /research/desk/playbook/evidence` live over HTTP — verified cell shape, 270 cells, the
  `(open_high_break, long, 5m)` cell at `n=12` (well-populated) beside `(open_high_break, long,
  1h)` at `n=1, below_min_n=true` — TC-8's own shape, confirmed both via curl and via a live
  Chrome-CDP screenshot of the rendered `/desk` page (fullpage capture, cropped).
- `GET .../backscan/plan?from=2026-06-2&to=2026-06-24` live over HTTP — HTTP 200, honest empty
  plan (TC-9).
- TC-11: `find apps/backend/.data -newermt <run start> -type f` — zero results after the full
  replay/browser session.
- Frontend: `npx tsc --noEmit` — zero errors.

## Known Issues

- **J-01/J-02/J-03/J-04/J-10's existing golden scripts are STALE relative to the now-properly-scoped
  replay lane** (this iteration's own carry item 5) — they fail `--mode verify` against the scoped
  rig (`J-01`/`J-03` expect "is not a recorded trading session" for dates that only the operator's
  real daily-bar history can prove non-session; `J-02` expects an "Open-Low Break" signal on
  2026-08-07 that only exists in the real store; `J-04` expects "Jump-Base Explosion" on a date not
  seeded here; `J-10` expects a real AAPL price "300.11" from the kept cockpit/structure surfaces).
  **This is a PRE-EXISTING condition my scoping fix REVEALED, not one I introduced**: no scoped
  fixture rig existed before iter-6, so these five goldens were necessarily authored/verified
  against the operator's real ambient backend at the time — iter-7's own QA report shows them
  PASSING, which is only possible if that pass ran unscoped (exactly the hole carry item 5 closes).
  I did NOT touch these four scripts — extending the fixture rig to cover their specific historical
  scenarios (a provable non-session date, a specific Open-Low Break firing, etc.) was not in this
  iteration's IN SCOPE list (only the J-05 fix and J-06 recording were), and inventing plausible
  substitute fixtures for scripts I don't own risks masking a REAL future regression behind a
  fabricated pass. The underlying BEHAVIORS these scripts exercise are still covered and passing in
  the hermetic unit suite (`test_desk_playbook.py`'s own non-session-refusal/absence tests,
  `test_desk_playbook_detect.py`'s Open-Low Break fixtures, `test_desk_forward.py`'s forward
  measurement). Per the DoD's own "LLM fallback where a golden is missing/stale" allowance, these
  five should route through the LLM lane this iteration (or be re-recorded against an extended
  fixture rig in a future iteration) — flagged for the QA/browser-qa-agent/auditor rather than
  silently worked around.
- **The evidence corpus on the scoped rig is not a fixed constant across a whole browser-QA
  session.** `J-07`'s own "Run Backscan" click (a legitimate action inside its own golden) computes
  and records 2026-06-22/23/24 under the CURRENT signature, which then feeds MORE signals into the
  evidence fold on any SUBSEQUENT `/desk` load (the well-populated cell's `n` grows from 12 to ~14
  after J-07 has run once in the same session). This is by design — the evidence view pools
  whatever the store has currently recorded — but it means the EXACT numbers a browser-QA pass
  screenshots depend on which OTHER playbook-touching journeys already ran in that session. TC-8's
  qualitative requirement (one cell `n >= 12`, one `below_min_n`) holds either way.
- **A CDP viewport-screenshot quirk in this headless Chrome session**: a plain (non-fullpage)
  `screenshot` action taken AFTER any non-zero `scrollY` returned a blank/flat frame consistently
  (confirmed at scrollY=900 and scrollY=2264; a screenshot at scrollY=0 worked fine). Worked around
  by using `fullpage: true` (a different CDP capture path) and cropping in Python/PIL to the
  relevant region. Flagging this as a landmine for the browser-qa-agent's own pass, alongside the
  existing `[chrome-mcp-cdp-port-9222]`/`[headless-chrome-throttles-live-chart]` lessons.
- `test_desk_refresh_chain_guard.py` needed NO diff — the evidence fetch was joined into the
  EXISTING mount-time effect (one more `.then()` inside the same `useEffect` body) rather than
  opening a new one, so the page's own effect/interval/trigger census is unchanged. Verified: the
  guard test still passes byte-unmodified.

## Fix Notes (audit FAIL — B2 + the three unmet DoD items)

**Date:** 2026-08-11 · **Mode:** fix (audit report: `docs/handoffs/goal-playbook-iter-8-audit.md`)

The audit passed J-08's pooling math end to end and fixed B1 itself. It FAILED the iteration on ONE
critical finding and the three DoD items that hang off it:

| Audit item | Status after this pass |
|---|---|
| **B2 (CRITICAL)** — the replay/QA lane ran UNSCOPED and wrote to the operator's real store; TC-11 unmet | **FIXED** — scoping is now a mechanism with a gate, not a launcher (below) |
| **DoD 7** — replay lane scoped, `find .data -newermt` shows zero new files | **MET** — proven by an executed guard: `reports/qa/goal-playbook-iter-8-store-scope-guard.md` = `CLEAN` |
| **DoD 2** — required-still-passing J-01..J-07 + J-10 green | **MET** — 8/8 PASS in ONE deterministic replay run on ONE scoped backend |
| **DoD 6** — J-06 golden replay-verified on the scoped rig | **MET** — inside that same 8/8 run |
| **T1 (gap)** — the baseline half of the fold has no unit coverage | **FIXED** — two new tests (the audit called this optional; it is two tests and closes a load-bearing key agreement) |
| B3/B4/B5/B6/B7, F1/F2 (gaps + observations) | **NOT touched** — the audit itself parks the register wording for J-09's iteration and calls F1 a spec decision; fix mode changes only what the report lists as broken |
| B1, T2 | already fixed by the auditor; untouched |

### 1. Scoping is now a mechanism (B2)

The auditor's root cause was exact: *"the deliverable is a launcher script, not a mechanism …
nothing obliges the replay lane to use it."* The obligation now lives where BOTH browser lanes pass
— they drive the same browser at the same frontend, so an LLM dispatch can write into the real store
exactly as a golden replay can.

- **`incredible_auto_dev/scripts/automation/store-scope/store-scope.sh`** (new, framework): three
  verbs. `require` runs the project's assert command, runs its prepare command ONCE if the assert
  fails, re-asserts, and returns non-zero if the backend still is not the scoped rig. `snapshot`
  manifests every file (size + mtime_ns) under the project's declared protected paths.
  `verify` re-scans and fails on ANY delta — added, removed, or modified — writing a disclosure
  artifact either way. **Absent `project-extensions/store-scope/store-scope.env` ⇒ every verb is a
  no-op exiting 0**, so every other project on this engine is byte-identical (the host-guard
  precedent).
- **`lib/replay-lane.sh`**: `store_scope_require` / `store_scope_snapshot` / `store_scope_verify`
  wrappers (the `bqa_browser_confine` shape), no-ops when the guard script is absent.
- **`browser-qa-phase.sh` + `goal-iter-lean.sh`**: require + snapshot BEFORE the replay lane and the
  LLM dispatch; verify AFTER the merge. A refusal rides the existing REL-14 path —
  `FRONTEND_AVAILABLE=no` + a `browser-infra.json` token with reason `store-scope` — so the journeys
  are recorded pending-infra and **can never be reported as verified by a lane that did not run**. A
  breach appends a loud `## Store-scope breach` section to the authoritative `ui-test-results.md`
  and emits a `store_scope_breach` telemetry event; it deliberately does not exit, because the
  verdicts still have to be published for anyone to read the disclosure.
- **`tests/automation/test-store-scope-guard.sh`** (new, registered in `run-evals.sh`): 25 assertions
  — the neutral no-op path, assert-decides, prepare-rescues, refusal, CLEAN, and **the iteration-8
  failure reproduced**: a new record file + a new ledger file under a protected path ⇒ `BREACH` naming
  both. Written before the implementation (all 25 failed rc 127 first).
- **Project side**: `project-extensions/store-scope/store-scope.env` (+ README),
  `apps/backend/scripts/assert_scoped_qa_backend.py` (pure `scoped_verdict` classifier + 5 unit
  tests in `tests/test_qa_scoped_backend_guard.py`; the marker is the served universe snapshot's own
  `source_url` — `fixture-rig*` for every seeder, the Wikipedia S&P-100 URL for the real store; every
  unproven case fails closed) and `apps/backend/scripts/start_scoped_qa_backend.sh` (frees the QA
  port, recording the replaced listener's command line in `<log-dir>/replaced-listener-<port>.txt`
  beside the root — never inside it, which an earlier draft got wrong: the fresh-root wipe deleted
  its own disclosure — then seeds
  a fresh root through the ONE mandatory launcher).

  Protected paths are the append-only stores only — playbook, playbook_runs,
  playbook_backscan_runs, universe, screen, screen_runs, forward, forward_runs, topup_runs,
  index_reconcile_runs, bars, datasets. The derived accelerator DBs are deliberately excluded (a
  read path legitimately updates them; listing them would make every clean run a false breach, and a
  guard that cries wolf gets ignored).

  **Proven to discriminate, not just to pass**: run against the operator's real backend the assert
  printed `NOT SCOPED … source_url='https://en.wikipedia.org/wiki/S%26P_100' (member_count=101) —
  a browser lane here would read and write the operator's real store` and returned 1. That is the
  exact configuration this iteration's own replay ran against.

### 2. One backend on which all eight required journeys pass (audit next step 2)

The audit: *"on the ambient backend J-05/J-06 fail; on the scoped rig J-01/J-02/J-03/J-04/J-10 fail
… no configuration exists on which all eight required journeys pass."* Closed by extending the rig,
not by re-pointing the goldens at whatever happens to be seeded:

- **`apps/backend/scripts/seed_playbook_iter8_replay_rig.py`** (new; reuses the iter-8 evidence
  seeder's `main()` verbatim, which reuses iter-7's, which reuses iter-6's):
  - `CALDR` — a member holding ONLY daily bars, one per weekday from 2024-01-02 to 2026-08-14.
    `desk_sessions` derives "is this a trading session" solely from recorded daily bars, and the rig
    had none, so `is_known_non_session` could never answer True and **J-01's and J-03's refusal
    assertions were structurally unreachable on any fixture rig**. Both asserted dates (2026-06-13,
    2024-01-06) are Saturdays inside the anchor's span; every fixture session date is a planted
    weekday. Verified date by date.
  - `OLBRK` / `JBEXP` / `DBIMP` on **2026-08-07** — the canonical open_low_break / JBE / DBI
    sessions copied bar-for-bar from `tests/test_desk_playbook_detect.py`. The date is forced:
    2026-06-22 cannot carry them, because recording that date at the current signature would flip
    J-07's own "3 missing at the current signature" to 2 and break a passing golden.
  - every **AAPL** series copied verbatim (read-only) from the operator's real bar store, so J-10's
    `/structure` step measures the KEPT PRODUCT rather than a fixture. Confirmed offline:
    `compute_levels(AAPL, as_of 2026-06-22T23:59:59Z)` on the rig contains `300.11`, the exact
    string J-10 asserts. A synthetic substitute would have turned the sentinel into a test of the
    fixture — the one thing the iter-8 dev handoff rightly refused to do.
  - one new nineteen-member universe snapshot (`source_url=fixture-rig-iter8-replay`), then TWO
    computes: 2026-06-25 re-keyed at the new signature (the evidence fold pools the DEFAULT
    signature only) and 2026-08-07. Append-only — the earlier versions stay on disk untouched.
- **`qa_playbook_iter7_fixture_scoped_backend.sh`** extended in place again (still THE one
  launcher): new seed entry point, fresh default root `playbook-iter8-replay-fixture-qa`. Also
  corrected its own stale comment that claimed the OHB members fire on 2026-06-22 (the iter-8
  seeder moved them to 2026-06-25 and the comment never followed).
- **`runs/goal-session-playbook/journey-scripts/J-04.json`** — the only golden edited: date
  2026-06-22 → 2026-08-07, and its two assertions upgraded from bare text to the row-scoped
  `[data-testid="desk-playbook-signal-setup"]:has-text(...)` selector J-05/J-06 already use, so a
  fixture-mismatched replay cannot pass on static section copy. J-02's golden needed NO edit — it
  already types 2026-08-07.

### 3. Evidence from this pass

```
store-scope require   → prepare replaced the ambient listener, re-assert SCOPED (fixture-rig-iter8-replay, 20 members)
demo_runner --mode lint    J-01..J-07,J-10  → 8 ok
demo_runner --mode verify  J-01,J-02,J-03,J-04,J-05,J-06,J-07,J-10
                       → 8 journey(s), 0 failed (verdict: PASS), 34s
store-scope verify    → CLEAN (9841 protected files before == 9841 after, sizes+mtimes unchanged)
```

- `reports/qa/goal-playbook-iter-8-store-scope-guard.md` — the CLEAN disclosure (TC-11 as an
  executed gate rather than a claim).
- `reports/qa/goal-playbook-iter-8-evidence/fix-scoped-replay-results.md` — the 8/8 results table
  from this pass, copied out of the run TMPDIR under a name that cannot be confused with a lane
  artifact. **The pipeline's own `reports/phase-goal-playbook-iter-8-regression-replay-results.md`
  was deliberately NOT edited**: it is the honest record of the PRE-fix run (`FAIL 6/8`, the one the
  audit's T3 cites), and the lane deletes and rewrites it at the start of its next run
  (`replay_lane_partition_and_verify`'s stale-artifact hygiene). Overwriting another lane's artifact
  by hand is exactly the kind of tidy-up that makes a record unreadable.
- `reports/qa/goal-playbook-iter-8-evidence/fix-scoped-replay-J-0{1..7}.png`, `…-J-10.png` — the
  replay's own per-journey captures, copied out of the run TMPDIR into the repo (the audit's T2
  lesson: `/tmp`-only evidence does not survive).
- `reports/qa/goal-playbook-iter-8-evidence/fix-scoped-rig-J-02-J-04-signals-2026-08-07.png` — the
  2026-08-07 record on the rig: Open-Low Break (J-02) and Jump-Base Explosion + Drop-Base Implosion
  (J-04) rows legible, with the record id, its signature, and the unchanged `08e471b10130e1e2` pin
  in frame.
- `reports/qa/goal-playbook-iter-8-evidence/fix-scoped-rig-J-08-evidence-cells.png` — TC-8's shape
  re-confirmed on the NEW rig: `open_high_break long 5m` at `n=15` (no tag) directly above
  `open_high_break long 1h` at `n=1` carrying the `low n` tag with its numbers still served.

### 4. Known issues after the fix

- **The deep-scroll screenshot quirk is real and recurred**: a plain CDP viewport screenshot after a
  non-zero `scrollY` returns a flat frame. Both crops above were taken from a `fullpage: true`
  capture. Same landmine the initial pass flagged — worth carrying into the next browser dispatch.
- **The evidence corpus still moves within a browser session** (unchanged, by design): J-07's own
  "Run Backscan" click records 2026-06-22/23/24, so `open_high_break long 5m` read `n=13` before the
  replay set and `n=15` after. TC-8's qualitative shape (one cell ≥ 12, one tagged) holds either way.
- **A breach does not abort the pipeline.** `store_scope_verify` discloses loudly (report + results
  section + telemetry) and lets the run finish, so the evidence is published rather than swallowed by
  a silent abort. If the project later wants a breach to be terminal, that is a one-line change at
  both call sites — deliberately not made here without a spec decision.
- **The guard cannot make the LLM lane's own browser calls scoped after the fact.** It refuses the
  dispatch when the backend is unscoped, which is the strongest thing available without a new
  disclosure contract for the agent itself.
- **T3 (the QA report certifying what its own artifacts contradicted) is not a dev-fixable defect.**
  What this pass could do about it is make the claim checkable by machine: the store-scope disclosure
  artifact + the 8/8 replay results are now files a reviewer can read instead of prose to trust.
- **NEW problem found while fixing, deliberately NOT fixed here** (fix-mode discipline — recorded so
  the reviewer/auditor can triage it): `incredible_auto_dev/hooks/post-write-artifact-quality.sh:42`
  crashes its own arithmetic test on any `reports/phase-*` file that is CLEAN. `VAGUE_MARKERS=$(grep
  -icE ... || echo 0)` yields the two-line string `0\n0` when `grep -c` finds nothing (it exits 1
  after printing `0`, so the `|| echo 0` appends a second), and `[[ "$VAGUE_MARKERS" -gt 2 ]]` then
  prints `arithmetic syntax error`. Advisory-only (the hook always exits 0) and pre-existing —
  `reports/phase-goal-playbook-iter-7-implementation-summary.md` does NOT trip it because it happens
  to contain a matching line. One-line fix (`| head -1` or `grep -c ... ; true`), out of scope here.

## Environment

**State as of the end of the FIX pass (this is the current truth — the paragraph below it describes
the initial pass and is kept for the record):**

- `:8301` — the OPERATOR'S REAL backend, restored exactly as the fix pass found it
  (`CHAIN_BACKEND_PORT=8301 bash scripts/start-backend.sh`, no `TAPEOLOGY_*` overrides; health 200,
  serving the 101-member S&P-100 universe). `assert_scoped_qa_backend.py` correctly reports it
  **NOT SCOPED**, which is the honest state, not a fault.
- `:3301` — frontend, healthy (unchanged; no frontend source was touched in the fix pass, so no
  rebuild was needed and none was done — `npm run build` was deliberately not run against the live
  dev server's `.next`).
- `:9222` — the isolated headless Chrome, still holding CDP.
- The operator's real `apps/backend/.data/` store: **verified CLEAN** by the store-scope guard
  across this entire pass (`reports/qa/goal-playbook-iter-8-store-scope-guard.md`; 9,841 protected
  files before == after, sizes and mtimes unchanged).

**The next browser/replay lane does not need any manual setup**: `store_scope_require` runs the
prepare command itself, which swaps `:8301` to the fixture rig (recording what it replaced in
`<log-dir>/replaced-listener-8301.txt`), and the operator restarts their own backend with the same
one-liner above afterwards. To stand the rig up by hand:

```bash
bash apps/backend/scripts/start_scoped_qa_backend.sh          # ~25s: seed + health
bash incredible_auto_dev/scripts/automation/store-scope/store-scope.sh require   # proves it
```

_Initial pass (2026-08-11, pre-audit) left: scoped backend at `:8301`
(`qa_playbook_iter7_fixture_scoped_backend.sh /tmp/playbook-iter8-fixture-qa 8301`), frontend at
`:3301`, Chrome CDP at `:9222`, and claimed the real store was never touched — the audit's finding
B2 showed that claim was wrong for the pipeline's own replay run, which is what the fix pass above
addresses._

## Tests Run (fix pass)

Command: `cd apps/backend && .venv/bin/python -m pytest -p no:warnings`
Result: **2157 passed, 8 skipped, 0 failed** (exit 0) — up from the audit's 2150/8 by exactly the
7 tests this pass added (5 scope-assert classifier + 2 baseline-pooling). Clears the DoD floor
(≥ 2130) with 8 skipped exactly.
`Config().config_fingerprint()` → `08e471b10130e1e2`, unchanged.

Framework side: `bash incredible_auto_dev/scripts/automation/run-evals.sh` → **152 pass, 0 fail**
(includes the new `test-store-scope-guard.sh`: 25 assertions), and the pre-existing lane suites
`test-replay-lane` (59), `test-replay-lane-full` (24), `test-goal-parallel-bqa` (103),
`test-browser-infra-makeup` (27), `test-golden-autoderive` (22), `test-iter-budget` (33) all still
pass unchanged.

# goal-clean_slate-iter-0 Dev Handoff

**Phase:** goal-clean_slate-iter-0
**Date:** 2026-07-23
**Agent:** developer
**Status:** complete

## What Was Built

Nothing — by design. This is "The Clean Slate" demolition interlude's **verify-only baseline** (Mode:
baseline, Depth: lean). The spec's BACKGROUND section states the developer step is an explicit no-op
("the developer step is a no-op here; all the value comes from the browser-qa step exercising every
Must-have journey"); the entire scope was executing the spec's read-only Verification scope checklist
against the current codebase and a live scratch backend/frontend, and recording the evidence below so
the goal-evaluator can mark passing/failing/partial for each of J-01–J-05.

**No source file was created, modified, or deleted this iteration.**

```
$ git status --short -- apps/
(empty)
$ git diff --stat -- apps/
(empty)
$ git status --short
?? docs/phases/goal-clean_slate-iter-0.md
?? reports/security/
?? runs/goal-session-clean_slate/
```

All three untracked entries are pipeline/session artifacts, not product source: the iter spec itself,
`runs/goal-session-clean_slate/` (goal-mode session state, written by the decomposer before this
developer step ran), and `reports/security/install-decisions.jsonl` (a pre-existing untracked file from
an earlier, unrelated security-audit skill run — not touched or created by me this iteration). This
confirms TC-9 and the DoD's "no anti-goal violation introduced" item directly: zero files under
`apps/backend/` or `apps/frontend/` are touched.

## Route-count reconciliation (per the spec's own NOTES section)

Confirmed the spec's flagged discrepancy: `docs/goal.md`'s Vision/Success-Criteria prose says "15
journal-era routes," but a direct grep of the running route table finds exactly **14** journal-era
`@router.get/post` decorators (matching the I-1 DELETE table's 14 rows exactly) plus the ONE separately
tracked SLIM route (`GET /research/taxonomy`, not a 15th delete):

```
$ grep -n '@router\.\(get\|post\)(' apps/backend/app/research/routes.py
```

lists 36 total registered routes; excluding `/taxonomy` (SLIM), exactly 14 are journal/thesis/hint/
studies/analytics routes, and the remaining 21 are KEEP routes (datasets/bars/candles/levels/
tradability/setups/backtests/pnl/profiles/strategies/edge-report). No 15th route exists. Per T-14, this
is a documented reconciliation, not a new inventory contradiction — the I-1 table (14 rows) is ground
truth, exactly as the spec's NOTES anticipated.

## Journey-by-journey verification evidence

Live checks ran against a scratch dev-stack instance (`bash scripts/dev.sh`, deterministic ports
`8301`/`3301` — this project's own offset, distinct from an unrelated `trendora` project's processes
found running on `8255`/`3255`, which were left untouched). Static checks ran directly against the
source tree. The spec's baseline predictions (J-01–J-04 failing, J-05 kept-behaviors intact) were
**confirmed on every point**.

### J-01: Backend demolition with byte-identical relocations — CONFIRMED FAILING (not started)

**TC-1** (four representative I-1 routes, expect 200 not 404):

| Route | Observed |
|---|---|
| `GET /research/analytics` | **200** |
| `GET /research/journal` | **200** |
| `GET /research/studies` | **200** |
| `GET /research/hints` | **200** |

All four still serve their existing content (not 404) — J-01's route deletions have not happened.
Extra GET-only spot checks: `/research/hints/active` and `/research/thesis/active` both return **422**
(missing a required query param, e.g. `ticker`) — still proves the route is registered (not a 404),
just not called with the args a real client would pass; `/research/taxonomy` returns **200** with the
CURRENT, un-slimmed payload (14,021 bytes; top-level keys include `analytics, checklist_absence,
checklist_checks, checklist_stances, directions, disclaimer, excursions, feed_basis, hints,
management_stances, mistake_tags, monitor_statuses, outcome_grades, process_grades, resolutions,
risk_flags, setups, sound_cue, stance_absence, stance_readout_caption, statement_statuses, statuses,
studies, verdicts` — every thesis/verdict/stance/study family the I-2 SLIM row targets for deletion is
still present alongside `feed_basis`, the one family that survives).

**TC-2** (module-import grep): all eleven I-2 DELETE-list modules still exist as files and are still
imported somewhere live:

```
journal_rows.py (75 lines) monitor.py (1382) hints.py (254) stance.py (603) verdict.py (434)
grades.py (154) marks.py (84) excursions.py (362) execution_checks.py (316) analytics.py (254)
studies.py (865)
```

A direct `routes.py` import grep finds 8 of the 11 as direct `from .X import` lines (`analytics`,
`excursions`, `execution_checks`, `grades`, `journal_rows`, `marks`, `monitor`, `studies`); the other
three (`hints`, `stance`, `verdict`) are imported transitively through `monitor.py` per I-2's own
importer table, not directly by `routes.py` — consistent with the inventory, not a contradiction.

**Relocations confirmed NOT started** (direct citations):
- `marks.py:27` still defines `def r_basis(...)`; `backtests.py:102` still does
  `from .marks import r_basis` (the pre-relocation import direction the I-2 RELOCATE row will invert).
- `studies.py:101/103/107` still define `SOURCE_REFERENCE`/`SOURCE_HISTORICAL`/`REFERENCE_SOURCE_ID`;
  `datasets.py:69-70` still does `from .studies import SOURCE_HISTORICAL, SOURCE_REFERENCE` and
  `from .studies import _load_reference_window as _load_reference`; `pnl_baseline.py:43` still does
  `from .studies import REFERENCE_SOURCE_ID, SOURCE_REFERENCE`; `test_studies_reference.py:26,158`
  still imports `StudyJobManager`/`_load_reference_window` from `app.research.studies` — all four
  confirm the pre-relocation import direction the RELOCATE row will invert.

**I-2 SLIM/other targets confirmed not yet touched:** `ResearchRegistry` in `routes.py` still defines
`study_jobs` (294), `hint_projection_for` (375), `on_engine_created` (309), `startup_sweep` (385);
`main.py:157,160,191` still wires `manager.set_on_engine_created(registry.on_engine_created)` /
`registry.startup_sweep()` / the shutdown unset.

**All ~24 I-8 DELETE-list test files and all guard tests confirmed present** (`test_analytics.py`
through `test_verdict_engine.py` — none missing; `test_no_execution_path.py`,
`test_no_credential_in_artifacts.py`, `test_cockpit_chart_upgrade.py`,
`test_structure_chart_viewport.py`, `test_price_chart_confluence.py` all present). The six I-8
UPDATE-target files (`test_mcp_server.py`, `test_meta_routes.py`, `test_copy_discipline.py`,
`test_research_api.py`, `test_research_store.py`, `test_studies_reference.py`, `conftest.py`) all
exist in their current (pre-update) form.

`config_fingerprint` (live-computed): `4d665603569b9dbf` — the OLD/current pin, matching J-01's
acceptance requirement that it stay unchanged through this journey.

### J-02: Frontend + WS demolition — CONFIRMED FAILING (not started)

Dev-level code/API/SSR inspection only — the browser-qa-agent's step per TESTING REQUIREMENTS covers
the actual click-through (T-13: no screenshot ⇒ `unknown`, never `passing`).

- Pages: `apps/frontend/app/journal/` (`page.tsx` + `[id]/`), `app/studies/page.tsx`,
  `app/performance/page.tsx` all **present**.
- Components: all 11 I-7 DELETE-list components present (`JournalTable`, `JournalDetailView`,
  `JournalFilterBar`, `ThesisStrip`, `HintDock`, `HintLog`, `SoundCue`, `StudyList`,
  `StudyCreateForm`, `StudyResultsView`, `AnalyticsView`).
- `lib/api.ts`: all 14 DELETE-list functions present (`declareThesis` through `cancelStudy`) plus the
  KEEP `fetchTaxonomy` (line 414) — confirms nothing has been touched yet.
- `lib/types.ts`: `ThesisVerdict`, `ThesisStatement`, `ThesisMarks`, `ThesisGeometry`,
  `ThesisProjection`, `Hint` all still exported. `TapeSnapshot` (the WS frame type `useTapeStream.ts`
  returns — the hook itself has no literal "thesis"/"hint" string; the fields live on this interface)
  still carries `thesis?: ThesisProjection | null` and `hint?: Hint | null` — the exact two fields
  I-7/J-02 must drop. **Precision note for whoever builds J-02:** the goal.md phrase "lib/
  useTapeStream.ts: the frame type drops thesis/hint" means `TapeSnapshot` in `types.ts`, not literal
  text inside `useTapeStream.ts` — worth knowing up front to avoid a wasted grep.
- `main.py:602,607,614,626` still has `frame["thesis"] = _thesis_projection(ticker)`,
  `frame["hint"] = _hint_projection(ticker)`, and both helper functions.
- `Cockpit.tsx:6,43` still imports/renders `HintDock`; `app/page.tsx:23-24,288,309` still imports/
  renders `ThesisStrip`.
- Live `GET /meta/ui-routes` returns exactly **6** entries (Cockpit `/`, Journal `/journal`, Journal
  detail `/journal/[id]` non-nav, Studies `/studies`, Performance `/performance`, Structure
  `/structure`) — not yet the target 2-row (Cockpit + Structure) nav.

### J-03: MCP contract v2 — CONFIRMED FAILING (not started)

**TC-4**: `app/mcp/__init__.py`'s `_TOOL_PATHS` still registers `"journal"` (86), `"analytics"` (87),
`"studies"` (88) alongside `"taxonomy"` (94, KEEP) and the 14 other kept paths; the `types.Tool` blocks
for `journal` (176), `analytics` (181), `studies` (186) are all still present. `tests/
test_mcp_server.py`'s `EXPECTED_TOOLS` constant (line 49) still lists the current **18**-tool contract
verbatim: `tape_state, tape_features, tape_history, journal, analytics, studies, datasets, bars,
levels, tradability, setups, backtests, strategies, edge_report, pnl_ledger, taxonomy, ui_route_map,
get_endpoint` — 3 more than the I-6 target 15-tool list. `get_endpoint`'s allowlist is untouched.

### J-04: The fingerprint epoch bump — CONFIRMED FAILING (not started)

**TC-5**: `cd apps/backend && .venv/bin/python -c "from app.config import Config;
print(Config().config_fingerprint())"` → **`4d665603569b9dbf`** (the OLD pin, live-recomputed, not just
grepped). `grep -n "verdict_dwell_seconds\|hint_sustain_dwell_seconds" app/config.py` → both present
(`verdict_dwell_seconds` at line 508, `hint_sustain_dwell_seconds` at line 843) — neither I-4
confirmed-delete field has been removed. Additional supporting evidence: `config_fingerprint()`'s
`excluded` set docstring (lines ~1626-1646) currently documents `management_stance_dwell_seconds` as
EXCLUDED — one of the very fields J-04 must delete-and-then-stop-excluding, confirming the "several
dwells above are exclusion-listed today" note in `docs/goal.md`'s Key Capabilities §5 is accurate.

PnL ledger baseline (`GET /research/pnl/ledger`, live): exactly **one** row exists today —
`founding-baseline-strategy-v1-default`, `provenance.config_fingerprint = "4d665603569b9dbf"`,
`candidate.train.n=1` / `candidate.holdout.n=1` (both `insufficient_sample: true`, consistent with the
project's long-running honest "champion loses money, n=1<5" finding). This is the exact "old founding
row" J-04's acceptance criterion requires to remain untouched, with a new-epoch row to be appended
beside it. `reports/pnl/pnl-history.md` currently documents only this one epoch's founding row.

### J-05: The kept product stands — regression sentinel — SUPPORTING EVIDENCE COLLECTED; browser walk deferred

Non-browser evidence (dev-level):

- `GET /research/strategies` (live) → all three registered, full unchanged config: `v1`,
  `structure_tape`, `structure_tape_map`; `champion: {"strategy_id": "v1", "profile": "default"}`.
- `GET /research/profiles` (live) → `default` (frozen) + `candidate-faster-warmup`, champion unchanged.
- Full backend suite: **1665 passed, 7 skipped, 0 failed, 0 errors, 448.33s (0:07:28), exit 0** (1672
  collected) — green, exceeding the last documented close-out floor (`edge-report-perf-fix`, 2026-07-22
  uncommitted: 1603 pass/7 skip). The +69-test growth is consistent with net-new coverage added by the
  uncommitted `structure-load-latency-fix` and `cockpit-chart-upgrade` follow-ups noted in project
  memory (new tradability-cache/batch-touch-counter/zone-class-index and chart/timeframe-accumulator
  tests) — nothing anomalous. See Tests Run below for the full command and skip breakdown.
- Service startup/restart verified clean (see below).
- **Not verified by me this iteration** (browser-qa-agent's step per TESTING REQUIREMENTS, T-13): the
  sim cockpit click-through (`SIM-BUYER` → `buyer_control`, with the `PriceChart` proving candles +
  timeframe switch + S/R band overlay + live tape bars), `/structure` Load for the pinned AAPL
  `2026-06-22` as-of date (the 300–302.4 wall band on `StructureChart`), the Case Studies drill-in, and
  the Edge Report section's honest current-state render (TC-6/TC-7) all require an active
  WebSocket-driven watch session and visual confirmation — a browser interaction, not a GET probe.
  Recorded as deferred, not as pass or fail, per T-13 ("no screenshot ⇒ `unknown`, never `passing`").
  goal.md's own NOTES section confirms this framing: J-05's full acceptance ties to "full suite green
  under the new pin" (only meaningful after J-04), so even the automated half above is
  today-only evidence, not the interlude's final J-05 verdict.

## `blueprint.md` (DoD item — already drafted, not by me)

`runs/goal-session-clean_slate/state/blueprint.md` already existed when this developer step started
(written by the goal-decomposer as part of the same iteration-0 dispatch, per this session's
established pattern). Verified it satisfies TC-10: the "Information Architecture" section's navigation
skeleton lists exactly **Cockpit `/`** and **Structure `/structure`**, and the "Data Contract" table
carries one row per KEPT canonical value named in `docs/goal.md`'s Product Shape section (bands, touch
events/setups, edge cells + not-computed payload, edge-report compute snapshot, PnL ledger rows,
bars/candles, levels/zones, strategy registry + champion, datasets, backtests, profiles, taxonomy,
route/nav inventory, `config_fingerprint`) — no source file was edited to satisfy this DoD item, it was
already correct on inspection.

## Files Changed

- (none — verify-only baseline; zero source modifications under `apps/`)

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **1665 passed, 7 skipped, 2 warnings in 448.33s (0:07:28). Exit code 0.** (1672 collected.)

Skip breakdown (all three are the standard two-stage `TAPEOLOGY_LIVE_INTEGRATION=1` opt-in gates, not
credentials-missing failures — expected and honest for an autonomous, keyless run):
- `tests/test_event_recording_integration.py` (1)
- `tests/test_live_integration.py` (1)
- `tests/test_yahoo_live_integration.py` (5)

Zero failures, zero errors. The two warnings are pre-existing library deprecation notices
(`starlette.testclient` httpx usage; `websockets.legacy`), unrelated to this codebase and unrelated to
this iteration (no code was touched).

`config_fingerprint` (direct python, not from the suite): `4d665603569b9dbf` — matches the pinned
value exactly (see J-04 above).

## Service startup verification

- `bash scripts/dev.sh` (deterministic scratch ports `8301`/`3301`, this project's own path-hash
  offset — distinct from an unrelated `trendora` checkout's processes observed on `8255`/`3255`,
  which were left untouched) started both services clean: backend `/health` → 200, frontend root →
  200, both within ~2s. No `error`/`EADDRINUSE`/`address already in use` in either log.
- Stopped both via port-based kill (`fuser -k -9 <port>/tcp`, matching the documented
  `uvicorn --reload` / `next dev` child-process gotcha — a parent-PID-only kill is insufficient),
  confirmed both ports fully released (`ss -tln` + `ps aux` both clean), then **restarted
  `scripts/dev.sh` on the same ports** — backend and frontend both healthy again within seconds, zero
  port-conflict errors in the restart log. Stopped again at the end; final state confirmed no
  tapeology `uvicorn`/`next`/`dev.sh` process remains, ports `8301`/`3301` fully free.

## No side effects (baseline hygiene)

- Every live probe this iteration was a **read-only GET** (`/health`, `/research/analytics`,
  `/research/journal`, `/research/studies`, `/research/hints`, `/research/hints/active`,
  `/research/thesis/active`, `/research/taxonomy`, `/research/strategies`, `/research/profiles`,
  `/research/pnl/ledger`, `/meta/ui-routes`) — no `POST`/`PUT`/`DELETE` call was made, so no
  journal/dataset/bar-series record was created or mutated.
- No Alpaca or Yahoo Finance network call was made or attempted.
- The scratch dev-stack smoke test used this project's real local `.data/`/`journal.db` — safe given
  the read-only-GET constraint above, consistent with prior baseline practice.

## Known Issues

- **Environment drift (carried over from every prior era baseline):** the backend venv runs Python
  **3.14.4**; `.claude/project-template.md`'s placeholder text says 3.12. The full suite is green on
  3.14.4 through the point this developer step observed it running — a documentation/environment
  drift observation, not a failure. No action taken (out of scope for a verify-only iteration).
- **`.claude/project-template.md` is still the generic unfilled vendored template** (confirmed again
  this iteration — same finding as every prior baseline; `.claude` is a symlink into
  `incredible_auto_dev/`, never customized for this project). This developer used `docs/goal.md`'s
  Constraints section, prior dev handoffs (especially `docs/handoffs/goal-fast_wall-iter-0-dev.md` and
  `goal-tradable_wall-iter-0-dev.md`), and direct codebase inspection (`pyproject.toml`,
  `apps/backend/tests/`, `scripts/dev.sh`) as the real stack-configuration source of truth. Not this
  iteration's scope to fix.
- **An unrelated project (`trendora`) had a dev stack running on ports 8255/3255** during this
  iteration, discovered via a routine `ps aux` scan before starting this project's own scratch stack.
  It was left completely untouched (different repo, different ports, no overlap with `tapeology`'s
  8301/3301) — noted here only so a later iteration isn't surprised to see it in a process listing.
- Full click-through browser verification of J-02 (nav/404 screenshots, WS frame capture) and J-05
  (sim cockpit + both charts, `/structure` Load + wall band, Case Studies, Edge Report honest state)
  is the browser-qa-agent's step per the spec's TESTING REQUIREMENTS; the evidence above is the
  dev-level code/API/SSR/config inspection leg only, per T-13.
- No credential blockers this iteration — none of J-01–J-05's baseline checks need Alpaca/Yahoo
  network access; the two expected suite skips are the standard two-stage `TAPEOLOGY_LIVE_
  INTEGRATION=1` opt-in gates, not missing-credential failures.

## Suggested Next Phase

Confirms the spec's own NOTES and `docs/goal.md`'s dependency order (J-01 → J-02 → J-03 → J-04 → J-05,
with J-05 guarding continuously): iteration 1 should build **J-01 alone** — the two byte-identical
relocations first (`r_basis` into `backtests.py`; the four dataset-source symbols into `datasets.py`,
proving the full suite green before any deletion), then the 15/14-route deletion + `routes.py`
SLIM + `taxonomy.py` SLIM + the eleven-module deletion (T-12 grep-before-delete on each) +
`JournalStore` method deletion + the ~24 test-file deletions and I-8 UPDATE-file edits. Per the spec's
own "Depth expectation for iteration 1" note, this is large and structurally ordered (relocate-and-
prove-green BEFORE deleting) — `full` depth, not `lean`, is the right call for that iteration.

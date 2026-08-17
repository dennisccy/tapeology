# goal-rapid-microscope-iter-6 Dev Handoff

**Phase:** goal-rapid-microscope-iter-6
**Date:** 2026-08-17
**Agent:** developer
**Status:** complete

## What Was Built

Two production-wiring fixes inside the already-shipped J-05 walk-forward engine, closing the two
gaps iteration-5's own audit left open (findings B5 and B2) — no new route, no new `Config` field,
no schema change, zero frontend files.

### Fix 1 — TR-15 wired into the one production fold-building call site (closes audit finding B5)

`require_sufficient_sessions_for_folds` (`apps/backend/app/research/walkforward.py:338`) already
raised the typed `InsufficientSessionsForFoldsError` and was already proven by TC-20, but had zero
callers in `app/`. `run_diagnostic_walkforward` (`apps/backend/app/research/walkforward.py:1044`)
now calls it at `walkforward.py:1148`, immediately before its one `build_folds` call and AFTER
`register_fold_spec` — so the frozen geometry is still committed to the ledger even for a
below-floor corpus, but fold *evaluation* is refused with a typed, exact-shortfall message instead
of `build_folds` silently returning `[]` (the "empty fold report standing in for the refusal" B5
named).

Two consumers of the raised exception:
- **The CLI** (`walkforward.py:1220-1228`, inside `main()` at `walkforward.py:1197`): a new
  `try/except InsufficientSessionsForFoldsError` around the `run_diagnostic_walkforward` call
  prints the typed message and returns exit code `1` — never an unhandled traceback.
- **The compute route's worker**: verified, not re-plumbed, per the plan's item 2 —
  `WalkForwardComputeManager.trigger`'s existing generic `except Exception as exc:` handler
  (`walkforward.py:890`, unmodified this iteration) already resolves any exception raised inside
  the route's `_work` closure to `{"state": "failed", "error": str(exc)}`. Proven live end-to-end
  via `POST /research/desk/micro/walkforward/compute` in the new TC-3 test (below) — no code
  change was needed on the route side.

Today's real corpus (154 walked sessions, well above the 105-session floor) passes this check
silently — confirmed live against a scoped copy of the real ledger (see "Real-corpus
verification" below); the served result is unchanged.

### Fix 2 — the §6.7 exposure registry now seeds the legacy tick corpus too (closes audit finding B2)

The seeding mechanism (`micro_accessor.initialize_r2_exposure_registry` /
`has_any_exposure_entries`) already existed but production only ever called it for
`PLAYBOOK_DIAGNOSTIC_CORPUS_ID`. `run_diagnostic_walkforward` now also seeds a **second**,
distinct exposure registry corpus for the legacy tick corpus, at `walkforward.py:1127-1130`,
mirroring the playbook seed immediately above it (same guard, same pattern):

- **New corpus_id: `TICK_LEGACY_CORPUS_ID = "tick_legacy_symbol_days_v1"`**
  (`walkforward.py:979`). This is an implementation choice the plan explicitly authorized and
  asked to be logged rather than invented silently (T-1) — named to mirror
  `PLAYBOOK_DIAGNOSTIC_CORPUS_ID`'s own `<what>_v1` shape, so a future recorder revision that
  changes what "the legacy tick corpus" means is a distinguishable `v2`, never a silent
  redefinition.
- **New helper `_tick_dataset_session_dates`** (`walkforward.py:984`): resolves the tick dataset
  list via `config.dataset_dir_resolved()` — the exact same mechanism `micro_readiness.py` already
  uses (no second inventory mechanism, no hardcoded date list) — and derives each dataset's ET
  session date with the SAME ET-conversion technique `micro_readiness.py`'s `_et_datetime` and
  `micro_accessor.py`'s `_session_date_for_dataset` already use (mirrored per this codebase's own
  documented per-module-private-`ZoneInfo` convention, not imported). `DatasetStore.list()` is
  metadata-only (no event replay), so this is cheap even against the real 18-shard corpus.
  Returns one entry per **distinct** session date (not per shard — multiple symbol-days sharing a
  date collapse to one window, exactly the playbook seed's own convention).
- The seeding call is guarded by `has_any_exposure_entries(exposure_registry,
  TICK_LEGACY_CORPUS_ID)` (idempotent — a repeat operator act never re-appends the window list)
  and fires from the SAME operator-act entry point the playbook seed uses
  (`run_diagnostic_walkforward`) — never a GET route, per the era's "No scheduling" non-goal.

**The two mechanisms stay separate (TC-7).** This walk-forward-internal `ExposureRegistry` (used
only to classify a future spec/window pair `historical_oos` vs `historical_exposed_diagnostic`) is
a completely different mechanism from `micro_readiness.py`'s served, per-shard `exposure_state`
(`exploratory`/`hand_assigned`) — the latter is a hardcoded literal per shard
(`micro_readiness.py`'s `EXPOSURE_STATE_EXPLORATORY` constant) and does not read this registry at
all, so seeding it cannot move readiness's served value. Proven live against the real 18-shard
corpus (below), not just asserted.

## Files Changed

- `apps/backend/app/research/walkforward.py` -- MODIFY: (a) `require_sufficient_sessions_for_folds`
  call wired into `run_diagnostic_walkforward` immediately before `build_folds`
  (`walkforward.py:1148`); (b) `main()` gains a `try/except InsufficientSessionsForFoldsError`
  (`walkforward.py:1220-1228`); (c) new `TICK_LEGACY_CORPUS_ID` constant (`walkforward.py:979`) +
  new `_tick_dataset_session_dates` helper (`walkforward.py:984`) + new tick-corpus exposure-seeding
  block (`walkforward.py:1121-1130`); (d) two new imports (`zoneinfo.ZoneInfo`,
  `.datasets.DatasetStore`) and one `__all__` addition; (e) `run_diagnostic_walkforward`'s
  docstring gained a short "iter-6 additions" paragraph documenting both fixes.
- `apps/backend/tests/test_walkforward.py` -- MODIFY: added TC-2, TC-3, TC-5, TC-6, TC-7 (five new
  tests); rewrote the existing empty-store CLI test as TC-4 (its old assertion — "an empty store
  registers the fold spec but evaluates zero folds" — was exactly the B5 gap this iteration closes,
  so its behavior is now the below-floor refusal instead); added `TAPEOLOGY_DATASET_DIR`
  redirection to the existing route-wiring test (see "Known Issues" below for why); extended
  `_FakeConfig` with `dataset_dir_resolved()`; added `_tick_events`/`_plant_tick_dataset` fixture
  helpers (mirroring `test_micro_readiness.py`'s own `_events`/`_plant_dataset` precedent).

No `docs/goal.md`, `docs/rapid-validation-spec.md`, or `blueprint.md` edit. No frontend file
touched (confirmed via `git status` — zero `.tsx` files in this diff; see "Known Issues" for why
`Frontend Present: yes` is nonetheless declared on this iteration's plan). No `Config` field added.
No new route. `git diff --stat` over `app/engine/`, `desk_playbook.py`, `desk_playbook_context.py`,
`config.py`, and all six `referee_*.py` files is empty — verified directly, not assumed.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/` (no extra `-q`, per the iter-0
lesson).

Result: **3038 passed, 8 skipped, 0 failed in 530.37s** (iteration-5's post-audit baseline was
3033 pass / 8 skip / 0 fail; net +5 new tests, 0 regressions). Exceeds this iteration's ≥3033
requirement.

Targeted pre-checks (before the full run): `tests/test_walkforward.py` alone — 54 passed. A
broader sweep (`test_walkforward.py`, `test_walkforward_oracles.py`, `test_micro_accessor.py`,
`test_micro_readiness.py`, `test_micro_join.py`, `test_scout.py`, `test_micro_chain_ledger.py`,
`test_mcp_server.py`, `test_meta_routes.py`, `test_desk_ui_guards.py`, `test_copy_discipline.py`,
`test_referee_guards.py`) — 397 passed, 0 failed.

**Frozen-foundation re-checks (TC-10), run directly against the live tree:**
- `Config().config_fingerprint()` -> `08e471b10130e1e2` (unchanged).
- All 6 `referee_*.py` SHA-256 hashes, re-computed via `sha256sum` -> byte-identical to the
  iteration-0 baseline listing (`docs/handoffs/goal-rapid-microscope-iter-0-dev.md`).
- `git diff --stat` over `app/engine/`, `desk_playbook.py`, `desk_playbook_context.py`,
  `config.py`, and the six `referee_*.py` files -> empty.

**Real-corpus verification (TC-1, TC-5, TC-6, TC-7), run against the ACTUAL real stores — not a
stand-in:**

Following the iteration-5 audit's own procedure (never mutate the live `.data` directly): copied
`.data/micro_walkforward` and `.data/micro_exposure_registry` to a scoped temp dir, pointed
`TAPEOLOGY_MICRO_WALKFORWARD_DIR`/`TAPEOLOGY_MICRO_EXPOSURE_REGISTRY_DIR` at the copies, and left
`TAPEOLOGY_DATASET_DIR`/`TAPEOLOGY_DESK_UNIVERSE_DIR`/`TAPEOLOGY_BAR_DIR` unset (real dirs) since
those are read-only for this run. Ran `python -m app.research.walkforward --diagnostic` twice:

```
RUN 1: diagnostic walk-forward complete: 5 fold(s) (0 newly recorded, 5 replayed from the
        existing ledger), 100 validation session(s) over 154 corpus session(s).
RUN 2: diagnostic walk-forward complete: 5 fold(s) (0 newly recorded, 5 replayed from the
        existing ledger), 100 validation session(s) over 154 corpus session(s).
```

- **TC-1 confirmed:** byte-identical to iteration 5's recorded values (5 folds, 100 validation
  sessions, 0 newly recorded / 5 replayed both times) — `require_sufficient_sessions_for_folds`
  passed silently against the real 154-session corpus, exactly as expected.
- **TC-5 confirmed:** after run 1, the scoped exposure registry gained **11** new rows under
  `corpus_id=tick_legacy_symbol_days_v1` (one per distinct ET session date across the real
  18-dataset/12-symbol-day tick corpus — matches the corpus's own recorded 11-session span), while
  the existing 154 `playbook_setups_diagnostic_v1` rows were untouched.
- **TC-6 confirmed:** after run 2 (same scoped registry), the tick-corpus row count stayed at 11 —
  no re-seeding. Both ledgers' hash chains verified `{"ok": true}` after both runs.
- **TC-7 confirmed:** re-read `micro_readiness.build_readiness()` directly against the real
  `.data/datasets` store (read-only) after the tick-corpus seeding above — all 18 real shards still
  serve `exposure_state: "exploratory"`.
- Confirmed the real `.data/micro_walkforward` and `.data/micro_exposure_registry` directories were
  never touched by this verification (`wc -l` before/after this whole session: unchanged at 6 and
  154 lines respectively) — every write happened in the scoped copy.

## Pre-handoff verification

- **Service startup:** `bash scripts/start-backend.sh` started cleanly on the project's
  deterministic port (8301, computed from the repo path per `scripts/dev.sh`'s own offset
  formula); `GET /health` returned `{"status":"ok"}` and both `GET
  /research/desk/micro/walkforward` and `GET /research/desk/micro/readiness` returned HTTP 200
  against the real store. Stopped by its exact recorded PID (never a pattern-based kill, per the
  operator's standing instruction) — confirmed the port freed and a follow-up request was refused.
  Restarted on the same port with zero conflict, confirmed healthy again, then stopped a second
  time by its exact PID. Frontend was not started/stopped for this verification: this iteration's
  diff touches zero frontend files, so a frontend start/stop cycle cannot exercise anything this
  diff changed (see "Known Issues" below for the separate, mechanical reason `Frontend Present:
  yes` is declared on this iteration's plan regardless).
- **External integrations:** N/A — no adapter, scraper, or new external API call this iteration.
- **Native dependency binaries:** N/A — no new dependency.

## Known Issues

**`Frontend Present: yes` on this iteration's plan is a mechanical declaration, not a UI claim —
by design, not an oversight.** This diff is 100% backend (confirmed via `git status`: zero `.tsx`
files). The plan's own "Frontend Present" section explains why: `browser-qa-phase.sh`'s
`detect_frontend_in_plan` short-circuits the entire browser lane — including the
required-still-passing regression set (J-01-J-04) and J-10's sentinel — whenever a plan says
`Frontend Present: no`, and this has silently swallowed browser evidence for two consecutive prior
iterations (iter-4, iter-5). Declaring `yes` here is the loop-internal workaround the operator's
dispatch instructed; the durable fix (making the gate read the already-exported
`CHAIN_GOAL_TARGET_JOURNEYS` safeguard instead) is framework-maintenance work outside this agent's
authority and outside `docs/goal.md`'s Key Capabilities. Flagging this explicitly so the
reviewer/QA/auditor do not go looking for UI changes that do not exist in this diff.

**The `TICK_LEGACY_CORPUS_ID` name is a disclosed implementation choice (T-1), not a spec-pinned
constant.** `docs/rapid-validation-spec.md` names the mechanism (§6.7's exposure registry) but not
a corpus_id string for the legacy tick corpus specifically. Chosen as `"tick_legacy_symbol_days_v1"`
to mirror the sibling `PLAYBOOK_DIAGNOSTIC_CORPUS_ID = "playbook_setups_diagnostic_v1"`'s own
naming shape. If a future J-06/J-07 owner ruling names a different canonical corpus_id for this
same set, that is a straightforward rename (the exposure registry rows carry no other identity
than this string).

**J-06 has not landed, so "every currently-registered tick dataset" and "the 12 legacy symbol-days"
remain the exact same 18-dataset/12-symbol-day set today** — this is what the plan calls out as
what makes seeding safe now (no sealed/opaque shards exist yet that this seeding could
inadvertently expose). When J-06 lands real sealed shards, its own vault work must ensure this
seeding path is never reached for a shard that is `sealed` (the vault does not exist yet, so this
iteration cannot itself prove that boundary — flagged for J-06's own scope, not fixed here per
Do-Not-Redo).

**One pre-existing test needed a hermeticity fix unrelated to its own assertions.**
`test_walkforward_routes_serve_empty_state_honestly_and_the_compute_trigger_round_trips` goes
through the actual FastAPI route, which passes the real `CONFIG` object (not
dependency-injected) into `run_diagnostic_walkforward` — since this iteration's fix reads
`CONFIG.dataset_dir_resolved()` for the tick-corpus seed, that test would otherwise have started
reading the real `.data/datasets` corpus (harmless correctness-wise — metadata-only — but breaks
this test's own hermetic-`tmp_path` intent). Added one `monkeypatch.setenv("TAPEOLOGY_DATASET_DIR",
...)` line pointing it at an empty scoped dir; no other change to that test.

No gaps against this iteration's own DEFINITION OF DONE from the developer's side. The remaining
DEFINITION OF DONE items (browser-qa-agent genuinely dispatching, J-01's Microscope Readiness
screenshot, J-10's 13-step sentinel, the golden-replay checks for J-01-J-04) are the
browser-qa-agent's own step, not something this handoff can discharge — flagged in the plan's own
"Escalation watch" section for the evaluator if the browser lane still fails to dispatch despite
`Frontend Present: yes`.

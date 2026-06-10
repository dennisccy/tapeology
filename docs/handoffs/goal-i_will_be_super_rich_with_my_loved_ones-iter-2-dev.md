# goal-i_will_be_super_rich_with_my_loved_ones-iter-2 Dev Handoff

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-2
**Date:** 2026-06-10
**Agent:** developer
**Status:** complete

## What Was Built

Thesis declaration with honest validation (J-38 + J-39) — the first `/research/*` API namespace,
the first persistence (journal-scoped SQLite), and the first cockpit research surface (the thesis
strip). The verdict stays honestly `pending` this iteration; the verdict-transition engine is next.

Backend:
- **Research config + fingerprint** (`app/config.py`): env-configured journal DB path
  (`TAPEOLOGY_JOURNAL_DB`, default `tapeology_journal.db`, `:memory:` supported), `journal_busy_timeout_ms`,
  `journal_schema_version`, and `config_fingerprint()` — a SHA-256 over the ENTIRE frozen config
  (classifier + research values), stable across runs/processes, changing when any threshold changes.
  Store-tuning fields (DB path / busy timeout / schema version) are excluded so two journals that
  differ only in location share a fingerprint.
- **Taxonomy module + `GET /research/taxonomy`** (`app/research/taxonomy.py`): the single backend
  owner of every research label — 4 setups (`absorption_reversal`, `trend_continuation`,
  `level_break`, `failed_move_fade`) with per-setup level requirement (REQUIRED for the two level
  setups, FORBIDDEN otherwise), direction-aware expected-behaviour statement templates, and
  direction/verdict/statement-status enums with display copy. The frontend hardcodes none of it.
- **Journal store (SQLite, scoped)** (`app/research/store.py`): stdlib `sqlite3` only — WAL +
  `busy_timeout` + `BEGIN IMMEDIATE` + ONE background writer-queue worker thread. The full versioned
  schema is created at once (theses, verdict_events, hints, actions, studies, study_occurrences,
  schema_version); only `theses` + `verdict_events` are written this iteration. The repository
  exposes NO update/delete on `verdict_events` (append-only). No tape data is persisted.
- **`POST /research/thesis`** (`app/research/routes.py`): honest validation, never coercion — 404
  not-watched, 409 active thesis exists, 422 wrong-side invalidation (both directions),
  missing/forbidden level, unknown enums. Nothing persisted on rejection. On success: freezes the
  entry context (state/confidence/last/spread/primary-window features) + derived expected-behaviour
  statements; binds to the SOURCE IDENTITY (the snapshot's `scenario` descriptor, never the bare
  ticker); stamps bound source + `data_feed` (`sim|sip|iex`) + `config_fingerprint`; appends the
  initial `pending` verdict event; returns the full projection.
- **`GET /research/thesis/active?ticker=`**: the canonical projection read (`thesis: null` is normal).
  Reads the SAME `monitor.projection()` the WS `thesis` key reads — verbatim-equal by construction.
- **Research monitor** (`app/research/monitor.py`): attached per-watch via the iter-1 observer seam,
  read-only over the engine, exception-isolated. Holds the active thesis, recomputes each frozen
  statement's live status (`met | not_yet | violated`) per event from EXISTING engine
  states/features only, serves the projection (verdict fixed at `pending`, `monitor_status`). A
  monitor/store error flips `monitor_status: failed` — the feed never dies.
- **Additive WS `thesis` key**: merged at the stream send site in `main.py` (NOT inside the engine
  serializers), so `serialize_stream`/`serialize_history` stay byte-identical (equivalence anti-goal).
- **Lifecycle honesty (subset of capability 24)**: stop / stream-end / feeder failure auto-resolves
  an active thesis `expired(reason)` with a final appended timeline event (via the monitor's
  `on_status`); a startup sweep resolves any DB row left `active` (e.g. a crashed prior process) to
  `expired`. No entry marks exist yet, so the survives-with-entry-mark exception is not built.
- **WatchManager research seam**: an exception-isolated `on_engine_created(ticker, engine)` hook
  (default None — every existing test unchanged) is fired at each engine-construction site so the
  research registry attaches a fresh monitor before the feeder starts. The WatchManager imports no
  research type.

Frontend:
- **ThesisStrip** (`components/ThesisStrip.tsx`): idle = one single-line declare affordance (nothing
  else moves); form fully taxonomy-driven from `GET /research/taxonomy` (the level field appears only
  when the selected setup requires it); inline 422/409/404 messages surfaced verbatim with form
  values preserved; active display reads the WS `thesis` projection verbatim — setup, direction,
  invalidation (mono), statements each with a live status, `pending` verdict badge (slate), bound
  source + `data_feed` stamp, `monitor_status: failed` surfaced honestly.
- Strip mounted on `/` between the price chart and the panel grid; shown only once a settled
  snapshot is live (never over waiting/connecting/failed). Wired into `lib/api.ts`
  (`fetchTaxonomy`/`declareThesis`/`fetchActiveThesis`), `lib/types.ts` (thesis + taxonomy types,
  additive `thesis?` on `TapeSnapshot`), and surfaced through the existing WS-parse in `useTapeStream`.

## Files Changed

- `apps/backend/app/config.py` -- research config block + `config_fingerprint()` + `journal_db_path_resolved()`
- `apps/backend/app/research/__init__.py` -- NEW research package
- `apps/backend/app/research/taxonomy.py` -- NEW: setup catalog, level rules, statement templates, enums + copy
- `apps/backend/app/research/store.py` -- NEW: SQLite journal store (WAL, writer queue, append-only verdict_events, full schema)
- `apps/backend/app/research/monitor.py` -- NEW: research monitor observer (statement statuses, projection, expiry-on-stop)
- `apps/backend/app/research/routes.py` -- NEW: `/research/taxonomy`, `/research/thesis`, `/research/thesis/active` + the `ResearchRegistry`
- `apps/backend/app/main.py` -- mount research router; store DI + registry + startup sweep in lifespan; merge additive WS `thesis` key
- `apps/backend/app/watch_manager.py` -- exception-isolated `on_engine_created` hook fired at every engine-construction site
- `apps/backend/tests/test_research_store.py` -- NEW: store discipline (WAL, writer queue, temp path, schema_version, append-only)
- `apps/backend/tests/test_research_monitor.py` -- NEW: frozen context/statements, source binding, stamps, statuses, monitor_status failed, expired-on-stop
- `apps/backend/tests/test_research_api.py` -- NEW: full POST validation matrix, taxonomy, REST==WS thesis projection
- `apps/backend/tests/test_observer_equivalence.py` -- extended: real monitor attached (no thesis + with thesis) byte-identical
- `apps/frontend/lib/types.ts` -- thesis projection + taxonomy types; additive `thesis?` on TapeSnapshot
- `apps/frontend/lib/api.ts` -- `fetchTaxonomy` / `declareThesis` (error-body passthrough) / `fetchActiveThesis`
- `apps/frontend/app/page.tsx` -- mount ThesisStrip between the chart and the panel grid
- `apps/frontend/components/ThesisStrip.tsx` -- NEW: idle / taxonomy-driven form / active-thesis display
- `.gitignore` -- add `*.db-wal` / `*.db-shm` (the WAL sidecar files; `*.db` was already ignored)

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **332 passed, 1 skipped** (baseline was 292 passed / 1 skipped — +40 new tests:
13 store + 12 monitor + 13 API + 2 equivalence). 0 failures, 0 regressions.

Command: `cd apps/frontend && npm run build`
Result: Compiled successfully; types + lint clean; `/` route 12.2 kB.

Live integration (real uvicorn, temp `TAPEOLOGY_JOURNAL_DB`, server demonstrably up):
- `GET /research/taxonomy` serves the 4 setups with correct `requires_level` flags.
- Declare on unwatched ticker → 404, nothing persisted.
- Wrong-side long invalidation → 422; `level_break` without level → 422; `absorption_reversal`
  with level → 422; valid declare → 200 (full projection, `verdict: pending`,
  `bound_source: bid_absorption`, `data_feed: sim`); second declare → 409.
- `GET /research/thesis/active?ticker=SIM-BIDABS` byte-identical to the WS frame's `thesis` key.
- Stop → thesis `expired` with appended `expired` event (timeline `[pending, expired]`); re-watch
  shows `thesis: null`.
- Hard-kill leaving an `active` row, then restart → startup sweep resolved it to `expired` with an
  appended `expired` event.
All test servers killed and all temp DB files removed afterward.

## Known Issues

- **Verdict is intentionally fixed at `pending`** this iteration (the verdict-transition engine —
  J-40–J-46, dwell, `rule_first_true` — is next iteration). The strip's verdict badge is always the
  slate `pending` pill; statement statuses DO update live.
- **`risk_flags` is omitted entirely** from the projection (no empty list) per the spec's honesty
  rationale — J-49 adds it.
- The expiry-on-stop store write runs on the event-loop thread inside the monitor's `on_status`
  callback (a single small terminal write, not the hot `on_event` path). It is bounded and never
  blocks the per-event feeder; only the one-time terminal resolution touches the store from a
  callback. If this ever shows up as latency under dense live tape, move `_expire_active` to a
  fire-and-forget enqueue.
- No browser QA was run by the developer (that is the QA agent's step); the live REST/WS evidence
  above stands in for the response-evidence portion of J-38/J-39.
- The journal DB defaults to `apps/backend/tapeology_journal.db` (gitignored). Operators set
  `TAPEOLOGY_JOURNAL_DB` to relocate it; tests inject a temp path via `set_registry` +
  `manager.set_on_engine_created`.

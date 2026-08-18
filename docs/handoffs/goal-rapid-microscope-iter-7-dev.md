# goal-rapid-microscope-iter-7 Dev Handoff

**Phase:** goal-rapid-microscope-iter-7
**Date:** 2026-08-17
**Agent:** developer
**Status:** complete

## What Was Built

Two independent pieces, exactly as scoped by the plan — J-06 step 1 (the era's most dangerous
change so far, per the iteration-6 evaluator) and J-05's remaining acceptance gap.

### 1 — J-06 step 1: the Card-5.1 data-preservation prerequisite (spec section 7.1/2.6 r2)

Threaded four optional trade fields and four optional quote fields through the whole event
pipeline — adapter → provider → engine event → stored row — all additive, absent-key
backward-compatible, engine-ignored:

- `apps/backend/app/providers/adapters/base.py` — `RawTrade` (`:65`) gains
  `conditions: list[str] | None = None`, `exchange: str | None = None`, `tape: str | None = None`,
  `trade_id: int | None = None` (named `trade_id`, not `id`, to avoid shadowing the builtin).
  `RawQuote` (`:87`) gains `conditions`, `tape`, `bid_exchange`, `ask_exchange` (all
  `| None = None`).
- `apps/backend/app/providers/base.py` — `TradeEvent` (`:25`) / `QuoteEvent` (`:52`) gain the
  matching optional fields, appended after every existing field so every pre-existing positional
  construction call site stays valid unchanged.
- `apps/backend/app/providers/historical.py` — both `HistoricalProvider.stream()` (`:60`) and
  `ProgressiveHistoricalProvider._emit()` (`:136`) thread the fields straight through from the
  `RawTrade`/`RawQuote` record already in scope (a direct pass-through, confirmed no new lookup
  needed).
- `apps/backend/app/providers/adapters/alpaca.py` — two new helpers, `_venue_str` (`:169`) and
  `_conditions_list` (`:182`), coerce the SDK's `Optional[Union[Exchange, str]]` /
  `Optional[Union[List[str], str]]` typing to plain vendor-neutral values (verified against the
  REAL `alpaca.data.models.Trade`/`Quote` classes, not a guess — see "Real SDK verification"
  below). Populated at both historical construction sites, `_fetch_one_subwindow` (`:363`) and
  `_fetch_trades_quotes` (`:444`), via `getattr(t, "conditions", None)` etc. (defensive — never a
  bare attribute access, so every existing hermetic test double lacking these attributes stays
  unaffected). Also populated at the live-streaming site (`_on_trade`/`_on_quote`, `:725`/`:740`)
  since it was trivial reuse of the same two helpers, per the plan's "keep it consistent if
  trivial" instruction — this never persists to a dataset, so it changes no stored data.
- `apps/backend/app/research/datasets.py` — `_event_to_row` (`:152`) / `_row_to_event` (`:200`)
  carry the eight fields **present-only**: a key is added to the stored row only when the source
  event's field is not `None`; `row.get(...)` (never `row[...]`) on load, so a legacy row lacking
  the key defaults cleanly to `None`. `DatasetStore.record()` (`:449`) and `record_from_source()`
  (`:578`) gain optional `schema_basis: str | None = None` / `quote_size_unit: str | None = None`
  keyword parameters, stamped into `meta` only when supplied. A supplied `quote_size_unit` is
  validated against the **existing** `micro_features.QUOTE_SIZE_UNITS` tuple (imported, not
  duplicated) and rejected with `ValueError` if unrecognised — no `ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE`
  defined (that dated-rule constant stays reserved for a future `tick_recorder.py`, per the
  assumption ledger's iter-7 first entry).

### 2 — J-05: the tick-family fold request reaches a genuine production entry point

- `apps/backend/app/research/walkforward.py` — new `run_tick_family_fold_request(ledger, config)`
  (`:1005`): resolves the real legacy tick corpus's session dates via the existing
  `_tick_dataset_session_dates` (no second inventory mechanism), registers `DIAGNOSTIC_GEOMETRY`
  for `TICK_LEGACY_CORPUS_ID` (mirroring `run_diagnostic_walkforward`'s own register-then-check
  ordering — idempotent, so repeat calls replay the same row rather than erroring), then calls the
  already-wired `require_sufficient_sessions_for_folds`. At today's real 11-session corpus this
  always raises `InsufficientSessionsForFoldsError` naming the exact shortfall — the typed refusal
  IS the acceptance (T-7 "insufficient is an answer"); no fold-evaluation branch was built past
  that point since nothing can reach or test it yet (J-06/J-09 scope).
- `main()` (`:1242`) gains a new `--family` flag (`choices=["tick_legacy"]`) that calls the new
  function and prints/exits exactly like the existing `--diagnostic` refusal handling, never a
  second divergent error path. `POST /walkforward/compute`'s route-level family parameter is
  explicitly deferred (no UI/MCP consumer needs it yet, per the assumption ledger's second iter-7
  entry).

## Files Changed

- `apps/backend/app/providers/adapters/base.py` — `RawTrade`/`RawQuote` gain the 4+4 optional
  Card-5.1 preservation fields.
- `apps/backend/app/providers/base.py` — `TradeEvent`/`QuoteEvent` gain the matching fields.
- `apps/backend/app/providers/historical.py` — both construction sites thread the fields through.
- `apps/backend/app/providers/adapters/alpaca.py` — `_venue_str`/`_conditions_list` helpers;
  populated at both historical fetch sites + the live-stream site.
- `apps/backend/app/research/datasets.py` — present-only row carry; `record()`/`record_from_source()`
  gain `schema_basis`/`quote_size_unit` kwargs.
- `apps/backend/app/research/walkforward.py` — `run_tick_family_fold_request` + CLI `--family` flag.
- `apps/backend/tests/test_datasets.py` — 4 new tests (TC-1, TC-2, TC-3, TC-9).
- `apps/backend/tests/test_walkforward.py` — 2 new tests (TC-6 + an unknown-`--family`-value edge
  case); `test_tc20_the_11_session_tick_corpus_returns_the_typed_floor_refusal_naming_11_lt_105`
  left byte-unmodified (confirmed via `git diff -U0`: the file's only diff hunk is a pure insertion
  after `test_the_cli_with_no_flag_does_nothing`, nowhere near TC-20 — TC-8).

No `docs/goal.md`, `docs/rapid-validation-spec.md`, or `blueprint.md` edit. No frontend file
touched (`git diff --stat` shows zero `.tsx`/`.ts` files). No `Config` field added. No new route.
No edit to `micro_features.py`, `micro_observer.py`, or `micro_snapshots.py` (confirmed via
`git diff --stat` — all three absent from the diff, per the iter-3 lesson and this iteration's own
OUT OF SCOPE list). No edit to any `referee_*.py` file, `journey-scripts/J-10.json`, or
`app/engine/`.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/` (no extra `-q`, per the iter-0
lesson).

**Result: 3044 passed, 8 skipped, 0 failed in 516.29s (0:08:36).** Iteration-6's baseline was 3038
pass / 8 skip / 0 fail; net **+6** new tests (4 in `test_datasets.py`, 2 in `test_walkforward.py`),
**0 regressions**. Exceeds this iteration's ≥3038 requirement.

Targeted pre-checks:
- `tests/test_datasets.py tests/test_walkforward.py` — 78 passed.
- The full byte-compat regression set — `test_observer_equivalence.py`, `test_dense_replay_gate.py`
  (the golden trace), `test_real_data_gate.py` (Alpaca confinement), `test_chunked_fetch.py`,
  `test_progressive_fetch.py`, `test_vendor_responsiveness.py`, `test_historical_provider.py`,
  `test_live_provider.py`, `test_epoch_anchor.py`, `test_speed_api.py`, `test_watch_manager.py` —
  **151 passed, 0 failed**, all byte-unmodified by this diff.

**Frozen-foundation re-checks (TC-4/TC-10):**
- `Config().config_fingerprint()` → `08e471b10130e1e2` (unchanged).
- All 6 `referee_*.py` SHA-256 hashes, recomputed via `sha256sum`, match the iteration-0 baseline
  listing (`docs/handoffs/goal-rapid-microscope-iter-0-dev.md` lines 76-81) **byte-for-byte**:
  `referee_adjudicate.py` `6dd807b5...`, `referee_evidence.py` `482f38a1...`, `referee_null.py`
  `34917e38...`, `referee_registry.py` `03840c86...`, `referee_routes.py` `0cc3a06f...`,
  `referee_stats.py` `fba8816a...` — all six confirmed identical.

**TC-1 — the 18 real on-disk tick datasets (the narrow risk surface the iteration-6 evaluator
flagged), verified directly, not assumed:**
- `store.list()` against the real `.data/datasets` (via `CONFIG.dataset_dir_resolved()`): **18
  records, 0 errors, 27.0s** — every checksum verifies; zero new manifest key
  (`schema_basis`/`quote_size_unit`) appears on any of the 18.
- `store.load_events()` over all 18: **9,145,900 total events reconstructed, 0 errors**, every
  dataset's event count matching its own `event_counts.total` exactly, 35.2s — this is
  `_row_to_event`'s absent-key discipline exercised against the entire real corpus, not a sample.
- Direct JSON row-scan (bypassing the loader) over all 18 files: zero occurrence of
  `conditions`/`exchange`/`tape`/`trade_id` on any trade row and zero occurrence of
  `conditions`/`tape`/`bid_exchange`/`ask_exchange` on any quote row, across every event in every
  file.
- Full-engine `replay()` determinism spot-check on the 3 smallest real datasets (52K/56K/84K —
  the two largest real files are 190MB/159MB, so a full double-replay of all 18 is a genuinely
  multi-minute compute path, not appropriate to force through given the era's iteration-hygiene
  rail; the 2 committed dataset fixtures already get a full byte-identical replay proof via the
  existing, unmodified `test_committed_fixture_pair_loads_through_the_real_store_path_and_replays_keyless`,
  and `_row_to_event`'s correctness is symbol/size-independent, so this is not a gap): all 3
  replay byte-identically across two consecutive calls (504/509/786 snapshots respectively).
- Both `tests/fixtures/datasets/*.json` (2 files) and `tests/fixtures/alpaca/*.json` (3 files)
  load correctly — proven via the existing, unmodified
  `test_committed_fixture_pair_loads_through_the_real_store_path_and_replays_keyless` and
  `test_committed_fixture_pair_windows_are_disjoint` (both passed as part of the targeted run
  above), plus every fetch/progressive/chunked test that reads the 3 alpaca fixtures (151-test
  regression set above).

**TC-7 (goal.md J-05, manual run against the real store, pasted verbatim):**

Ran the SAME production CLI path the automated TC-6 test exercises, pointed at the operator's
real `.data/datasets` (read-only — `list()` and `_tick_dataset_session_dates` never write), with
`TAPEOLOGY_MICRO_WALKFORWARD_DIR` scoped to a throwaway copy (the iteration-6 dev handoff's own
"never mutate the live `.data` directly" precedent) so the real walkforward ledger is never
touched:

```
$ TAPEOLOGY_MICRO_WALKFORWARD_DIR=<scoped-copy> .venv/bin/python -m app.research.walkforward --family tick_legacy
tick-family fold request refused (tick_legacy): 11 < 105 -- refused (TR-15): this corpus cannot produce WF_MIN_SUFFICIENT_FOLDS(3) folds under this geometry
$ echo $?
1
```

Names exactly **"11 < 105"** — the literal string goal.md J-05's acceptance requires — produced
by the new production entry point against the real 11-distinct-ET-session-date tick corpus, not a
synthetic fixture. Confirmed the real `.data/datasets` directory's aggregate content hash was
identical before and after this run (read-only), and confirmed the scoped ledger copy DID receive
the new `fold_spec` row for `TICK_LEGACY_CORPUS_ID` (geometry matches `DIAGNOSTIC_GEOMETRY`
exactly, chain verifies `{"ok": true}`) while the real `.data/micro_walkforward` directory's
modification time predates this whole session — untouched. The evaluator should independently
re-run this same command (with its own scoped `TAPEOLOGY_MICRO_WALKFORWARD_DIR`) against the real
store to confirm.

**TC-6 (hermetic):** `test_tc6_the_family_flag_prints_the_typed_refusal_naming_the_real_shortfall`
seeds 11 distinct-session-date tick fixtures under a `tmp_path`-scoped `TAPEOLOGY_DATASET_DIR`,
runs `--family tick_legacy`, and asserts the exact substrings `"11 < 105"` and `"TR-15"` in stdout,
exit code ≠ 0, zero `ROW_KIND_FOLD_RESULT` rows, and the `fold_spec` row IS registered (mirrors
TC-7's own real-corpus shape).

**TC-9:** `test_tc9_no_second_quote_size_unit_vocabulary_or_early_dated_rule_constant_exists` — an
AST-based scan (the codebase's own `test_micro_accessor.py` import-ban-guard idiom) over all 50+
files in `app/` confirms zero `ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE` assignment and zero second
`QUOTE_SIZE_UNITS` assignment outside `micro_features.py`.

**Real SDK verification (nice-to-have per the plan, done since it was cheap and directly
addresses the plan's "read the live SDK response shape directly, never guess a field name"
instruction):** constructed real `alpaca.data.models.Trade`/`Quote` instances from raw
dict payloads (the exact shape `TRADE_MAPPING`/`QUOTE_MAPPING` define) and ran them through
`_venue_str`/`_conditions_list` and the full `RawTrade → TradeEvent → _event_to_row →
_row_to_event` pipeline — confirmed byte-identical round trip, and confirmed both edge cases the
docstrings warn about: an `exchange` value that resolves to a bare `str` in this pydantic version
(not an `Exchange` enum instance — `_venue_str` handles both correctly either way) and a
single-code `conditions` value arriving as a bare string rather than a list (`_conditions_list`
normalizes it to `['@']`). This was a hermetic exercise of the real installed SDK's model classes,
not a live network call — no credentials were used or required.

## Pre-handoff verification

- **Service startup:** `bash scripts/start-backend.sh` (deterministic port 8301) started cleanly;
  `GET /health` → `{"status":"ok"}`; `GET /research/desk/micro/readiness` → HTTP 200 with all 18
  real shards served; `GET /research/desk/micro/walkforward` → HTTP 200 serving the pre-existing
  real playbook fold ledger (proves the whole FastAPI app — including the new
  `from .micro_features import QUOTE_SIZE_UNITS` import in `datasets.py` — boots and serves
  against the real corpus with no import/runtime error). Stopped by its exact recorded PID (never
  a pattern-based kill, per the operator's standing instruction), confirmed the port freed
  (connection refused), restarted on the same port with zero conflict (`grep` over the restart
  log for "address already in use"/"error" found nothing), confirmed healthy again, then stopped a
  second time by its exact PID — confirmed not running afterward. Frontend was not started/stopped:
  this iteration's diff touches zero frontend files (the iter-6 handoff's own precedent for the
  same reason).
- **External integrations:** N/A — no new adapter, scraper, or external API call this iteration
  (the Alpaca adapter changes only extend field extraction on the EXISTING two historical
  construction sites; no live credentialed fetch was run or required — see "Real SDK verification"
  above for the closest thing, done hermetically against the installed SDK's own model classes).
- **Native dependency binaries:** N/A — no new dependency.

## Known Issues

**`Frontend Present: yes` on this iteration's plan is a mechanical declaration, not a UI claim —
by design.** This diff is 100% backend (confirmed via `git status`: zero `.tsx` files). See the
plan's own "Frontend Present" section and the iter-5/iter-6 dev handoffs for why this declaration
is the loop-internal workaround for `browser-qa-phase.sh`'s frontend-gated browser lane. Flagging
so the reviewer/QA/auditor do not go looking for UI changes that do not exist in this diff.

**J-06's OVERALL journey status is not claimed complete by this handoff** — only step 1 of 5
(the Card-5.1 preservation prerequisite). Steps 2-5 (`tick_recorder.py`, `vault.py`, universe
registration, the Tier-B resolution order, the real Alpaca starter-tranche recording) remain
entirely unbuilt, exactly as scoped. The evaluator determines J-05/J-06/J-10's resulting status,
not this handoff.

**The double full-engine `replay()` proof was scoped to a 3-dataset spot-check plus the existing
2-fixture byte-identical test, not all 18 real datasets.** The real corpus is 882MB across 18
files (two of them 190MB/159MB); a full double-replay of every one would be a multi-minute
compute path the era's own iteration-hygiene rail (13 of 15 referee iterations tripped step
timeouts) argues against forcing through when the actual risk surface —
`_row_to_event`/`_event_to_row`'s absent-key discipline — is symbol/size-independent and is
already proven three independent ways: (1) `load_events()` succeeding over all 9.1M real events
with exact count matches, (2) the direct JSON row-scan over all 18 files finding zero new keys,
and (3) the unmodified golden-trace/observer-equivalence/fixture-pair tests passing byte-unchanged.
Flagged for the reviewer/auditor to weigh — the developer's judgment is this is sufficient, not a
gap, but the choice is disclosed rather than silent.

**No live credentialed Alpaca fetch was run.** Per the plan, this is explicitly a nice-to-have,
never gating; the DEFINITION OF DONE requires the hermetic suite (which passed), and the "Real SDK
verification" section above goes one step further than a plain mock by exercising the actual
installed SDK's `Trade`/`Quote` model classes — but it is not a live network call. If the operator
wants a genuine live-fetch proof of real `conditions`/`exchange` values, that remains available as
a follow-up hand-verification, not blocking this iteration.

No other gaps against this iteration's own DEFINITION OF DONE from the developer's side.

## Post-audit amendment (2026-08-18, written by the auditor)

The independent audit found one CRITICAL defect this handoff did not know about and fixed it; two
claims above are amended accordingly. See
`docs/handoffs/goal-rapid-microscope-iter-7-audit.md` finding **B1**.

- **Amended:** the present-only row carry was byte-safe for reading legacy data (independently
  re-proven: full round-trip identity over all 9,145,900 rows in the 18 real datasets) — but the
  new row keys also entered `_content_checksum`, which is the sole enforcement of "split tags are
  frozen at registration". A window recorded before this iteration could therefore be re-fetched
  through the now-populating Alpaca adapter and registered a SECOND time under a DIFFERENT split.
  Fixed by hashing a tape-only projection (`datasets.py:_tape_identity_rows`), with a regression
  guard at `tests/test_datasets.py::test_the_frozen_split_guard_still_refuses_one_tape_re_fetched_with_preservation_fields`.
- **Amended:** `record()`'s docstring statement that `_content_checksum` "hashes
  `symbol`/`data_feed`/`epoch_anchor`/`events` only" now reads "…`events`, the last projected to
  tape-only". Every byte-compat number reported above remains accurate and was independently
  confirmed.
- **Suite after the fix:** 3045 passed / 8 skipped / 0 failed (+1 = the new regression guard).

# goal-rapid-microscope-iter-3 Dev Handoff

**Phase:** goal-rapid-microscope-iter-3
**Date:** 2026-08-17
**Agent:** developer
**Status:** complete

## What Was Built

- **`app/research/micro_join.py` (NEW)** — the structure x flow join (J-03). Two public entry
  points:
  - `join_playbook_signal(signal, dataset_store, snapshots_dir, config)` — joins a recorded
    playbook signal's `(symbol, trigger_ts)` (read verbatim, never re-detected) to its covering
    snapshot.
  - `join_band_touch(touch, resolver, dataset_store, snapshots_dir, config)` — joins a
    `{"symbol", "as_of_epoch"}` band-map wall touch, resolved read-only through the EXISTING
    `desk_playbook_context.BandMapResolver.resolve` (`compute=False`) — an honest
    `no_band_context` absence on a cache miss, never a fabricated wall.

  Both funnel through a shared `_join_core` that: (1) locates the covering dataset via a
  metadata-only window-containment match (`_covering_dataset`, mirroring `setups.py`'s own
  `_matching_dataset` technique — see Interpretation calls below), (2) confirms a currently-valid
  snapshot exists for it (`load_snapshot_meta`, TR-7), (3) translates the trigger's absolute UTC
  epoch into the dataset's own LOGICAL replay clock (`epoch_anchor + logical_ts`, the identical
  reconstruction `setups.py`'s `_tape_timeline` and `serializers.serialize_history` already use),
  (4) scans the snapshot's own append-ordered rows for the LAST one at-or-before the trigger
  (`_locate_at_or_before` — the lookahead rail, mechanically: a row is only ever chosen because
  its own `anchor_at` precedes or equals the trigger), and (5) builds the closed outcome set
  (spec section 4) at every horizon of section 1 (`MICRO_HORIZON_TRADES`/`_SHARES`/
  `_CLOCK_SECONDS`, transcribed verbatim as this module's own constants).
  - A closed status vocabulary (`JOIN_STATUS_JOINED` / `_NO_COVERING_SNAPSHOT` /
    `_NO_ROW_BEFORE_TRIGGER` / `_NO_BAND_CONTEXT`) — every absence is typed and honest, never
    fabricated.
  - `joinable_corpus_counts(dataset_store, playbook_store)` — the honest, real-store count behind
    the new readiness field: every recorded playbook signal whose `(symbol, trigger_ts)` falls
    inside a recorded tick dataset's own window, with a `by_setup_id` breakdown. Fails closed on a
    malformed (present-but-unparseable) `trigger_ts` (raises, never silently undercounts); skips
    (never crashes on) a structurally absent symbol/`trigger_ts` — the identical treatment
    `desk_playbook_context.record_band_context` already gives that case.
- **`app/research/micro_features.py`** — added `spread_bps(spread, mid)`, closing audit B4's
  "no spread column" gap: the quoted spread at the outcome start, in bps, served as its OWN key
  beside every outcome (`mid`/`last_trade`), never netted into either outcome's `value`.
- **`app/research/micro_snapshots.py`** — added `read_snapshot_rows(root_dir, dataset_id)`, the
  plain JSONL row reader `micro_join.py` uses (never a raw `open()` of its own) — co-located with
  the writer, per the iteration's own accessor-boundary note (see Known Issues).
- **`app/research/micro_readiness.py`** — `build_readiness` gained an optional
  `playbook_store=None` kwarg; when given, the response now carries a `joinable_corpus` object
  (`total`/`playbook_signal_count`/`band_touch_count`/`by_setup_id`), computed entirely by
  `micro_join.joinable_corpus_counts` (never re-derived here). `playbook_store=None` (every
  pre-J-03 call site, unchanged) serves the honest zero, never an error.
- **`app/research/micro_routes.py`** — `GET /research/desk/micro/readiness` now also depends on
  `desk_routes.get_playbook_store` (the EXISTING provider, reused verbatim — never a second,
  redefined one) and passes it through.
- **`runs/goal-session-rapid-microscope/journey-scripts/J-10.json`** — step 9 (Playbook Evidence
  expand) now asserts the stable `"Built from signature:"` label instead of the volatile
  per-instance hash `b06e0bc289c54d77`. A new step 10 fills the Playbook Signals section's own
  `desk-playbook-date-input` with `2026-06-22` (the same session steps 5-7 already use for
  Structure/AAPL, already proven on the store-scoped rig to carry recorded signals — iter-2's
  audit F1) and asserts the count-independent `"recorded signals, none hidden"` text — real
  content, never the `"No signals fired in this session."` empty state a wrong/default session
  produces. Steps 10-12 were renumbered to 11-13; no other step changed.

## Files Changed

- `apps/backend/app/research/micro_join.py` -- NEW: the structure x flow join (find/locate/
  outcome/join/count functions).
- `apps/backend/app/research/micro_features.py` -- MODIFY: added `spread_bps` (spec section 4's
  cost-proxy column).
- `apps/backend/app/research/micro_snapshots.py` -- MODIFY: added `read_snapshot_rows`, the plain
  reader.
- `apps/backend/app/research/micro_readiness.py` -- MODIFY: `build_readiness` gained
  `playbook_store=None` + the `joinable_corpus` field.
- `apps/backend/app/research/micro_routes.py` -- MODIFY: the readiness route now injects
  `desk_routes.get_playbook_store`.
- `apps/backend/tests/test_micro_join.py` -- NEW: TC-1/TC-2/TC-3/TC-4/TC-6, the outcome set, and
  `joinable_corpus_counts` unit tests.
- `apps/backend/tests/test_micro_features.py` -- MODIFY: `spread_bps` oracle tests.
- `apps/backend/tests/test_micro_readiness.py` -- MODIFY: the `client` fixture now also overrides
  `get_playbook_store` (hermeticity, since the route gained the dependency); 5 new TC-5
  (`joinable_corpus`) tests; `real_readiness`'s honest-zero case covered too.
- `runs/goal-session-rapid-microscope/journey-scripts/J-10.json` -- MODIFY: step 9's assertion +
  the new Playbook Signals filter step (see above).

## Interpretation calls (logged, not spec-ambiguities requiring an owner ruling)

- **`_covering_dataset` mirrors, rather than imports, `setups.py`'s `_matching_dataset`
  technique** (symbol equality + numeric-epoch window containment, ties on `(created_utc, id)`).
  A small, generic technical match over dataset metadata, not a second implementation of any
  measurement rail — the same class of judgment call `micro_readiness.py`'s own
  `_quote_rule_decides` docstring makes for mirroring a sibling module's documented technique
  rather than importing a private, single-call-site function across module boundaries.
- **`band_touch_count` is honestly zero this iteration.** No module anywhere in the shipped
  product enumerates discrete band-map wall-touch INSTANTS as a stored, countable list yet —
  identifying what counts as a "touch" is explicitly J-09's own predeclared-mechanism work (the
  iteration's own OUT OF SCOPE list). `join_band_touch` proves the join PRIMITIVE itself works
  against an explicit, caller-supplied `(symbol, as_of_epoch)` pair (TC-2, tested with a fixture
  band-map cache entry); there is simply no existing corpus of such pairs to count over yet, so
  the field reports the honest, non-fabricated zero rather than inventing a detector. Expressed as
  a named variable, never a bare literal at the return site, so a future J-09 caller wiring a real
  enumeration in changes exactly one line.
- **CLOCK_SECONDS outcome horizons sample the trade-anchored representation.** Spec section 4
  wants "quote mid at the horizon boundary"; the section 2.4 benchmark (J-02) chose trade-anchored
  rows as the ONE snapshot representation — there is no standalone quote row to sample instead. A
  CLOCK horizon's mid is therefore read off the nearest at-or-before TRADE row, the identical
  lookahead-clean technique `_locate_at_or_before` already uses for the feature-at-trigger row.
- **`build_readiness(..., playbook_store=None)` defaults to the honest zero**, rather than making
  the parameter required, so every pre-J-03 call site (and the module-scoped real-corpus test
  fixture) keeps working unchanged — "no playbook evidence was even checked" is a true statement
  in that case, never a fabricated count.
- **"The Playbook Signals filter" (IN SCOPE / TC-8) reads as the section's own session-date
  input**, not a literal per-symbol text filter — no such control exists on `/desk` (the two
  actual filter widgets, `desk-playbook-band-filter`/`desk-playbook-inside-filter`, narrow an
  ALREADY-loaded session's rows by band/room, not by symbol; a session covers every scanned
  symbol at once). J-10.json's new step therefore fills `desk-playbook-date-input` with
  `2026-06-22` and asserts the count-independent `"recorded signals, none hidden"` label (the
  UNFILTERED-cohort summary line, `page.tsx:7666`) rather than a specific signal count, which
  could legitimately drift as the rig's recorded corpus grows.
- **The outcome set implements all three spec section 1 horizon families** (trades/shares/
  clock_seconds, 7 outcome entries total per join), not only what TC-1/TC-2's own acceptance
  literally asserts — the iteration's IN SCOPE explicitly calls for "spec section 4's closed
  outcome set" to be implemented, and a caller (J-09) will need every horizon, not a partial set
  quietly deferred.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/` (bare, no extra `-q` —
`pyproject.toml` already sets `addopts = "-q"`; per the iter-0/iter-2 lesson, a second `-q` makes
it `-qq` and suppresses the summary line).
Result: **2866 passed, 8 skipped, 0 failed** (446.82s). iter-2's own final (post-audit) count was
2835/8/0; this iteration's own DEFINITION OF DONE floor (≥ 2,828, the pre-audit dev number) is
cleared with room to spare. All new tests are additive; nothing pre-existing changed behavior.

### Era-open invariant re-check (J-10 / iteration-0 baseline)

- `Config().config_fingerprint()` -> `08e471b10130e1e2` -- unchanged (re-verified directly).
- All 6 `referee_*.py` SHA-256 hashes -- re-verified directly (not merely via the suite), and
  byte-identical to the iteration-0/iter-2 listing:
  ```
  482f38a11740bc839038290fc2a0e131f649a23f17265cbca0f2aa19fe07e1c5  referee_evidence.py
  03840c863b1e1f382ad2588d3bb6d8dc0e36a70582c3cb7a716638dabef32d99  referee_registry.py
  0cc3a06f7b382c63d544886ec74a47f2414612fc77dd3dac444b00cc35216140  referee_routes.py
  6dd807b5ab69af033686a395484b1b10515d0f453a79c0943e534a578259786c  referee_adjudicate.py
  fba8816a5d4901ea1eeb7faa71e350538f546a2a3af1f9edb5f6f5aa1ec5271c  referee_stats.py
  34917e381e4169aa029f5d0e18228fde75e4d3db5acec516f937e3ef3b371603  referee_null.py
  ```
- `desk_playbook.py` / `desk_playbook_context.py` -- byte-unchanged this iteration (`git status`
  confirms zero diff to either file); the same two SHA-256 digests are pinned as a standalone
  regression guard in `test_micro_join.py` (TC-4), independent of the referee-era guard that
  already covers the context module.
- `tests/test_observer_equivalence.py` and `tests/test_dense_replay_gate.py` -- zero diff to
  either file (confirmed via `git status`); both pass as part of the full suite above.
- MCP `EXPECTED_TOOLS` -- still the 22-tuple (unchanged; no MCP tool added this iteration; the
  guard test is part of the full green suite above, not separately re-verified).
- `app/engine/` -- zero diff (`git status` confirms).

### Real-corpus rebuild (an expected consequence of adding `spread_bps`)

`micro_snapshots.feature_source_hash()` hashes the source bytes of BOTH `micro_features.py` and
`micro_observer.py` (iter-2's own B3 fix) -- adding `spread_bps` to `micro_features.py` therefore
re-keyed every one of the 18 real legacy-corpus snapshots (an honest TR-7 MISS, never a served
stale value). `run_snapshot_build_and_record` rebuilt all 18 during this iteration's own test run
(`test_micro_snapshots.py`'s TC-12 real-corpus acceptance, inside the full suite above) --
confirmed both by the suite's own green pass and by a live, throwaway backend instance (started
on a scratch port, stopped cleanly afterward) whose `GET /research/desk/micro/readiness` served
the correct real totals (12 distinct symbol-days / 18 datasets / ~3.01 session-equivalents) AND a
real, non-fabricated `joinable_corpus` (`{"total": 2, "playbook_signal_count": 2,
"band_touch_count": 0, "by_setup_id": {"range_trade": 2}}` -- 2 of this host's own recorded
playbook signals genuinely fall inside the real tick corpus's recorded windows). `micro_join.py`
touches nothing in `_resolve_depletion`/`finalize`/any other observer arithmetic -- only the
NEW `spread_bps` pure function was added, so this rebuild changes no persisted VALUE, only the
identity that verifies them.

## Known Issues

- **The already-flagged spec section 3 window-mean `quote_imbalance`/`microprice` gap (iter-2
  audit B4) is still open — documentation only this iteration, not built.** Section 3 requires
  quote imbalance and microprice served "both instantaneous at the in-effect NBBO and as
  feature-window means"; only the instantaneous forms exist on a snapshot row
  (`micro_observer.py`'s `quote_imbalance`/`microprice` fields). No window-mean form exists, and
  this iteration's `micro_join.py` reads the row's instantaneous fields verbatim like everything
  else — it neither adds nor needs the window-mean form for J-03's own acceptance (TC-1/TC-2/TC-3/
  TC-6 assert `cumulative_delta`/`spread`/`tape_state`/the `deferred` list, none of which are
  window-mean quote features). Still J-05's inheritance once it starts conditioning on this
  family; not this iteration's scope to build.
- **Audit B5 (a price-change-terminated depletion's `available_at` timing) remains an open
  owner-ruling item, unaffected by this iteration.** `micro_join.py` never reads `quote_depletion`
  completions specially -- it passes through whatever `deferred` list a matched row already
  carries, verbatim (TC-6). Still scoped to "before J-05" per iter-2's audit; not touched here.
- **`micro_join.py` reads snapshot rows through a PLAIN reader
  (`micro_snapshots.read_snapshot_rows`), not an origin-fenced accessor.** This is the
  iteration's own documented boundary (assumption-ledger entry, goal-decomposer's NOTES):
  `micro_accessor.py` and its TR-3 import-ban guard are J-05 deliverables, and the corpus this
  iteration reads (the 12 legacy symbol-days) is still fully exploratory, so there is no sealed
  shard yet for an accessor to protect. J-05 is expected to re-point this read through the
  accessor as part of its own scope, not to have the accessor built early to pre-empt it.
- **`micro_join.py`'s outcome set is unconditioned (no per-candidate feature conditioning).**
  Outcome start = the trigger's own `anchor_at` verbatim (this iteration's own assumption-ledger
  entry — no per-candidate conditioning feature set exists before J-04's Scout). A future caller
  conditioning on a DEFERRED feature (whose `available_at` is later than its own `anchor_at`) must
  call `micro_features.require_outcome_start_not_before_conditioning` itself, at the point it
  builds that condition — this join's own outcome rows do not attempt that generality.
- **J-10's overall verdict is intentionally left to the evaluator, per this iteration's own
  DEFINITION OF DONE note.** This iteration repairs the two specific rig-data-caused browser gaps
  iter-2's audit F1 identified (the volatile-hash step-9 assertion; the empty-session Playbook
  Signals check) — it does NOT complete the TR-1...TR-22 trap suite (structurally spread across
  J-02...J-07 by goal.md's own design) or re-photograph the Microscope Readiness panel with fuller
  corpus totals (deferred, per the iteration's OUT OF SCOPE list, until a later iteration seeds
  the rig with more tick data).
- **No dedicated browser pass was run for J-10.json's new/repaired steps this iteration.** J-03
  itself is keyless/automated (goal.md's own framing; no browser check in this iteration's TESTING
  REQUIREMENTS). The two J-10.json edits were verified STATICALLY against the current frontend
  source (`grep`-confirmed: `data-testid="desk-playbook-date-input"` exists unconditionally inside
  the always-rendered Playbook Signals section, `page.tsx:8564`; the literal string
  `"Built from signature: "` precedes the volatile hash span, `page.tsx:4690`; the unfiltered-
  cohort summary text is literally `"${record.signals.length} recorded signals, none hidden"`,
  `page.tsx:7666`) and against iter-2's own audit F1, which directly observed 2026-06-22 rendering
  5 recorded signals live on this exact rig. A live browser pass (`rm -rf apps/frontend/.next` +
  rebuild first, per T-9) is QA's next step, not re-run here — "Frontend Present: no" for this
  iteration and zero `.tsx`/frontend source files were touched (`git status` confirms).

## Pre-handoff verification

- **Service startup:** no top-level `scripts/dev.sh` exists in this repo currently (searched;
  none found — `.claude/project-template.md`'s STACK/SERVICE START COMMANDS sections are also
  still the unfilled generic template, not project-specific). Verified the BACKEND directly
  instead: started a throwaway `uvicorn app.main:app` on a scratch port (8791, not the pipeline's
  own 8000/8301), confirmed `GET /health` (200) and `GET /research/desk/micro/readiness` (200,
  real data, `joinable_corpus` present and correct — see above), then stopped the exact PID
  (2411263, confirmed via `ss -ltnp` before killing) and confirmed the port is free. No frontend
  source changed this iteration, so no frontend rebuild/start was attempted.
- **External integrations:** N/A — no new adapter/scraper/external API call this iteration.
- **Native dependency binaries:** N/A — no new dependency.

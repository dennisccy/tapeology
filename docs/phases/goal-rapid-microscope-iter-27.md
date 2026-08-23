# Goal Iteration 27 — Make the suite finishable; serve the referee-evidence disclosure

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** rapid-microscope
- **Iteration:** 27
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — cross-cutting: fixes a root cause shared by two backend test files
  (`test_micro_readiness.py` = J-01's own suite, `test_micro_join.py` = J-03/J-05 territory) plus a
  frontend + guard change on the shared, shipped Referee Registry section (J-10's "traps armed,
  sentinel green" territory); the interaction of suite hermeticity + a rail-sensitive shipped-section
  UI change is not covered by any single journey's own test suite. (This also matches the engine's
  own binding depth recommendation for this iteration.)
- **Frontend Present:** yes
- **Target journeys:** J-01, J-10
- **Required-still-passing journeys:** J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09
- **Anti-goal reminders:**
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five
    states and thresholds, the frozen structure computations, the JSON `BarStore`, and every
    KEPT surface's behaviour stay byte-identical. New work is additive and versioned beside
    them, never a mutation of them. *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*
  - Foundation invariant 5: **the kept surfaces as shipped**: the cockpit, `/structure`, and
    every shipped `/desk` section (Playbook, band context, cohorts, Referee Registry/
    Adjudications/Runs) keep working exactly as shipped. Rapid-Microscope sections land as NEW
    sections below the shipped ones; no shipped section, column, or behavior changes. *(This
    iteration's ONE deliberate, owner-authorized exception is spelled out in BACKGROUND below.)*
  - Foundation invariant 2: "...and every `referee_*` module, the referee spec, and the
    `pnl_scan` promotion interlock — all behaviorally byte-identical. This era READS them; it
    never touches, re-implements, re-tunes, or feeds back into any of them. There is NO
    deliberate exception this era." *(critical — `referee_evidence.py` and `referee_routes.py`
    are NOT touched by this iteration; see BACKGROUND.)*
  - Foundation invariant 3: "The stores — every EXISTING registered `BarStore`/`DatasetStore`
    artifact stays byte-identical with its checksum verifying; no legacy file is ever rewritten
    or reserialized; append-only immutability, frozen splits, parsing compatibility ... are
    untouched in discipline."
  - Referee-era rail: "no confirmatory claim outside the gauntlet" *(critical)*
  - Referee-era rail: "the Referee never feeds back" *(critical)*
  - Constraint: **Hermetic tests** — keyless on committed fixtures (synthetic corpora with known
    truth; the spec's oracle vectors; fixture shards); no test fetches the network; real
    recordings and tranche acts are operator-run, reported run-or-not-run, never CI gates; heavy
    suites respect the pinned time budgets.
  - Constraint: "Store discipline: frozen, checksummed, append-only records; record id = pure
    function of the key; duplicate key raises; corrupt files surfaced, never overwritten; NO
    update/delete/supersede path (source-scan guard-tested); ..."

## GOAL

Make the backend test suite finish reliably without starving the live backend (root-causing six
straight rounds of blank pictures and unverifiable "all tests pass" claims), and serve the
owner-ruled r5-point-7 disclosure sentence beside the Referee Registry's legacy, seal-unaware
dataset/trade counts on `/desk` — the largest non-owner-owned item standing between this era and
certification.

## BACKGROUND

Iter-26 (CONTINUE, full depth) closed two open items but surfaced a NEW one the auditor traced to
root cause: `test_micro_readiness.py`'s `real_readiness`/`real_dataset_records` fixtures and
`test_micro_join.py`'s two real-corpus tests construct `DatasetStore` against the operator's real
`.data/datasets` directory (now 26 GB / 98 files, up from the ~0.92 GB / 18 files it was at era
open, because the J-06 recorder's sealed tranche lives in the SAME store) with **zero durable
caching** — `MicroReadinessCache`'s cache DB is rebuilt in a fresh `tmp_path_factory` dir every
single pytest invocation, and neither `DatasetStore` construction passes `index_db_path=`, so every
run re-parses and re-checksums the whole 26 GB from scratch. Production `routes.py` already avoids
exactly this by wiring `index_db_path=".../dataset_index.db"`; `micro_readiness.py` already owns a
checksum-keyed `MicroReadinessCache` for the one genuinely expensive per-shard computation
(`fallback_frac`). The fix this iteration is to point both test files at persistent, on-disk copies
of these SAME existing, already-hardened caching primitives — never a new cache class, never a
change to any production module. Iter-26's own lesson (second entry) names this precise failure
mode as "an infra bomb"; per the priority rubric this is an unblocker (it is why "all tests pass"
has been unverifiable and why browser evidence has gone missing without an obvious cause) and per
`.claude/anti-patterns` caching discipline it is safe by construction here: both caches key on
content (checksum / `(size, mtime_ns)`) against append-only, checksummed, immutable dataset files
(Store discipline anti-goal), so there is no second mutable input of the kind iter-26's OTHER
finding (`BandMapResolver` cache) warned about.

The second item is iter-26's own next-step (3): the owner's 2026-08-18 r5-point-7 ruling
(`docs/rapid-validation-spec.md` section 10, point 7) requires the verbatim caveat sentence to be
served beside `referee_evidence.strategy_trade_readiness`'s output, because that legacy metric
counts dataset FILES through its own enumeration and may include withheld, unexposed
Rapid-Microscope shards. Both `referee_evidence.py` and `referee_routes.py` are frozen `referee_*`
modules this era (SHA-256-pinned, re-verified every iteration) — the ruling explicitly forbids
editing either or intercepting `DatasetStore` to change frozen behaviour indirectly — so the caveat
can ONLY be served at the frontend rendering layer, as static copy beside the already-served
`strategy_trade` fields (`apps/frontend/app/desk/page.tsx`'s `referee-evidence-strategy-block`);
this is exactly what the spec's own "wherever that metric is served" clause resolves to, since no
MCP tool proxies `GET /research/desk/referee/evidence` at all (confirmed by grep — only
`desk_referee`/`desk_referee_registry` exist, proxying different routes). This is this iteration's
one deliberate exception to Foundation invariant 5 ("no shipped section, column, or behavior
changes") — explicitly owner-authorized by the r5-point-7 ruling itself, adding descriptive copy
only, never a computed value, never a behavior change. **Investigation finding, logged to the
assumption ledger:** the ruling's OTHER clause — "add a guard/source-scan proving the gates read
only the seal-aware owner" — is already built and passing (`test_micro_no_referee_evidence_guard.py`,
committed iter-21, 4/4 green today); only the caveat-serving half remains, narrowing this
iteration's scope accordingly.

Depth is `full` per the engine's binding recommendation for this iteration (see dispatch metadata);
independently justified under trigger 1 (cross-cutting — see metadata above). Target journeys are
J-01 (its own test file is edited) and J-10 (the sentinel/guard/kept-surface territory this whole
iteration lives in); Required-still-passing widens to all eight remaining journeys, matching a full
round's periodic-regression spirit — J-07 carries no golden by design (binding, unchanged). Two
"Do not redo" make-up captures from `iteration-state.md` (Desk readiness figures; Scout Ledger
family row + "variants tried" line) are NOT this iteration's goal (rule 7) — they are expected to
ride passenger on this round's own browser-qa pass over J-01/J-10 and the replay of J-08, and are
noted here only so the evaluator does not mistake a natural side effect for manufactured scope. The
owner-owned items (chain-ledger identity commitment; the sealed judge's money-floor question) are
excluded per iter-25/26's own "drop 4 and 5, never 1" ordering — neither blocks any journey.

## IN SCOPE

### Backend
- [ ] `apps/backend/tests/test_micro_readiness.py`: give `real_readiness`/`real_dataset_records`
      (currently lines ~456-479) a PERSISTENT, gitignored on-disk cache path (never a fresh
      `tmp_path_factory` dir) for both the `MicroReadinessCache` DB and the `DatasetStore`'s
      `index_db_path=` — reusing the SAME production caching primitives `routes.py` already wires,
      never a new cache mechanism. The real 18-legacy-dataset assertions (TC-1..TC-5) must keep
      passing byte-identically, only faster on a warm cache.
- [ ] `apps/backend/tests/test_micro_join.py`: give
      `test_tc16_real_corpus_joinable_corpus_arithmetic_is_unchanged_by_the_passenger_fixes` (real
      corpus, ~line 942) and `test_tc4_real_corpus_join_playbook_signal_is_unaffected_by_the_
      accessor_re_point` (~line 962) the same durable `index_db_path=` treatment on their
      `DatasetStore` construction.
- [ ] Add (or extend `test_micro_no_referee_evidence_guard.py`) a small static-scan test asserting
      the spec section 10.7 verbatim caveat sentence is defined exactly ONCE as a shared string
      constant in the frontend source and matches `docs/rapid-validation-spec.md` section 10.7
      character-for-character.
- [ ] Re-hash all six `referee_*.py` files after this iteration's diff and confirm 6/6 byte-identical
      to the iteration-0 listing (`docs/handoffs/goal-rapid-microscope-iter-0-dev.md:75-81`) — no
      code change expected, verification only.

### Frontend
- [ ] `apps/frontend/app/desk/page.tsx`: inside the existing `referee-evidence-strategy-block`
      (Referee Registry → Strategy Family, ~lines 5150-5217), render the spec section 10.7 verbatim
      caveat sentence beside the `Datasets`/`Trades`/tick-gate figures, under a NEW `data-testid`
      (never reusing an existing shipped testid or heading string — T-11 discipline).

### New user-facing capability
None (disclosure only — no new action, no new page).

### New information displayed
The verbatim disclosure sentence next to the Referee Registry's Strategy Family Datasets/Trades
figures: *"Legacy Referee readiness metric — seal-unaware in the Rapid Microscope era. It may
include withheld/unexposed Rapid-Microscope shards and must not be used as the canonical
Rapid-Microscope readiness count."*

### New user actions
None.

### UI surface changes
One new `<p>`/`<li>` element inside the already-shipped Referee Registry → Strategy Family block
on `/desk`. No new section, no new page, no nav change.

### Product surface delta
The desk operator reading the Referee Registry can no longer mistake the legacy, seal-unaware
dataset/trade counts for the era's own canonical, seal-aware `micro_readiness` numbers.

### Blueprint conformance
Both changes land under the already-registered Desk → Referee Registry ("Unchanged owners" row)
and Desk → Microscope Readiness (J-01) homes in `blueprint.md`'s Information Architecture; no
nav-skeleton change.

### Data-contract additions
None. The caveat is a static, non-computed copy string (verbatim from
`docs/rapid-validation-spec.md` section 10.7), rendered beside the already-registered
`strategy_trade.dataset_count`/`trade_count`/`tick_gate_statement` fields whose owner
(`referee_evidence.py`) and endpoint (`GET /research/desk/referee/evidence`, via
`referee_routes.py`) are unchanged and untouched. `blueprint.md` carries an iter-27 note
recording this explicitly (already written).

## OUT OF SCOPE

- Editing `referee_evidence.py`, `referee_routes.py`, or any other `referee_*.py` file.
- Any new MCP tool or proxy for `GET /research/desk/referee/evidence` (none exists today; none is
  needed — the caveat is frontend-only copy).
- Re-building `test_micro_no_referee_evidence_guard.py`'s import-ban guard — it already exists and
  passes; this iteration only re-runs it unmodified as a regression check.
- Recording more real tape, exposing/assigning any sealed shard, running J-09's studies against the
  real recorded corpus, or moving the fingerprint pin `08e471b10130e1e2`.
- The chain-ledger identity commitment and the sealed judge's money-floor question (owner-owned,
  block no journey).
- Making the two make-up captures (Desk readiness figures; Scout Ledger "variants tried" row) a
  goal of this iteration — they may ride passenger on the target/required-still-passing browser
  passes below, never as a planned deliverable.
- Any new Config field, any fold/grid/threshold change, any change to a frozen playbook detector.

## DEFINITION OF DONE

- [ ] Target journeys J-01, J-10 pass via browser-qa-agent, with fresh screenshots (no screenshot
      ⇒ `unknown`, never `passing` — T-10).
- [ ] Required-still-passing journeys J-02..J-09 remain green (deterministic replay + LLM fallback,
      mechanically verified).
- [ ] No anti-goal violation introduced; all six `referee_*.py` files re-hash byte-identical to the
      iteration-0 listing.
- [ ] The full backend suite (`pytest tests/`) runs to completion with an explicit PASS/FAIL summary
      line (never a truncated process silently reporting `EXIT_CODE=0`), and neither
      `test_micro_readiness.py` nor `test_micro_join.py` is the slowest file in the run on a warm
      cache.
- [ ] `test_micro_no_referee_evidence_guard.py`'s existing 4 tests still pass unmodified.
- [ ] Unit tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-rapid-microscope-iter-27-dev.md`, including
      before/after wall-clock timing evidence for the two fixed test files.

## TESTING REQUIREMENTS

- Browser: J-01 (Microscope Readiness + Referee Registry proximity), J-10 (sentinel — traps armed,
  Referee sections render).
- Unit/integration: `test_micro_readiness.py` real-corpus TC-1..TC-5, `test_micro_join.py` TC-16 and
  the J-05 TC-4 real-corpus test, the new/extended caveat-presence guard,
  `test_micro_no_referee_evidence_guard.py` (unmodified, re-run), the referee-module SHA-256
  re-check.
- Error cases: a corrupted dataset file must still surface as an explicit `integrity_errors` row
  (unchanged behavior) even when the durable index cache is warm — the cache must never mask a
  content-checksum failure.

Test-first contract:

- TC-1: given `MicroReadinessCache`'s DB and `DatasetStore`'s `index_db_path` in
  `test_micro_readiness.py` point at a persistent on-disk location instead of a fresh
  `tmp_path_factory` dir, when `pytest tests/test_micro_readiness.py -k real` is run twice back to
  back with no source changes between runs, then the second (warm) run completes in under 60
  seconds wall-clock and both runs produce byte-identical assertion results (TC-1..TC-5 all pass).
- TC-2: given the same durable `index_db_path=` treatment applied to
  `test_micro_join.py`'s two real-corpus tests, when they are run twice back to back, then both
  runs complete in under 30 seconds combined on the second (warm) run, and
  `counts["playbook_signal_count"] == 2`, `counts["by_setup_id"] == {"range_trade": 2}`, and
  `counts["playbook_integrity_errors"] == []` hold unchanged in both runs.
- TC-3: given the full backend suite is run once end to end (`pytest tests/`), when it completes,
  then the process exits with an explicit pass/fail summary line printed by pytest itself (never a
  process killed mid-run), and the combined runtime of `test_micro_readiness.py` +
  `test_micro_join.py` is not the largest single contributor to total suite wall-clock time on a
  warm cache.
- TC-4: given `apps/frontend/app/desk/page.tsx`'s Referee Registry → Strategy Family block, when
  the frontend source is grepped for the verbatim sentence "Legacy Referee readiness metric —
  seal-unaware in the Rapid Microscope era. It may include withheld/unexposed Rapid-Microscope
  shards and must not be used as the canonical Rapid-Microscope readiness count.", then it is found
  exactly once, sourced from a single shared string constant (never duplicated ad hoc), and its
  text matches `docs/rapid-validation-spec.md` section 10.7 character-for-character.
- TC-5: given `/desk` is loaded live (backend + frontend booted, `rm -rf apps/frontend/.next` +
  rebuild per T-9) with the Referee Registry section expanded, when browser-qa captures the
  Strategy Family block, then the screenshot shows the new caveat text rendered beside the
  Datasets/Trades figures, under a data-testid distinct from every existing shipped testid in that
  block.
- TC-6: given `tests/test_micro_no_referee_evidence_guard.py`'s existing 4 tests (TC-10, committed
  iter-21), when run after this iteration's changes land, then all 4 still pass unmodified,
  proving no Rapid-Microscope module began importing/calling the seal-unaware
  `strategy_trade_readiness`/`referee_evidence` functions as a side effect of this iteration.
- TC-7: given the six `referee_*.py` files' iteration-0 SHA-256 listing
  (`docs/handoffs/goal-rapid-microscope-iter-0-dev.md:75-81`), when re-hashed after this
  iteration's full diff, then all six hashes are byte-identical to that listing (`git diff` on each
  file is empty).
- TC-8: given J-01's stored golden `journey-scripts/J-01.json`, when replayed via `demo_runner.py
  --mode verify` post-change, then it passes end to end with 0 failed steps.
- TC-9: given J-10's stored golden `journey-scripts/J-10.json` (sentinel), when replayed, then it
  passes end to end with 0 failed steps, including its existing step-12 "variants tried" assertion,
  unaffected by the new caveat markup elsewhere on the page.
- TC-10: given a deliberately corrupted dataset file is planted in a scratch copy of the store used
  by `test_micro_readiness.py`'s real-corpus fixtures, when the fixture is built against that
  scratch copy with a WARM durable index/cache pointed at a DIFFERENT store's content, then the
  corrupted file's content-checksum mismatch still surfaces as an `integrity_errors` row (the cache
  never masks or bypasses checksum verification for content it has not actually verified).

## NOTES

- Lesson applied (iter-26, second entry): real-`.data`-store test fixtures are a slow-acting infra
  bomb; this iteration's fix reuses the SAME already-hardened, checksum/mtime-keyed caching
  primitives production code already relies on (`DatasetIndex`, `MicroReadinessCache`) rather than
  inventing a new cache class — avoiding the SAME iteration's other lesson (a cache with a second
  mutable input can serve a permanent wrong answer); both caches here key on immutable,
  checksummed, append-only content, so there is no second mutable input to go stale.
- Lesson applied (iter-25, first entry): a "guard already built" claim was re-derived from the code
  today (`test_micro_no_referee_evidence_guard.py` re-run, 4/4 green), not copied forward from the
  stale `iteration-state.md` phrasing — see the assumption-ledger entry for iter-27.
- Lesson applied (iter-25, second entry / iter-24 T2): the deterministic replay lane structurally
  cannot execute a target journey's OWN golden in the round that touches it — J-01 and J-10 (this
  round's targets) must get genuine browser-qa (LLM) verification this round, not a replay-only
  claim; TC-8/TC-9 above cover their goldens being re-run in a LATER context, but this round's own
  DoD leans on the browser-qa pass (first DoD bullet), not the replay lane, for J-01/J-10 themselves.
- Lesson applied (iter-22, second entry / this session's precedent): a demo/showcase step against a
  raw `GET /research/...` address 404s through the frontend port rewrite — the new caveat's evidence
  must be captured through `/desk` itself, never a bare API URL.
- The two make-up captures named in `iteration-state.md` (Desk readiness figures; Scout Ledger
  family row + "variants tried" line in frame) are expected to be satisfied as a natural side
  effect of this round's own J-01/J-10 browser-qa pass and J-08 replay — flag this to the evaluator
  rather than claiming it as planned scope, per rule 7.

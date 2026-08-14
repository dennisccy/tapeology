# Goal Iteration 1 — J-01: the evidence readiness fold (Playbook + strategy counts)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** referee
- **Iteration:** 1
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes (no frontend code changes this iteration — J-01 is backend-only per
  goal.md's `(Keyless; automated.)` marker; browser-qa still runs the J-10 regression sentinel:
  cockpit `/`, `/structure`'s AAPL Load, and every shipped `/desk` section, per the "rides every
  iteration" binding note in `iteration-state.md`)
- **Target journeys:** J-01
- **Required-still-passing journeys:** J-10
- **Anti-goal reminders:** (verbatim from `docs/goal.md`; the subset this iteration's build
  surface actually touches — see full list under § Anti-goals for the rest)
  - 3. **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five
    states and thresholds, the frozen structure computations, the JSON `BarStore`, and every
    KEPT surface's behaviour stay byte-identical. New work is additive and versioned beside
    them, never a mutation of them. *(critical)*
  - 6. **Single source of truth** — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*
  - 9. **Immutable data** — registered datasets and bar series are append-only, checksummed,
    never re-tagged, never deleted, never content-perturbed. Splits are frozen at
    registration. *(critical)*
  - **No threshold or definition tuning, anywhere, ever.** Detector constants, band-context
    constants (`70 bps`, `(1R, 2R)` edges), and cohort vocabulary are frozen; `room_r`,
    backing, headroom never become detector gates; no code path iterates any threshold against
    outcomes (source-scan guard-tested). A genuine bug fix is a named revision that re-keys,
    never an edit of recorded meaning.
  - **No fingerprint epoch movement.** Zero new Config fields expected; Path A if one is
    unavoidable; the pin `08e471b10130e1e2` does not move.
  - **The Referee never feeds back.** No referee output gates, filters, ranks, or tunes any
    detector, context, screen, or strategy computation (import-ban + source-scan
    guard-tested); the frozen research vocabulary stays frozen. *(critical)*

## GOAL

Backend-only: the system can answer, from one honest endpoint, exactly how much Playbook and
strategy evidence already exists — per-`(setup, side)` occurrence and session counts at the
current detector basis, plus strategy dataset/split/trade counts and the honest statement that
the tick-data gate remains unmet — the first real Referee artifact, and the foundation every
later Referee journey (J-02 through J-09) depends on.

## BACKGROUND

Iteration 0's baseline recorded J-01 through J-09 failing and J-10 partial, and its evaluator
explicitly recommended building J-01 alone at lean depth next: the first backend slice that
reports existing evidence, because goal.md's stated dependency order
(J-01 → J-02 → … → J-09) makes every later Referee journey depend on this count existing
first. Depth is lean per the binding recommendation, and no escape condition holds: the prior
verdict was `CONTINUE` (not ESCALATE), no `coherence.md` was produced for iteration 0 (a
zero-diff baseline had nothing structural to audit, so it is not a FAIL either), consecutive
lean iterations sit at 0 of the 6-iteration hardening cadence, and J-01 is explicitly
backend-only per goal.md's own `(Keyless; automated.)` marker — not a brand-new full-stack
journey. Per the binding "Do not redo" list, this iteration does not re-verify the kept
product, re-draft `blueprint.md`, or re-prove the absence of `referee_*.py` files — it builds
directly on iteration 0's already-confirmed absence and the already-drafted blueprint row for
this exact endpoint. Target selection is a single journey (J-01), matching rubric rule 3
(smallest unblocker) and the evaluator's explicit single-journey recommendation — no deviation
to explain.

## IN SCOPE

### Backend
- [ ] New `app/research/referee_evidence.py` — the readiness fold (first slice of the
      evidence contract): playbook-family per-`(setup, side)` `n`/`n_sessions` plus totals
      (records, distinct sessions, signals at the current `detector_basis`), read from the
      existing `PlaybookStore` (`desk_playbook.py`, anchors: `playbook_parameters()` :246,
      `PlaybookStore.newest_for_date` :956); strategy-family dataset/split/trade counts, read
      from `store.py`/`datasets.py`; the honest tick-gate-unmet statement (~150 symbol-day
      gate vs. the recorded tick corpus); the Card-6.4 `basis_caveats` disclosure text (authored
      for the first time this iteration — see NOTES). Pure aggregation over existing
      records — zero recomputation of anything Playbook or strategy already owns.
- [ ] New route `GET /research/desk/referee/evidence`, registered in
      `app/research/desk_routes.py` (or a new referee-scoped router file — developer's choice
      of file organization), wired to `referee_evidence.py`, following the desk router's
      established never-404-on-absence convention (see anchors: `router = APIRouter(prefix=
      "/research/desk", ...)` in `desk_routes.py`).
- [ ] New `tests/test_referee_guards.py` — the two guard tests goal.md's J-01 names: (a) the
      `playbook-band-context-v3` spec-drift pin (asserts `docs/playbook-detector-spec.md` §6's
      heading and `PLAYBOOK_CONTEXT_ALGORITHM_VERSION` constants line both name it exactly
      where `desk_playbook_context.py` :131 does) plus a zero-diff source-hash pin on
      `desk_playbook_context.py` (the `hashlib.sha256(inspect.getsource(...))` idiom already
      used by `test_desk_playbook_guards.py::test_decline_disclosure_doc_edit_left_the_
      capitulation_code_byte_unchanged`); (b) the `docs/research-directions.md`
      catalog-reconciliation string-presence pins (status-table rows for eras 5/5B/5C/5D/B/B2
      and the Card 6.2/6.3 "AMENDED 2026-08-14" notes — all already present; this test only
      pins them so they cannot silently regress).
- [ ] New hermetic fixture tests for the endpoint (committed synthetic Playbook + strategy
      corpora with hand-computed expected counts, covering the zero-corpus honest-empty case).
- [ ] Zero new `Config` fields; zero diff to `desk_playbook*.py`, `desk_forward.py`,
      `levels.py`, `tradability.py`, `setups.py`, `pnl_scan.py`.

### Frontend
- (none — J-01 is backend-only; goal.md marks it `(Keyless; automated.)`)

### New user-facing capability
None directly user-facing yet — this is a backend-only slice. The readiness numbers become
operator-visible later, inside J-07's `/desk` shortlist (a future iteration reads this exact
endpoint).

### New information displayed
None (no UI change this iteration).

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None visible in the UI. `GET /research/desk/referee/evidence` becomes a new, queryable backend
endpoint reporting honest per-family evidence readiness — the first concrete Referee artifact,
though not yet rendered anywhere.

### Blueprint conformance
Fulfills the already-registered blueprint Data Contract row **"Referee evidence coverage +
per-family readiness"** (owner `app/research/referee_evidence.py`; endpoint
`GET /research/desk/referee/evidence`) exactly as drafted at baseline — owner and endpoint are
unchanged, so `blueprint.md` needs no edit. No new page: per the blueprint's Feature/journey
homes table, J-01 has no dedicated page (`n/a` — it surfaces later inside J-07's shortlist
under Desk).

### Data-contract additions
This iteration pins the already-registered row's field-level shape for the first time (no new
blueprint row — see Blueprint conformance):

```
GET /research/desk/referee/evidence ->
{
  "playbook_occurrence": {
    "detector_basis": str,            # sha256(canonical(playbook_parameters()))[:16]
    "config_fingerprint": str,        # == Config().config_fingerprint()
    "records": int,
    "distinct_sessions": int,
    "signals_at_current_basis": int,
    "per_setup_side": [
      {"setup": str, "side": "long" | "short", "n": int, "n_sessions": int}, ...
    ]
  },
  "strategy_trade": {
    "dataset_count": int,
    "per_split_counts": {"train": int, "holdout": int},
    "trade_count": int,
    "tick_gate_met": bool,            # honest false at today's corpus
    "tick_gate_statement": str,       # names the ~150 symbol-day gate and the shortfall
    "basis_caveats": [str]            # Card-6.4 forming-bar disclosure (authored this iteration)
  }
}
```

Top-level keys `playbook_occurrence` / `strategy_trade` deliberately match J-02's forthcoming
`evidence_family` enum values verbatim (`docs/referee-statistical-spec.md` §2) so J-02 extends
this shape rather than renaming it. No other new displayed/served value this iteration.

## OUT OF SCOPE

- J-02's full observation contract (`evidence_family`, `observation_id`, `anchor_ts`,
  `cluster_key`, per-observation `provenance`) — J-01 serves AGGREGATE counts only, never
  individual observations.
- J-03's statistics core, oracle suite, and attestation — no CI/p-value/bootstrap work this
  iteration.
- J-04's matched nulls, J-05's registry, J-06's adjudication — deferred, in dependency order.
- J-07's and J-09's `/desk` UI surfacing and the two new MCP tools — zero frontend, zero MCP
  changes this iteration.
- J-08's promotion interlock / `authorize_promotion` — untouched; `pnl_scan.py` stays
  byte-identical.
- The derived observation cache (`TAPEOLOGY_REFEREE_OBS_CACHE_DB`, `desk_meta_cache`
  contract) — that caches J-02's per-observation records, not J-01's aggregate readiness counts
  (which read the store directly; no cache needed at this corpus size).
- Any edit to `docs/research-directions.md` or `docs/playbook-detector-spec.md` — this
  iteration only PINS the already-reconciled text with guard tests, never edits either
  document.
- Any real registration/evaluation/null-build operator act — none of that machinery exists yet.
- Re-verifying or re-scoring J-10 as a target journey — it rides along only as
  Required-still-passing per the binding "Do not redo" note ("Do NOT plan an iteration whose
  goal is J-10").

## DEFINITION OF DONE

- [ ] Target journey J-01 passes: `GET /research/desk/referee/evidence` serves the per-family
      readiness shape with fixture-exact playbook and strategy counts (goal.md marks J-01
      `(Keyless; automated.)` — no browser check required for this journey).
- [ ] `tests/test_referee_guards.py` is green: the band-context version-string pin, the
      `desk_playbook_context.py` zero-diff source-hash pin, and the
      `docs/research-directions.md` catalog-reconciliation string-presence pins.
- [ ] Required-still-passing journey J-10 remains green (cockpit, `/structure`, every shipped
      `/desk` section — deterministic replay where a golden exists, else the LLM browser-qa
      fallback; the check must actually run, not be assumed from zero frontend diff).
- [ ] No anti-goal violation introduced: zero diff to `desk_playbook*.py`, `desk_forward.py`,
      `levels.py`, `tradability.py`, `setups.py`, `pnl_scan.py`; zero new `Config` fields;
      `Config().config_fingerprint()` still `08e471b10130e1e2`.
- [ ] Full backend suite green at ≥ 2,418 pass / 8 skip (the era-open floor recorded at
      iteration 0); no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-referee-iter-1-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-10 only (regression sentinel — cockpit `/`, `/structure` AAPL Load, every shipped
  `/desk` section; deterministic replay where a golden exists, else LLM browser-qa fallback).
  J-01 itself needs NO browser check — goal.md marks it `(Keyless; automated.)` and its
  acceptance runs entirely against committed pytest fixtures, not the browser-qa fixture-scoped
  rig.
- Unit/integration: new `tests/test_referee_guards.py` (spec-drift pin, zero-diff pin,
  catalog-reconciliation pins) and new hermetic fixture tests for
  `GET /research/desk/referee/evidence` (committed synthetic Playbook + strategy corpora,
  hand-computed expected counts, including the zero-corpus case) must exist and pass; the full
  existing suite must stay green at ≥ 2,418 pass / 8 skip.
- Error cases: zero Playbook records and/or zero strategy datasets on disk must serve an honest
  all-zero readiness shape at HTTP 200 (never 404/500, matching the desk router's established
  never-404-on-absence convention); a corrupted/unparseable store file must propagate the
  existing store's surfaced error, never be silently dropped.

Test-first contract:

- TC-1: given a committed hermetic fixture corpus of Playbook records spanning at least two
  distinct `(setup, side)` cells and at least two distinct `session_date` values, when
  `GET /research/desk/referee/evidence` is requested, then the response's
  `playbook_occurrence.per_setup_side` array contains one entry per fixture `(setup, side)`
  cell with `n` and `n_sessions` integers equal to the hand-computed fixture counts.
- TC-2: given the same fixture corpus, when `GET /research/desk/referee/evidence` is
  requested, then `playbook_occurrence.records`, `.distinct_sessions`, and
  `.signals_at_current_basis` are integers equal to the fixture's exact counts, and
  `.detector_basis` equals `sha256(canonical(playbook_parameters()))[:16]` computed via the
  formula pinned in `docs/goal.md` § Key Capabilities item 1.
- TC-3: given a committed hermetic strategy-family fixture (at least one dataset in each of the
  `train` and `holdout` splits, each with recorded trades), when
  `GET /research/desk/referee/evidence` is requested, then `strategy_trade.dataset_count`,
  `.per_split_counts.train`, `.per_split_counts.holdout`, and `.trade_count` are integers equal
  to the fixture's exact counts.
- TC-4: given the fixture's tick-derived dataset corpus is below the ~150 symbol-day Era-6 gate
  (`docs/research-directions.md`'s Card 5.2 figure — ~12 partial 2.5h windows on disk today),
  when `GET /research/desk/referee/evidence` is requested, then `strategy_trade.tick_gate_met`
  is `false`, `.tick_gate_statement` is a non-empty string naming the gate and the measured
  shortfall, and `.basis_caveats` contains a non-empty disclosure string naming the Card-6.4
  forming-bar admission in `levels._bars_as_of` (`epoch <= as_of`) — the first authoring of
  this exact sentence (see NOTES).
- TC-5: given a fixture-scoped store directory with zero Playbook records and zero strategy
  datasets on disk, when `GET /research/desk/referee/evidence` is requested, then the response
  is HTTP 200 (never 404 or 500) with `playbook_occurrence.records == 0`,
  `.per_setup_side == []`, `strategy_trade.dataset_count == 0`, and `.trade_count == 0`.
- TC-6: given `docs/playbook-detector-spec.md` as committed, when
  `tests/test_referee_guards.py`'s band-context version-string test runs, then it asserts §6's
  heading text and its `PLAYBOOK_CONTEXT_ALGORITHM_VERSION` constants line both contain the
  literal string `playbook-band-context-v3` matching `desk_playbook_context.
  PLAYBOOK_CONTEXT_ALGORITHM_VERSION`'s live value, and fails if either string diverges.
- TC-7: given `desk_playbook_context.py` as it exists at the start of this iteration, when
  `tests/test_referee_guards.py`'s zero-diff test runs after this iteration's changes land,
  then `hashlib.sha256(inspect.getsource(...)).hexdigest()` over the module (or its
  load-bearing functions, following `test_desk_playbook_guards.py::test_decline_disclosure_
  doc_edit_left_the_capitulation_code_byte_unchanged`'s precedent) equals the hash recorded at
  the start of this iteration, proving zero diff.
- TC-8: given `docs/research-directions.md` as committed, when
  `tests/test_referee_guards.py`'s catalog-reconciliation test runs, then it asserts string
  presence of the status-table rows for eras 5, 5B, 5C, 5D, B, and B2, plus the
  `"AMENDED 2026-08-14"` notes under Card 6.2 and Card 6.3, and fails if any string is removed
  or reworded.
- TC-9: given zero frontend files changed this iteration, when the required-still-passing
  check for J-10 runs, then the cockpit (`/`), `/structure`'s AAPL Load, and every shipped
  `/desk` section render with no new failure relative to the iteration-0 evidence baseline
  (`reports/qa/goal-referee-iter-0-evidence/`).
- TC-10: given this iteration's full diff, when `git diff --stat` is checked against the
  pre-iteration commit and `Config().config_fingerprint()` is evaluated, then the diff touches
  no file under `desk_playbook*.py`, `desk_forward.py`, `levels.py`, `tradability.py`,
  `setups.py`, or `pnl_scan.py`, `app/config.py` gains zero new fields, and the fingerprint
  still prints `08e471b10130e1e2`.
- TC-11: given this iteration's full backend test suite run, when `pytest` completes, then it
  reports pass and skip counts each ≥ the iteration-0 floor (2,418 pass / 8 skip) with zero
  errors.
- TC-12: given this iteration's implementation is complete, when the developer step finishes,
  then `docs/handoffs/goal-referee-iter-1-dev.md` exists and documents the endpoint's exact
  response shape, the fixture corpus location, and the two new guard-test pins.

## NOTES

- **Two different "fixture" words — do not conflate them.** J-01's own acceptance ("on the
  fixture rig") means committed hermetic pytest fixtures (synthetic corpora, per goal.md's
  Constraints: "Hermetic tests: keyless on committed fixtures") — TC-1 through TC-5 exercise
  these directly, no server needed beyond the test client. This is UNRELATED to the
  browser-qa fixture-scoped QA backend (`project-extensions/store-scope/`) that serves J-10's
  browser pass. `lessons.md`'s iter-0 entry (Applies to: any iteration scoring J-10 or reading
  `/desk` browser evidence) still holds for TC-9: read a near-empty `/desk` Playbook panel
  there as the rig's own seeded data, never as a regression.
- T-9 (clean `.next` rebuild before any browser pass) is a Constraint, but iteration 0's own
  evidence-lane note recorded it is safe to skip when zero frontend files changed (no
  stale-build risk exists). The same holds this iteration — J-01 is backend-only — so the
  browser-qa step for J-10 may skip the rebuild, consistent with that disclosed precedent.
- The Card-6.4 `basis_caveats` disclosure sentence has no pinned verbatim text anywhere in
  `docs/goal.md` or `docs/referee-statistical-spec.md` (only a description of what it must
  disclose) — this iteration authors it for the first time, subject to
  `tests/test_copy_discipline.py`. J-06 and J-08 must read this exact string back rather than
  minting a second version (single source of truth).
- No entry added to `runs/goal-session-referee/state/assumptions.md` this iteration —
  field-shape choices for a not-yet-pinned response envelope are routine spec-authorship, not
  a goal ambiguity requiring an owner ruling.
- `runs/goal-session-referee/state/blueprint.md` is unchanged this iteration: the Data Contract
  row this journey fulfills was already drafted at baseline with the correct owner and
  endpoint; nothing new to register, no nav change, so no
  `blueprint.reapproval-requested` file either.
- Anchors to re-locate by symbol name (grep), never by line arithmetic, per goal.md's Build
  anchors section: `playbook_parameters()` :246, `compute_playbook_input_signature` :345,
  `PlaybookStore.newest_for_date` :956, `PLAYBOOK_MIN_N_DISCLOSURE` :174 in
  `desk_playbook.py`; `PLAYBOOK_CONTEXT_ALGORITHM_VERSION` :131 in `desk_playbook_context.py`;
  dataset `(id, checksum, split)` identity in `store.py`/`datasets.py`.

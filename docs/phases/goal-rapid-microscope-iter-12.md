# Goal Iteration 12 — Close the vault's disclosure holes before real tape ever enters it

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** rapid-microscope
- **Iteration:** 12
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — r6 §7.8's `verify_chain()`-first retrofit is a shared-architecture change
  spanning `vault.py`'s whole predicate/mutator surface plus its `micro_snapshots.py` /
  `micro_readiness.py` / `routes.py` / `micro_routes.py` consumers; no single journey's own tests
  cover that cross-module interaction.
- Frontend Present: yes
- **Target journeys:** J-06, J-07, J-10
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05
- **Anti-goal reminders:**
  - No exploratory read of a sealed shard. Event data and outcome aggregates of a `sealed` shard
    are refused everywhere (routes, MCP, accessor, readiness) until its recorded exposure; the
    refusal is typed, tested, and fail-closed. *(critical)*
  - A recorded tranche is one opaque research pool until its shards are exposed. No served
    surface — readiness, recorder progress, datasets, backtests, PnL ledger, Scout, walk-forward,
    graduation, MCP, UI — may present a complete identity-labelled partition of "exploratory"
    versus "sealed", nor a complete per-shard list of EITHER side while any pool member is
    unexposed; the registered universe is public by construction, so a complete list of one side
    identifies the other by subtraction. Unexposed pool members stay mutually indistinguishable;
    identity becomes public only at real exposure or assignment. The governing test is the TR-2
    inference trap: given the registered universe plus every public artifact, no still-unexposed
    vault-eligible shard is identifiable with certainty. *(critical — spec r5)*
  - The denominator never shrinks. Every evaluated variant lands in the hash-chained ledger with a
    closed-vocabulary decision; kills are never deleted; the union-N across grid versions is
    served beside every family. *(critical)*
  - The 12 pre-existing tick symbol-days are permanently exploratory — never sealed, never
    `historical_oos`, never relabeled. *(critical)*
  - The vault secret never enters the repo, a log, a payload, or a screenshot — only its sha256
    commitment is ever recorded. *(critical)*
  - Single source of truth — each shared value is computed once, owned by one canonical endpoint,
    and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations.
    *(critical)*
  - Immutable data — registered datasets and bar series are append-only, checksummed, never
    re-tagged, never deleted, never content-perturbed. Splits are frozen at registration.
    *(critical)*

## GOAL

Make the vault's "opaque research pool" promise actually true by wiring the already-correct
`verify_chain()` primitive to fail closed everywhere, replacing the plain rule hash with a nonced
commitment that survives the two-GET subtraction attack even after every tracked shard is exposed,
and coarsening the recorder's live trade/quote counts — so the only three things still standing
between today's code and a safe real recording are built and attacked before any real tape is ever
sealed.

## BACKGROUND

The iteration-11 evaluator recommended `full` depth for this round explicitly (binding per this
iteration's dispatch); no escape condition is needed since the recommendation already asks for it,
but the scope independently earns Full trigger 1 on its own merits (see metadata). Its own
next-step list, in the order given, is this iteration's exact scope: (1) r6 §7.8 vault-ledger
integrity, fail closed on any `verify_chain()` failure (TR-25) — ruled 2026-08-18, unbuilt; (2) r7
§7.2 nonced rule commitment, hidden until whole-ORIGINAL-pool release (TR-27) — ruled 2026-08-19,
unbuilt, and it explicitly tightens the r5 gate a second door defeated (the vault's reveal check,
`vault._fully_exposed_universe_ids`, is ledger-row-only today); (3) r7 §7.1 coarse pre-release
trade/quote/byte volumes (TR-28) — same ruling, unbuilt, and the iteration-11 audit proved the
current exact `progress.trades_total`/`quotes_total` IS a withheld one-symbol-day shard's exact
count; (4) three cheap companions — case/format-normalize the symbol/date withhold match (today
`AAPL` vs `aapl` hides nothing), widen the existing TR-2 leak sweep's forbidden-substring check to
symbol/date strings (today it only checks dataset id and checksum), and restore J-07's regression
coverage (`state/golden-gaps` was deleted mid-iter-11 with no `journey-scripts/J-07.json` written
in its place, so its safety net silently disappeared). Two passenger evidence retakes ride along
(UT-04 landed on the Backscan panel instead of the readiness table; UT-09 came out blank) — no
round of their own, recaptured this time as part of this iteration's own browser pass (see TC-16).

Code inspection (this iteration) narrows and de-risks all four items materially. `verify_chain()`
(`micro_chain_ledger.py:121`) is already a correct, previously-audited primitive that distinguishes
a genuinely-empty ledger from a truncated one via its own durable tail anchor
(`chain_head.json`) — the gap is purely that nothing calls it as a gate; `build_vault_state`
currently only surfaces its verdict informationally (`vault.py:988-989`). The withhold choke point
is a single function (`vault.unresolved_pool_universe_by_dataset_id`, `vault.py:809`) with exactly
two authorized callers (`micro_snapshots._unresolved_pool_ids`, `micro_readiness.build_readiness`)
per iter-11's coherence audit, so gating it once reaches every existing consumer with no second call
site to add. The only surface that currently
serves an exact trade/quote volume total for withheld data is `tick_recorder.py`'s `_progress_view`
(`trades_total`/`quotes_total`, `tick_recorder.py:686-687`) — readiness's own `sealed_tranche`
aggregate (`micro_readiness.py:477-487`) never serves anything beyond shard/symbol-day counts, so
it needs no change here. The real `.data` store still has no `micro_vault` directory (re-confirmed
this iteration) and no registered universe, so every change below is provably inert against
production data — nothing re-keys, nothing regresses silently.

Applying the session's own hard-won lesson (iter-11's first lesson, and iter-9's before it):
widening one side of a paired mechanism re-opens the leak through the twin left narrow. This
iteration deliberately builds the RELEASE gate (`_fully_exposed_universe_ids` → whole-original-pool
awareness) in the SAME diff as the commitment scheme it protects, rather than shipping the nonce
alone and leaving the weaker ledger-row-only reveal gate to defeat it a third time — and item 2's
"whole pool released" predicate is required to be the ONE implementation the recorder's coarse-
bucket gate (item 3) also reads, never a second divergent check.

**Deliberate scope exclusion, per the priority rubric's "never bundle two risky journeys" rule.**
Three other ruled-but-unbuilt items are plannable per this iteration's carried context (r6 §8.1
`SEALED_PASS_RULE_V1`/TR-23, r6 §8.2 lineage confirmation boundary/TR-24, r6 §3 depletion revealing
quote/TR-26) but are NOT in this iteration's scope, matching the iteration-11 evaluator's own
priority list, which conspicuously omits all three. TR-23/TR-24 touch `micro_graduation.py` — J-07's
own module, a distinct risk area from vault/disclosure hardening, and TR-23 alone requires standing
up a new owner module (`micro_sealed_evaluation.py`) with a multi-step mandatory sequence. TR-26
touches `micro_observer.py`/`micro_features.py` — the currently-stable module every one of J-02
through J-05's snapshot data depends on — and additionally requires a new `grid_version` so
previously-excluded depletion candidates can return under corrected provenance. Bundling any of
these into the same diff as the vault/disclosure hardening below would violate "never bundle two
risky journeys" (a joint failure would be undiagnosable) and blow this iteration's size well past
what the session's own history says the auditor lane survives. Each is named explicitly in OUT OF
SCOPE below, reserved for its own iteration.

## IN SCOPE

### Backend

- [ ] `vault.py`: retrofit the shared `unresolved_pool_universe_by_dataset_id` choke point,
  `build_vault_state`, and the shard mutators (`seal_shard`/`assign_shard`/`expose_shard`) to call
  `verify_chain()` on both ledgers FIRST and fail closed with a typed refusal whenever either
  returns `{"ok": False, ...}` — no warn-and-continue path, no vault work proceeds on a corrupted
  ledger (spec §7.8).
- [ ] `vault.py`: a lawful-recovery primitive — halt, an immutable corruption record, byte-for-byte
  preservation of the corrupt ledger, identification of the last verified row, a hash-attested
  reconstruction of the missing suffix from caller-supplied trusted sources, completeness
  verification, and a new epoch/recovery ledger record naming every hash, source, operator identity
  and reason. A shard whose freshness the reconstruction cannot prove gets the new
  `exposure_unknown` state and is permanently ineligible for sealed-OOS use — never a
  truncate-and-continue (spec §7.8).
- [ ] `vault.py`: replace the plain `rule_hash` served pre-release with a nonced
  `rule_commitment = sha256(nonce ‖ canonical_rule)`; the nonce is generated at registration and
  held privately with the immutable universe row, never served until reveal (spec §7.2).
- [ ] `vault.py`: widen the reveal gate (`_fully_exposed_universe_ids`) from "every ledger-tracked
  shard exposed" to "every member of the universe's ORIGINAL registered pool released" — the same
  expected-pairs computation `unresolved_pool_universe_by_dataset_id` already uses — as the ONE
  "whole pool released" predicate the rule-reveal check and the recorder's volume-bucket gate below
  both read; never a second, divergent implementation of the same question (spec §7.2/§7.5).
- [ ] `tick_recorder.py`: `_progress_view`'s `trades_total`/`quotes_total` become a frozen,
  predeclared coarse-bucket scheme (a module constant, order-of-magnitude or power-of-two ranges)
  while the run's pool is unexposed, differencing-resistant (buckets never narrow within a run, and
  no before/after pair of responses may algebraically reconstruct a withheld exact count) (spec
  §7.1/§7.5).
- [ ] `vault.py` (`unresolved_pool_universe_by_dataset_id`'s universe-rule test): normalize the
  symbol/date comparison on BOTH the registered rule and the incoming record so a plan registered
  as `AAPL` still withholds a recording produced as `aapl`, and vice versa.
- [ ] `micro_routes.py`: map the new typed vault-ledger-corruption refusal to a clear, non-500 HTTP
  error on every route it can reach.
- [ ] `tests/test_vault.py`: widen the existing TR-2 leak sweep (Do-Not-Redo trap — do not touch its
  existing assertions, only add to them) so its forbidden-substring check also covers each
  still-withheld pair's symbol string and session-date string, not only dataset id/checksum.
- [ ] New/extended tests proving TR-25 (vault-ledger integrity), TR-27 (nonced rule commitment,
  including the dictionary-attack case), and TR-28 (coarse pre-release volumes, including the
  before/after differencing case) in the appropriate `apps/backend/tests/test_*.py` files.
- [ ] Restore J-07's regression coverage: write `journey-scripts/J-07.json` for its one servable
  surface (the `GET /research/desk/micro/graduation` honest empty-state), or, if a golden replay
  script is genuinely infeasible for this surface, restore an explicit non-silent disclosure to
  `state/golden-gaps` naming why — either way, the gap must not be silently absent again.

### Frontend

No new frontend code this iteration — the Validation Vault / Scout Ledger / Walk-Forward UI
sections remain J-08's unbuilt scope (confirmed again this iteration: zero occurrences of those
section names in `apps/frontend/app/desk/page.tsx`). The browser lane runs for **regression
verification only**: J-10's kept-surface sentinel walk (`/`, `/structure`, `/desk` including every
shipped section), J-01's Microscope Readiness re-check (its `sealed_tranche` aggregate is served by
code this iteration touches), and two evidence retakes carried from iteration 11 (UT-04, UT-09).
See TESTING REQUIREMENTS.

### New user-facing capability

None — this iteration hardens data already withheld from the UI; no new control, page, or section.

### New information displayed

None. The affected fields (`rule_commitment`, the coarse volume buckets) are API/MCP-only today;
their eventual UI rendering is J-08's unbuilt scope.

### New user actions

None.

### UI surface changes

None.

### Product surface delta

None visible — this is hardening beneath already-shipped surfaces. The only change in what the
product can honestly claim is that the vault's hiding promise becomes actually true rather than
defeatable by a two-GET subtraction or a live progress poll.

### Blueprint conformance

No new pages, routes, or nav entries. This iteration edits `blueprint.md`'s Data Contract only —
additive sub-field rows under the already-registered "Vault shards, universes, exposure ledger" and
"Recorder job + tranche progress/runs" rows (both already live under the Desk → Rapid Microscope
Information-Architecture home). No nav-skeleton change; no `blueprint.reapproval-requested` file.

### Data-contract additions

- `rule_commitment: str` (64-hex-char `sha256(nonce ‖ canonical_rule)`) — owner `vault.py`
  (`register_universe`, `_serialize_universe`), served by the already-registered
  `GET /research/desk/micro/vault`. Supersedes the plain `rule_hash` at the committed (pre-reveal)
  stage; `rule_hash`/`compute_rule_hash` stays as the ledger's own internal identity function.
- `commitment_nonce: str` (high-entropy hex, served ONLY once a universe's whole ORIGINAL pool is
  released) — same owner, same endpoint, sub-field of the revealed-stage projection alongside the
  already-served `symbol_rule`/`date_rule`.
- `progress.trades_total_bucket: str` / `progress.quotes_total_bucket: str` (a frozen, predeclared
  coarse label such as `"1M-10M"`, never a rounded number) — owner `tick_recorder.py`
  (`TickRecorderComputeManager`), served by the already-registered
  `GET /research/desk/micro/recorder/compute`. Supersede the iteration-11-registered exact
  `progress.trades_total`/`progress.quotes_total` at THIS surface while the run's pool is unexposed;
  the exact int fields stay valid only after whole-pool release, a state this surface cannot reach
  before its own recording finishes.
- `exposure_state` value-space extension: gains the legal value `exposure_unknown` beside the
  already-registered `sealed`/`assigned`/`exposed` — same owner (`vault.py`), same endpoint, no new
  row; a shard an unverifiable ledger recovery could not prove fresh.
- The `verify_chain()`-first fail-closed behaviour itself introduces no displayed value (a refusal
  behaviour, not a served field) and needs no Data Contract row.

## OUT OF SCOPE

- **J-06 step 4** (the credentialed real Alpaca starter tranche). Stays closed until TR-25, TR-27,
  TR-28, and the symbol/date normalization are all built and green — no real vendor call, no write
  to the operator's real `.data/datasets` store this iteration.
- **TR-23 (r6 §8.1 `SEALED_PASS_RULE_V1` + new `micro_sealed_evaluation.py`)** and **TR-24 (r6 §8.2
  lineage-wide `proposed_confirmation_boundary`)** — both ruled and plannable, but deliberately
  deferred to their own iteration (see BACKGROUND): they touch `micro_graduation.py`, a distinct
  risk area from this iteration's vault/disclosure work, and TR-23 alone requires a new owner
  module with a multi-step mandatory sequence.
- **TR-26 (r6 §3 `quote_depletion` revealing-quote fix + new `grid_version`)** — ruled and
  plannable, deliberately deferred: it touches `micro_observer.py`/`micro_features.py`, the
  currently-stable snapshot module every passing journey J-02 through J-05 depends on, a third
  distinct risk area.
- **The "exposed for exploratory use" release mechanism** (iteration-11's own deferred item,
  unchanged this iteration) — still not specified anywhere in `docs/rapid-validation-spec.md`
  §7.1-§7.7; not invented here (T-1). J-06 step 4 stays closed regardless, so nothing needs it yet.
- **Wiring `tick_recorder._finalize_day`/`run_tick_recording` to call
  `vault.seal_shard`/`assign_shard`/`expose_shard` directly.** Not required for this iteration's
  fixes (the universe-rule-driven predicate already closes the withholding hole without it) and not
  built.
- **J-08** (the four new `/desk` sections + four new read-only MCP tools) and **J-09** (the pilot
  studies, which render through J-08's panels) — the natural next iteration after this one, per the
  iteration-11 evaluator's own sequencing.
- **Editing the historical `docs/phases/goal-rapid-microscope-iter-11.md` phase spec.** That file
  is a point-in-time record of what iteration 11 planned; rewriting it after the fact would falsify
  history. The actual fix is procedural — this spec (see BACKGROUND) does not inherit its stale
  "open owner question" framing, and `docs/rapid-validation-spec.md` itself already documents the
  staleness in r7's own revision note (line 111). No live document currently repeats the stale
  claim (checked by grep this iteration).

## DEFINITION OF DONE

- [ ] TR-25 (vault-ledger integrity), TR-27 (nonced rule commitment), and TR-28 (coarse pre-release
  volumes) all pass, joining TR-2 (widened) as green — J-06 step 3's remaining hardening lands.
- [ ] Symbol/date matching is normalized on both the registered universe rule and incoming records.
- [ ] J-07's regression coverage is restored (a golden replay script or an explicit, non-silent
  `state/golden-gaps` disclosure exists on disk) and J-07 is freshly re-verified this iteration
  (not carried/deferred).
- [ ] The era's trap-suite count reaches 23 of 28 (TR-3, TR-22, TR-23, TR-24, TR-26 remain the only
  ones still missing, each named by ID in OUT OF SCOPE above).
- [ ] Required-still-passing journeys J-01 through J-05 remain green (deterministic replay, with
  the LLM browser-qa lane as fallback where a golden script is absent).
- [ ] No anti-goal violation introduced; the three OPEN-minor anti-goal items the iteration-11
  evaluator listed (vault ledger integrity; the "one opaque research pool" item's two remaining
  named gaps; symbol/date matching fails open) close.
- [ ] Unit tests pass; full suite count is at or above the iteration-11 baseline (3192 collected /
  3184 passed / 8 skipped / 0 failed) with 0 regressions.
- [ ] The real `.data` store stays byte-unchanged (still 18 datasets, still no `micro_vault`
  directory) — no vendor call, no real recording act this iteration.
- [ ] `Config().config_fingerprint()` still prints `08e471b10130e1e2`; all six `referee_*.py`
  SHA-256 hashes are unchanged from iteration 0; the MCP tool count stays the 22-tuple.
- [ ] Dev handoff written at `docs/handoffs/goal-rapid-microscope-iter-12-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-10 (kept-surface sentinel — `/`, `/structure`, `/desk` including every shipped
  section, browser-verified via the store-scoped rig); J-01 (Microscope Readiness section
  re-check). Two evidence retakes carried from iteration 11: UT-04 (readiness table — landed on the
  wrong panel last round) and UT-09 (whole-product safety walk — came out blank last round). J-06
  and J-07 have no NEW browser acceptance this iteration (J-06's own UI section ships at J-08; J-07's
  servable surface is the existing empty-state screenshot, restored per TC-15 below).
- Unit/integration: every Backend IN SCOPE item above, plus the TC- scenarios below.
- Error cases: a corrupted/truncated/mutated vault ledger (either the shard ledger or the universe
  ledger) must fail closed, never silently proceed; a dictionary-guessed rule must never verify
  against a served `rule_commitment` without its nonce; a withheld one-symbol-day run must never
  leak its exact trade, quote, or byte count through any surface.

Test-first contract:

- TC-1: given a vault shard ledger whose tail was truncated after being written, when any
  vault/exposure predicate runs (e.g. `unresolved_pool_universe_by_dataset_id`, `build_vault_state`),
  then it raises a typed refusal instead of returning a result, and no shard is reported as "never
  exposed".
- TC-2: given a vault ledger with one interior row's bytes mutated after append, when the
  `verify_chain()`-gated predicates run, then they raise the same typed refusal and halt all vault
  work — no sealing, no assignment, no exposure check, no sealed evaluation.
- TC-3: given a corrupted ledger replaced with a last-known-good prefix while a separately-committed
  tail-anchor checkpoint proves more rows existed, when a predicate runs, then it still fails closed
  rather than treating the truncated prefix as complete.
- TC-4: given a corrupted ledger's missing suffix is reconstructed from hash-attested trusted
  sources and verified complete, when the new recovery epoch record is written, then vault
  predicates resume and report the exact prior exposure state.
- TC-5: given a reconstruction whose completeness cannot be proven, when recovery is attempted, then
  every shard whose freshness could be affected is marked `exposure_unknown` and stays permanently
  ineligible for sealed-OOS use.
- TC-6: given a universe with every ledger-tracked shard exposed but at least one untracked
  ORIGINAL-pool member still unresolved, when `GET /research/desk/micro/vault` is called, then
  `symbol_rule`/`date_rule` for that universe stay hidden and only `rule_commitment` is served.
- TC-7: given every member of a universe's ORIGINAL registered pool is released, when
  `GET /research/desk/micro/vault` is called, then `symbol_rule`, `date_rule`, and
  `commitment_nonce` are all served, and recomputing `sha256(nonce ‖ canonical_rule)` equals the
  originally registered `rule_commitment` exactly.
- TC-8: given the served `rule_commitment` of a still-withheld universe, when a dictionary attack
  recomputes `sha256` over plausible rule guesses without the nonce, then no guess verifies against
  the commitment.
- TC-9: given a one-symbol-day recorder run whose pool is unexposed, when
  `GET /research/desk/micro/recorder/compute` is polled during and after the run, then no exact
  trade count, quote count, or byte count appears anywhere in the response — only a predeclared
  coarse bucket label.
- TC-10: given a multi-shard pool recording, when the recorder progress is queried before and after
  one shard's exposure, then the before/after pair cannot be combined to solve any remaining
  withheld count exactly, and the served bucket never narrows as the pool shrinks.
- TC-11: given the final ORIGINAL-pool member is released, when the recorder/readiness volume
  surfaces are queried, then exact trade/quote/byte totals may be served again.
- TC-12: given a universe registered with a lowercase `symbol_rule` entry and a recording later
  produced under the vendor-canonical uppercase symbol, when the withhold predicate evaluates that
  dataset, then the dataset id appears in the predicate's withheld-set result (the same outcome an
  exact-case match would produce).
- TC-13: given the reverse case (uppercase-registered rule, lowercase-produced recording), when the
  predicate evaluates it, then the dataset id appears in the withheld-set result too — the same
  outcome as TC-12, from the other direction.
- TC-14: given a registered pool with untracked members, when the widened TR-2 leak sweep runs
  across every registered route, the recorder progress path, and the `datasets` MCP tool, then no
  still-withheld member's symbol string or session-date string (in addition to its dataset id and
  raw checksum) appears anywhere in the swept response union.
- TC-15: given J-07's single servable surface (`GET /research/desk/micro/graduation`'s honest empty
  state), when the browser-qa lane runs this iteration, then a fresh element-captured screenshot is
  recorded, and either `journey-scripts/J-07.json` or an explicit `state/golden-gaps` disclosure
  exists on disk afterward.
- TC-16: given the Microscope Readiness section and the whole-product kept-surface walk, when the
  browser-qa lane captures evidence this iteration, then the UT-04 image shows the readiness table
  itself (not the Backscan panel) and the UT-09 image shows the rendered sentinel walk (not a blank
  image).
- TC-17: given the frozen rails and the full backend suite, when the developer, reviewer, QA, and
  auditor each run their own checks this iteration, then the suite count is at or above 3192
  collected / 3184 passed / 8 skipped / 0 failed with 0 regressions, `Config().config_fingerprint()`
  still prints `08e471b10130e1e2`, all six `referee_*.py` hashes are unchanged, and the real
  `.data/datasets` store stays byte-identical (18 datasets, still no `micro_vault` directory).
- TC-18: given the extended trap suite runs in CI, when the auditor counts TR-IDs present under
  `apps/backend/tests/`, then TR-25, TR-27, and TR-28 are all present and green, bringing the era's
  trap-suite count to 23 of 28.
- TC-19: given J-01 through J-05's stored golden replay scripts (or the LLM browser-qa fallback
  where one is absent), when they replay against this iteration's code, then all five remain
  `passing` with zero regressions.
- TC-20: given the iteration-11 evaluator's anti-goal table listed "vault ledger integrity", "one
  opaque research pool" (its two named r7 gaps), and "symbol/date matching fails open" as OPEN minor
  items, when this iteration's evaluator re-checks the same table, then all three read OK and no new
  critical item opens.
- TC-21: given the iteration completes, when `docs/handoffs/goal-rapid-microscope-iter-12-dev.md` is
  checked, then it exists on disk.

## NOTES

- **Implementation freedom, not a spec reading.** Recording strictly precedes any possible exposure
  in the one-way `sealed → assigned → exposed` lifecycle (nothing in production calls
  `seal_shard`/`assign_shard`/`expose_shard` today), so an implementation that ALWAYS buckets
  `tick_recorder.py`'s live/just-finished progress volumes (never conditionally exact) is
  provably spec-compliant without threading per-universe vault state through the recorder. This is
  offered as a scope-reducing option, not a mandate — TC-9/TC-10/TC-11 are outcome-based and pass
  either way; if a per-universe check is cheap given item 2's shared "whole pool released"
  predicate, that is equally acceptable.
- **Lesson applied (iter-11, first entry):** "widening one side of a paired mechanism re-opens the
  leak through the twin you left narrow." This spec deliberately pairs the nonced-commitment build
  (item 2) with the reveal-gate widening it depends on in the SAME diff, rather than shipping the
  nonce alone against the still-ledger-row-only gate a third time.
- **Lesson applied (iter-11, second entry):** stale "open owner question" framing must not be
  carried forward. Checked by grep this iteration — no live document (goal.md, rapid-validation-spec.md,
  blueprint.md, iteration-state.md) repeats it; only the historical iteration-11 phase spec does,
  and that file is not touched (see OUT OF SCOPE).
- If the developer finds any of the four numbered items genuinely ambiguous against
  `docs/rapid-validation-spec.md`'s text, the project's own rule applies: drop the procedure,
  disclose it, and surface it for an owner ruling rather than improvise (T-1) — do not repeat the
  iteration-10 pattern where an unspecified TC pressure produced an invented rule.

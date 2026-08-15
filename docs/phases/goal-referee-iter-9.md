# Goal Iteration 9 — The promotion interlock: no certificate, no champion move

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** referee
- **Iteration:** 9
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — Structural/cross-cutting: this iteration rewires `pnl_scan.py`'s frozen
  `_promote` gate to consult a certificate minted through a NEW path threaded across
  `referee_adjudicate.py` (the evaluation rail's certificate mint site), `referee_registry.py`
  (the `CertificateStore` writer), and `pnl_scan.py` itself (`_promote`/`run_sweep`'s signature
  and report shape) — plus inverts `test_pnl_scan.py`'s existing promotion-path assertions. The
  interaction between brand-new statistical machinery and an already-shipped, already-tested
  production gate is not covered by any single existing journey's tests.
- **Frontend Present:** yes
- **Target journeys:** J-08
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-10
- **Anti-goal reminders:**
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five
    states and thresholds, the frozen structure computations, the JSON `BarStore`, and every
    KEPT surface's behaviour stay byte-identical. New work is additive and versioned beside
    them, never a mutation of them. *(critical)*
  - **Hold-out-only promotion** — The champion pointer moves only on a genuine hold-out
    survival through the sweep gate PLUS a valid Referee certificate (this era makes the
    "era-6 statistical gates" clause real). Train-only wins are labeled overfit. Never lower a
    minimum sample size, widen a gate, or pool across feeds/fingerprints to manufacture a
    survivor. *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*
  - **The Referee never feeds back.** No referee output gates, filters, ranks, or tunes any
    detector, context, screen, or strategy computation (import-ban + source-scan guard-tested);
    the frozen research vocabulary stays frozen. *(critical)*
  - **Promotion is certificate-locked.** No champion promotion without a valid
    candidate-specific Referee certificate; no bypass flag, env override, or default-allow
    path exists (source-scan guard-tested); a Playbook certificate can never satisfy a
    strategy promotion. *(critical)*
  - **No confirmatory output without a verified oracle attestation.** The adjudication fold
    never serves a confirmatory verdict from an evaluation whose attestation is missing,
    mismatched, or version-stale — it serves the refusal state with its reason; descriptive
    output never masquerades as confirmatory. *(critical)*
  - **No profit claims and no advice** — every $ figure is a simulated measurement carrying R,
    n, fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language,
    no imperative trading cues. *(critical)*
  - **Never shrink the BH denominator.** No BH pass may run with m smaller than the family's
    registered planned count; no candidate joins a family retroactively; no unevaluated or
    late-withdrawn candidate is dropped from m — they fold as p=1, never disappear; no family's
    q changes after registration. *(critical)*

## GOAL

No strategy candidate can be promoted to champion — however strong its hold-out numbers —
unless a valid, candidate-specific Referee certificate exists on file: `pnl_scan` refuses closed
with a distinct, honest reason when the certificate is missing, stale, mismatched, or failed, and
the strategy family gets its own first real adjudication through the identical statistical rail
the Playbook family already uses.

## BACKGROUND

Per the priority rubric: no journey regressed (rule 1); the last coherence verdict
(`iter-8/coherence.md`) was `COHERENCE-WARN`, not FAIL, so no mandatory consolidation pass is
owed (rule 2) — its one open advisory (F1, the unowned `family_q` browser literal) is folded in
as a rider below, not escalated into its own round; J-08 is goal.md's own next dependency-order
journey and the evaluator's explicit, unambiguous pick (rule 3 — the only candidate journey with
no competing claim); it is targeted ALONE (rule 6) because it is the riskiest remaining journey —
it fails closed on the era's one production-mutating surface, `pnl_scan._promote`, with no bypass
of any kind, and inverts tests that currently allow promotion.

**Depth is full per the evaluator's own binding recommendation** (`iter-8/eval.md`: "Full depth
is not a preference here: the round rewrites existing tests that today allow promotion, and the
deeper checking lane has now found a real fault in all three of the rounds it actually ran.");
independently, Trigger 1 (structural/cross-cutting, cited above) holds on its own merits — this
touches `pnl_scan.py`, `referee_adjudicate.py`, and `referee_registry.py` in one interlocking
change, not a single-module addition. Iterations 6 and 7 were both planned as the deep pass and
iteration 7 was demoted to lean by a wall-clock budget breach, both times shipping with a real
fault the deferred hard-audit later caught; the evaluator flagged that pattern explicitly and
asked that it not recur here. This iteration keeps its own NEW surface area to exactly what
goal.md's J-08 steps 1–4 require, plus four already-diagnosed, already-scoped riders the
evaluator asked to ride along rather than become their own rounds — not because the work is
small, but because widening it further would repeat the same time-pressure risk.

**Lessons applied** (`state/lessons.md`): iter-8's lesson — a served number with a subtraction,
floor, or saturation point must be hand-checked against REAL-corpus magnitudes, not just the
fixture rig — applies directly to the strategy-family Δ_d computation and the certificate's
`gate_results` (calibrated p, CI, floors): hand-verify the `insufficient_sample` arithmetic
against today's real corpus (champion holdout n=1 < `promotion_min_sample_size`=5), not only a
fixture built past the floor. iter-6's lesson — a guard on one field is worthless if a sibling
field reaches the same derived value another way — applies to `authorize_promotion`'s "stale"
comparison: confirm every live-scan-context field a certificate pin is derived from
(`champion_identity`, `config_fingerprint`, `gate_version`, `referee_parameters_hash`,
`train_dataset`, `holdout_dataset`) is actually compared, not only the ones already coded.
iter-3/iter-4's lessons on oracle/property-test branch coverage apply only if the strategy-family
pooling needs any new `referee_stats.py` code path — the design goal is ZERO new code there
(pure reuse of the existing cluster-agnostic primitives), so if that goal cannot be met, the drop
must be recorded (T-1), not silently worked around.

## IN SCOPE

### Backend
- [ ] `referee_adjudicate.py`: a strategy-family evaluation branch (spec §3.7) — pools each
  candidate's `strategy_trade` observations against their recorded `random_null` trades PER
  DATASET cluster (`Δ_d = mean(candidate net_r in d) − mean(random_null net_r in d)`), reusing
  `referee_stats.py`'s existing permutation/bootstrap/BH primitives verbatim (never a second
  implementation) and the SAME floors/attestation/role/snapshot machinery already built for the
  playbook estimands.
- [ ] `referee_stats.py` / cross-module: the `referee_parameters()` aggregator spec §1 names —
  combines every referee module's existing `_parameters()` stub (stats, null specs, test spec)
  plus `REFEREE_GATE_VERSION` into one dict, hashed once, read at call time (Parameters
  discipline; a monkeypatched constant must move both the dict and the hash).
- [ ] `referee_registry.py`'s `CertificateStore`: the real MINT call site — at a strategy-family
  hypothesis's attested, gate-passing confirmatory checkpoint, append ONE certificate record
  (spec §8 shape) — reachable only through the real evaluation rail, never a hand-written or
  fixture path in production code.
- [ ] `pnl_scan.py`'s `_promote`/`run_sweep`: thread the live scan's own `live_scan_context`
  (champion identity, train/holdout dataset pins, config fingerprint, gate version, parameters
  hash) and a `CertificateStore` handle through; consult `authorize_promotion` BEFORE the
  ledger-row write (ledger-row-first / pointer-second order unchanged after authorization); on
  refusal, write nothing and surface the refusal class/reason in the report's `promotion` block.
- [ ] `pnl_scan.py`'s report: the `promotion` block distinguishes `candidates[i].survivor: true`
  (unchanged meaning) from its own new `promotion_eligible`/`refusal_class`/`reason` fields; a
  non-promoting sweep's report stays byte-compatible outside these new fields.
- [ ] Invert `tests/test_pnl_scan.py`'s promotion-path assertions per goal.md J-08 Step 4
  (refusal-without-certificate assertions plus new promotion-with-fixture-certificate
  assertions; suite grows, never shrinks) and extend the no-bypass source-scan guard test to
  cover the interlock (no `--force`/skip flag/env override/default-allow path).
- [ ] Rider (discovery/accrual context fix): apply the SAME `context_predicate`/backing-bucket
  check `_starter_context_readiness` already uses to BOTH `_hypothesis_accrual` and
  `_hypothesis_discovery`'s pooling walk, via one shared helper (not a second implementation),
  so a context-based (B/C) hypothesis's registry-row numbers agree with its own shortlist row's
  live readiness for the identical cell.
- [ ] Rider (S-4 short side): add `range_trade:short at_wall` (estimand B) as a sixth
  `REFEREE_STARTER_FAMILY_SHORTLIST` module constant, reusing `_starter_context_readiness`
  verbatim — spec §7's own "(registered per side)" wording for S-4 (see
  `state/assumptions.md` iter-9 entry).
- [ ] Rider (family_q ownership): a `REFEREE_DEFAULT_Q = 0.10` module constant in
  `referee_registry.py` (spec §1's own pinned value); `shortlist_response()` serves it plus the
  existing `REFEREE_STARTER_FAMILY_ID` value as new top-level `family_id`/`family_q` fields.
- [ ] Rider (UI guard): extend `tests/test_desk_ui_guards.py`'s `_PRICE_ARITHMETIC_FIELDS` to
  `hyp.accrual.*` (mirroring the existing `hyp.discovery.*` entry) with its seeded counter-test.

### Frontend
- [ ] `apps/frontend/app/desk/page.tsx`: read `family_id`/`family_q` from the fetched shortlist
  response instead of the local `REFEREE_STARTER_FAMILY_ID`/`REFEREE_STARTER_FAMILY_Q` literals
  in the registration POST body; remove the two now-dead local constants. `lib/types.ts` gains
  the two fields on the shortlist response type. No rendered value changes — the submitted
  numbers are identical to today's.

### New user-facing capability
None from J-08 itself — it is backend-only this era (goal.md's own "(Keyless; automated.)"
framing); its outcome is visible only in the `pnl_scan` CLI sweep report's `promotion` block,
which has no `/desk` UI home (per `blueprint.md`'s existing J-08 Information-Architecture row).
The already-shipped Referee Registry shortlist table gains a sixth selectable candidate purely
from the S-4-short rider, rendered by the EXISTING generic `candidates.map()` — zero JSX change
for that row.

### New information displayed
The sixth shortlist candidate row (`range_trade:short at_wall`, estimand B) with the identical
field shape as its five siblings. Nothing else new is rendered anywhere.

### New user actions
None new in the browser (the existing select-and-confirm registration flow now has one more
selectable candidate). The strategy-family promotion interlock is exercised only by the existing
`run_sweep` CLI act — no new user action.

### UI surface changes
None. No new section, no new JSX branch; the `family_id`/`family_q` literal-to-field swap does
not change any rendered class, element, or copy.

### Product surface delta
The champion promotion pointer becomes provably certificate-locked: a genuine hold-out survivor
that would have promoted before this iteration is refused, honestly and specifically, when no
matching Referee certificate exists — visible in the `pnl_scan` CLI report, not yet on `/desk`
(J-09's job). The strategy family receives its first real statistical adjudication.

### Blueprint conformance
No new route, no new Information-Architecture entry. J-08's own machinery keeps the "no new
page" home `blueprint.md` already registers for it. The sixth shortlist candidate lives under
the already-registered J-07 home (`/desk` → Referee Registry).

### Data-contract additions
1. **`promotion` block** (already-registered "Promotion authorization verdict" row; owner
   `referee_adjudicate.py`'s `authorize_promotion`; endpoint unchanged — surfaced inside
   `pnl_scan._promote` / the scan report's `promotion` block) gains three fields alongside its
   existing `candidate_id: str` / `promoted: bool` / `note: str|None` / `enhancement_id:
   str|None`: `promotion_eligible: bool`, `refusal_class: "no_certificate"|"stale"|
   "wrong_candidate"|"mismatched_datasets"|"failed_gates"|"malformed_unverifiable"|None`,
   `reason: str|None`.
2. **Certificate record** — shape unchanged from the iter-6 `blueprint.md` registration
   (`candidate: {strategy_id, profile}`, `champion_identity_at_scan_time: dict`, `train_dataset:
   {id, checksum, split}`, `holdout_dataset: {id, checksum, split}`, `config_fingerprint: str`,
   `gate_version: str`, `referee_parameters_hash: str`, `family_id: str`, `hypothesis_id: str`,
   `gate_results: {calibrated_p: float, bh_pass: bool, ci: [float, float], floors_met: bool}`);
   this iteration adds its WRITER (mint-only-through-the-real-rail).
3. **`shortlist_response()`** (already-registered endpoint `GET
   /research/desk/referee/registry/shortlist`) gains two new top-level fields: `family_id: str`
   and `family_q: float` (`0 < family_q <= 1`).
4. **`REFEREE_STARTER_FAMILY_SHORTLIST`** gains one more `candidates` array entry (identical
   shape to S-1..S-5, no new field): `range_trade:short at_wall`, estimand B.
5. **Registry row's `accrual`/`discovery` blocks** — no new field, a correctness fix: for a B/C
   hypothesis, both now filter by the hypothesis's own `context_predicate`, matching the
   shortlist row's live readiness for the identical cell.
6. **Evaluation record** (already-registered row) — no new field; its already-declared
   `evidence_family: "playbook"|"strategy"` enum gets a real `"strategy"` branch for the first
   time.

All six are registered in `runs/goal-session-referee/state/blueprint.md`'s iter-9 note as of
this spec-writing pass.

## OUT OF SCOPE

- J-09 (the `/desk` Referee Adjudications / Referee Runs sections, MCP contract v5) — a separate
  journey, not touched this iteration; MCP tool count stays 20.
- Any change to `desk_forward.py`, `desk_playbook*.py`, `levels.py`, `tradability.py`,
  `backtests.py`'s trade-construction logic, or `app/config.py` — frozen this whole era.
- Rendering the `promotion` block anywhere on `/desk` — no UI home is registered for it this
  era; it stays CLI/report-only.
- Actually registering or evaluating a REAL strategy-family hypothesis against the operator's
  real corpus — fixture-only this iteration (goal.md: "no strategy certificate can honestly
  exist this era"). Do not fabricate one to satisfy DEFINITION OF DONE.
- Any change to `referee_stats.py`'s core statistical primitives — pure reuse (Read-side law;
  no second implementation of the measurement/testing rail).
- Any edit to the five already-shipped shortlist candidates' (S-1..S-3, S-5) own definitions —
  only the S-4 sibling is ADDED; nothing existing changes.
- Card 6.4 forming-bar fix, any new detector/setup/alpha dimension, any new vendor or runtime
  dependency — explicit Non-Goals of `docs/goal.md`.
- New `Config` fields — zero expected; the fingerprint pin `08e471b10130e1e2` must not move.

## DEFINITION OF DONE

- [ ] J-08 passes (pytest; `(Keyless; automated.)` per goal.md): a fixture survivor is refused
  (no ledger row, no pointer move) absent a valid certificate; the same candidate promotes when
  a fixture certificate minted through the real evaluation rail matches every pin; each of the
  six refusal classes (`no_certificate`, `stale`, `wrong_candidate`, `mismatched_datasets`,
  `failed_gates`, `malformed_unverifiable`) is separately fixture-tested through the full
  `run_sweep`/`_promote` path; a non-promoting sweep's report is byte-compatible except the new
  `promotion` fields; the no-bypass source scan is green; the strategy-family adapter serves
  `insufficient_sample` with its `basis_caveats` and null-design disclosure at today's real
  corpus.
- [ ] Required-still-passing journeys J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-10 remain green
  (deterministic replay + LLM fallback, mechanically verified at both depths).
- [ ] No anti-goal violation introduced: no bypass flag/env override/default-allow path exists
  anywhere in the interlock (source-scan guard-tested); a Playbook-origin hypothesis can never
  mint or satisfy a strategy certificate; `pnl_scan.py`'s non-promotion-path behavior stays
  byte-compatible; zero new `Config` fields; fingerprint pin unchanged.
- [ ] Riders verified: registry `accrual`/`discovery` agree with the shortlist's live readiness
  for context-based (B/C) candidates; the S-4 short-side candidate is served; `shortlist_
  response()` serves `family_id`/`family_q` and `page.tsx` reads both from the response;
  `_PRICE_ARITHMETIC_FIELDS` covers `hyp.accrual.*`.
- [ ] Unit tests pass; suite collected count >= 2,657, 0 failed; no regressions.
- [ ] `Config().config_fingerprint()` prints `08e471b10130e1e2`; MCP tool count stays 20.
- [ ] Dev handoff written at `docs/handoffs/goal-referee-iter-9-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-10 (kept-product golden-replay walk, continuous per goal.md's "J-10 guarding
  continuously"); J-07 (regression smoke re-check after the `family_id`/`family_q` source-swap
  and the sixth shortlist row — no new acceptance, confirm unchanged rendering, screenshot).
- Unit/integration: `authorize_promotion` wired end-to-end through `_promote`/`run_sweep` for
  all six refusal classes plus the authorized path; the certificate mint call site (fixture
  strategy hypothesis reaching an attested, gate-passing checkpoint); the strategy-family Δ_d
  pooling (dataset-clustered, reusing `referee_stats.py` verbatim); `referee_parameters()`'s
  aggregation + hash stability + monkeypatch-moves-the-hash counter-test; the accrual/discovery
  context-predicate fix; the S-4 short-side candidate's readiness; `shortlist_response()`'s new
  fields; the no-bypass source scan; `test_pnl_scan.py`'s inverted promotion-path assertions.
- Error cases: a malformed/corrupted certificate file must return `malformed_unverifiable`,
  never crash `_promote`; a survivor with zero certificates on file must still complete the
  sweep and report honestly (never raise); an unattested or version-stale strategy-family
  evaluation must never mint a certificate.

Test-first contract: every DEFINITION OF DONE checkbox and every Data-contract addition above
maps to at least one concrete scenario line below.

- TC-1: given a fixture strategy candidate that reaches survivor status (train positive, holdout
  positive, holdout `candidate_n >= promotion_min_sample_size`) and zero certificates exist for
  its `(strategy_id, profile)`, when `run_sweep` executes, then `_promote` appends no PnL-ledger
  row, the champion pointer is unchanged, and the report's `promotion` block reads
  `promotion_eligible: false, refusal_class: "no_certificate"` while `candidates[i].survivor`
  still reads `true`.
- TC-2: given the same fixture candidate and a certificate minted through the real evaluation
  rail whose `candidate`, `champion_identity_at_scan_time`, `train_dataset`, `holdout_dataset`,
  `config_fingerprint`, `gate_version`, `referee_parameters_hash`, and `gate_results.{bh_pass,
  floors_met}` all equal the live scan's own values, when `run_sweep` executes, then `_promote`
  appends exactly one PnL-ledger row, moves the champion pointer, and the report's `promotion`
  block reads `promoted: true, promotion_eligible: true`.
- TC-3: given a certificate whose `config_fingerprint` differs from the live scan's own value,
  when `run_sweep` reaches a survivor with that certificate on file, then no ledger row is
  written, no pointer moves, and `promotion.refusal_class` reads `"stale"`.
- TC-4: given a certificate recorded for a different `profile` than the live survivor's, when
  `run_sweep` reaches that survivor, then `promotion.refusal_class` reads `"wrong_candidate"`
  and nothing is written.
- TC-5: given a certificate whose `train_dataset` or `holdout_dataset` pin differs from the live
  scan's datasets, when `run_sweep` reaches the matching survivor, then `promotion.refusal_class`
  reads `"mismatched_datasets"` and nothing is written.
- TC-6: given a certificate whose `gate_results.bh_pass` or `gate_results.floors_met` is not
  `true`, when `run_sweep` reaches the matching survivor, then `promotion.refusal_class` reads
  `"failed_gates"` and nothing is written.
- TC-7: given a certificate store reporting an unparseable certificate file, when `run_sweep`
  reaches a survivor, then `promotion.refusal_class` reads `"malformed_unverifiable"` and
  nothing is written.
- TC-8: given the source tree, when the extended no-bypass guard test scans `pnl_scan.py` and
  `referee_adjudicate.py`, then it asserts no `--force`/skip flag, environment override, or
  default-allow code path can satisfy `authorize_promotion`.
- TC-9: given a strategy-family hypothesis registered against a recorded backtest dataset's
  trades and its recorded `random_null` trades, when an evaluation runs through the strategy
  branch, then the record's `evidence_family` reads `"strategy"`, groups observations by
  `cluster_key` = dataset id (never session date), and reuses `referee_stats.py`'s
  permutation/BH primitives with zero diff to that module.
- TC-10: given today's real corpus (champion holdout n=1 `< promotion_min_sample_size`=5), when
  the strategy-family evaluation runs, then the recorded verdict is `insufficient_sample`,
  `basis_caveats` includes the Card-6.4 forming-bar caveat, and a served disclosure states the
  recorded null is 100 uniform-random entries, not count/ToD-matched.
- TC-11: given a Playbook-family hypothesis (e.g. S-1) reaching its confirmatory checkpoint, when
  the snapshot is recorded, then the `CertificateStore` gains no new record — the mint path
  fires only for `evidence_family == "strategy"` checkpoints.
- TC-12: given a strategy-family hypothesis reaching an attested, gate-passing confirmatory
  checkpoint, when `run_evaluation_and_record` completes, then exactly one certificate record is
  appended pinning `{candidate, champion_identity_at_scan_time, train_dataset, holdout_dataset,
  config_fingerprint, gate_version, referee_parameters_hash, family_id, hypothesis_id,
  gate_results}`, reachable only through this evaluation call, never a hand-written fixture path
  in production code.
- TC-13: given a strategy-family evaluation whose oracle attestation fails, when
  `run_evaluation_and_record` completes, then no certificate is minted and the evaluation's
  `role` reads `"pending"` (the same Rider-1 gate iteration 8 built for the playbook path).
- TC-14: given `referee_parameters()` called twice with unchanged module constants, when its
  return value is hashed, then the hash is byte-identical across both calls; given one referee
  constant is monkeypatched, when `referee_parameters()` is called again, then both the returned
  dict and its hash change (Parameters discipline counter-test).
- TC-15: given a registered estimand-B hypothesis with `context_predicate: {"backing_bucket":
  "at_wall"}` and a fixture corpus containing observations both inside and outside that backing
  bucket, when `GET /research/desk/referee/registry` folds that hypothesis's `accrual` and
  `discovery` blocks, then both counts include only observations satisfying the context
  predicate, matching the shortlist row's own live `n`/`n_sessions` for the identical
  `(setup_id, side, context_predicate)` cell.
- TC-16: given `GET /research/desk/referee/registry/shortlist`, when the response is inspected,
  then it includes a `range_trade:short at_wall` candidate (estimand B) alongside the existing
  `range_trade:long at_wall` S-4 candidate, with `n`/`n_sessions`/`accrual_rate_sessions_per_day`/
  `projected_days_to_target` computed by the identical `_starter_context_readiness` primitive.
- TC-17: given `GET /research/desk/referee/registry/shortlist`, when the response is inspected,
  then it carries `family_id: "referee-starter-family"` and `family_q: 0.10` as top-level keys,
  and `apps/frontend/app/desk/page.tsx`'s registration POST body reads both from the fetched
  response rather than a local literal.
- TC-18: given `tests/test_desk_ui_guards.py`'s `_PRICE_ARITHMETIC_FIELDS`, when its seeded
  counter-test runs against `hyp.accrual.*`, then a mutated-to-arithmetic rendering fails the
  guard and the shipped pass-through rendering passes it.
- TC-19: given the full backend suite, when it runs after this iteration's changes, then it
  collects at least 2,657 tests, 0 fail, and `Config().config_fingerprint()` prints
  `08e471b10130e1e2`.
- TC-20: given the kept `/desk` product after `rm -rf apps/frontend/.next` and a rebuild, when
  the golden-replay walk runs, then every shipped `/desk` section and the existing Referee
  Registry section render exactly as before, evidenced by a fresh dated screenshot.
- TC-21: given the Referee Registry shortlist after the `family_id`/`family_q` source-swap and
  the sixth-candidate addition, when `/desk` is opened in a real browser, then all six candidate
  rows render with their rationale and readiness numbers, the four untouched candidates' numbers
  are visually unchanged from iteration 8's capture, and a fresh screenshot is captured.

## NOTES

- **Human-owned, non-blocking, outside this project** (carried since iteration 2): the unrelated
  trendora backend on port 8255 has not been restarted. No action needed from this session.
- **Budget history:** iterations 6 and 7 were both planned as the deep pass; iteration 7 was
  demoted to lean by a wall-clock budget breach and shipped a real fault the deferred hard-audit
  later caught. This iteration's own new-scope surface is bounded to exactly goal.md's J-08
  steps 1–4 plus the four riders below — depth stays full regardless of any budget pressure,
  per the evaluator's own explicit request not to let this recur a third time.
- **Assumption logged:** `state/assumptions.md`'s iter-9 entry records reading spec §7's
  "(registered per side)" for S-4 as a plain instruction, not a human-ruling question — this
  iteration builds the missing short-side candidate directly rather than deferring it.
- **Riders folded in per the iter-8 evaluator's explicit next-step recommendation** (not new
  scope of their own): (1) the `discovery`/`accrual` wall-condition fix; (2) the S-4 short-side
  candidate; (3) moving `family_q`/`family_id` from an unowned browser literal to a backend
  constant + served field (closes coherence-audit F1, `iter-8/coherence.md`); (4) extending
  `_PRICE_ARITHMETIC_FIELDS` to `hyp.accrual.*`.
- **Golden replay:** no new browser acceptance exists for J-08 itself (`(Keyless; automated.)`);
  J-07's existing golden script should still replay cleanly after the source-swap refactor,
  since no rendered value changes — a fresh capture is precautionary regression evidence, not a
  new acceptance.

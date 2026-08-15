# Goal Session referee — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-0 — 2026-08-14T15:37:59Z

**Verdict:** CONTINUE
**Lesson:** The browser lanes run against the fixture-scoped QA backend
(`project-extensions/store-scope/`), NOT the operator's `apps/backend/.data/` store — so `/desk`
correctly renders "Desk screen not computed yet." and near-empty Playbook Evidence cells, and the
two playbook signatures stamped `2026-08-14T14:58:20Z` in `J-07-fail.png` are the rig's own seeded
records, not a write into the real store (store-scope guard: 11,274 protected files unchanged).
Read those empty states as the rig, never as a kept-product regression; and note that J-10's
acceptance embeds era-end clauses (the three Referee sections + 22 MCP tools), so the sentinel
stays `partial` until J-09 lands no matter how healthy the kept product is.
**Applies to:** any iteration reading `/desk` browser evidence, scoring J-10, or computing J-07's
shortlist readiness numbers from what the QA rig serves.

## iter-1 — 2026-08-14T18:05:00Z

**Verdict:** CONTINUE
**Lesson:** No golden replay script can exist for a backend-only journey: `demo_runner.py`
resolves every step's URL against the single frontend origin (`normalize_url` rewrites even
absolute `localhost` URLs onto `:3301`), so a `:8301`-only JSON endpoint is un-replayable and
lands in `state/golden-gaps` (J-01 is listed there now). Era 6's J-02–J-06 and J-08 are all
`(Keyless; automated.)` too, so plan their re-verification as pytest + an LLM browser-qa
live-endpoint smoke pass, never as replay coverage — and expect `golden-gaps` to keep growing
without that being a defect.
**Applies to:** any iteration targeting a backend-only Referee journey (J-02, J-03, J-04, J-05,
J-06, J-08) or reading `runs/goal-session-referee/state/golden-gaps`.

## iter-2 — 2026-08-14T19:20:00Z

**Verdict:** CONTINUE
**Lesson:** A pattern-based `pkill -f "uvicorn main:app"` used to clean up this project's dev
backend also killed an unrelated project's backend on the same host (trendora, port 8255,
still down at evaluation time) — the pattern is not project-specific, and the restore attempt
was correctly blocked as out-of-scope. Only exact-PID process-tree kills, captured before the
kill, are safe on this shared host. Related: this iteration's `UT-J-01-result.png` is
byte-identical to iteration 1's (a deterministic re-render of an unchanged static JSON body
looks exactly like a copied file), so a screenshot of a fully static payload cannot by itself
prove a fresh navigation — anchor such journeys on a live-code check instead (I printed
`current_playbook_detector_basis()` and the fingerprint and matched them to the pixels).
**Applies to:** any iteration whose developer starts/stops `scripts/dev.sh` or any local
server; and any journey whose only evidence is a screenshot of a static JSON endpoint
(J-01–J-06, J-08 in this era).

## iter-3 — 2026-08-14T22:05:00Z

**Verdict:** ESCALATE
**Lesson:** A statistical procedure can be exactly-enumerated, fully deterministic, oracle-suite
green, and still anti-conservative: in `referee_stats.permutation_test`'s enumeration branch,
`g2_sum = total - g1_sum` (:424) differs by ~1 ULP from `_t_statistic`'s own `math.fsum(group2)`
(:454), so the OBSERVED grouping fails `_is_extreme` (:430) and p drops to 1/(N+1) — below the
exact test's own 2/(N+1) floor — on 1.7% of 2v2 fixtures, concentrated on the most extreme
results. Two structural blind spots hid it: every oracle generator uses S>=10 sessions so the
permutation space always exceeds `REFEREE_ENUMERATION_THRESHOLD` and the enumeration branch is
NEVER exercised by the suite that "IS the acceptance"; and the one enumeration unit test
(`test_referee_stats.py:258`) uses 5.0/1.0/2.0 — binary-exact values that cannot expose a
float-accumulation asymmetry.
**Applies to:** any iteration touching `apps/backend/app/research/referee_stats.py` or adding a
statistical procedure with two computation branches. Three rules: (1) whenever a quantity is
computed two ways in the same function (fsum vs subtraction, general path vs fast path), assert
the OBSERVED/identity case is bit-identical between them, not just "close"; (2) an oracle suite
must exercise EVERY branch it claims to prove — check the branch predicate against the
generators' own shapes before trusting a green suite; (3) a mutation fixture whose mutant is
conservative by construction (here: every mutant p == 1.0, rejection rate exactly 0.0) proves the
suite catches over-cautious bugs only — pair it with an ANTI-conservative mutant, since that is
the direction that manufactures false findings.

## iter-4 — 2026-08-15T07:05:00Z

**Verdict:** CONTINUE
**Lesson:** A boundary-property test is only as good as the regime its generator samples. The
developer's 3,000-case floor test in `apps/backend/tests/test_referee_stats.py` drew BOTH groups
from the same zero-mean generator, where the observed grouping is the unique maximum with
probability only `1/draws_used` — so the floor was almost never approached and the test passed
even against a build with half the fix reverted (the auditor proved this by mutation). The
tail-regime variant (groups deliberately shifted apart) hits the floor constantly: my own 2,500-case
sweep landed 448 cases exactly ON the floor, and the audit-added tail block carries an
`assert at_the_floor >= 100` can-fail guard so it cannot silently drift out of the sensitive regime.
Any floor/boundary property test in this era must (a) generate in the regime where the boundary is
actually reached and (b) assert how many cases reached it.
**Applies to:** any iteration adding a property/oracle test for `referee_stats.py` or its
consumers (J-04 nulls, J-06 estimands, J-08 gates) — especially any test asserting an inequality
against a mathematical floor, ceiling, or exact-attainability bound.

## iter-5 — 2026-08-15T08:45:00Z

**Verdict:** ESCALATE
**Lesson:** A "hand-verified draw" test can be structurally vacuous: every fixture in
`apps/backend/tests/test_referee_null.py` gives the builder at most K=4 eligible anchors while it
must draw K=4, so the seeded Fisher–Yates SELECTION is never exercised — any permutation, and even
a broken selector, passes. Reviewer and coherence both missed it; the evaluator only caught it by
counting each fixture's `range(n)`. Whenever a test claims to verify a seeded/random choice, check
that the candidate pool is strictly LARGER than the number drawn, and that two different keys
produce different draws.
**Applies to:** any iteration whose acceptance names a seeded draw, sample, shuffle, or bootstrap
— `referee_null.py`, `referee_stats.py`, `desk_forward._draw_anchor_indices`, and the J-06
estimand evaluators that will reuse all three.

## iter-6 — 2026-08-15T10:30:00Z

**Verdict:** CONTINUE
**Lesson:** A validation that guards one field is worthless if a SIBLING field on the same
request reaches the same derived value by another route. `referee_registry.py`'s
`RetroactiveBoundary` carefully refused a caller-supplied `confirmation_start_boundary` while
`registered_at` — the sole input the boundary is *computed from* — sat unguarded on the same
POST body and the same CLI, letting a caller backdate the immutable boundary to any date and
make already-recorded historical sessions accrue as forward confirmation. Reviewer
(`spec_alignment: complete`) and QA (`PASS`) both cleared it; only the full pipeline's hard
audit ran the adversarial payload. The iteration's own `assumptions.md` entry had reasoned
correctly about the guarded field and never applied the identical argument to the field behind
it.
**Applies to:** any iteration adding validation to a DERIVED value (boundaries, identities,
signatures, hashes) — enumerate every input the value is derived from and confirm each is
either server-stamped or refused, not just the value's own name-alike field. Also: any
`Frontend Present: no` iteration — the browser/replay lane self-skips wholesale, so the
`Required-still-passing` DoD item silently does not run (auditor gap T3); a backend-only
iteration must still schedule the kept-product replay, or the sentinel journey accumulates
unverified iterations.

## iter-7 — 2026-08-15T12:45:00Z

**Verdict:** ESCALATE
**Lesson:** A fail-closed rail that only guards the SERVED response leaves the append-only record
unguarded: `referee_adjudicate.run_evaluation_and_record` computes `run_oracle_attestation()`,
then proceeds regardless of its `passed` flag — so a failed attestation still mints the
hypothesis's one permanent `corroborated` snapshot while `adjudications_response()` correctly
refuses to serve it (evaluator probe, iter-7). On an append-only store the write side needs the
same gate as the read side, because the read side can be re-run and the record cannot. Second half
of the same lesson: an integrity-error disclosure must be added to EVERY reader of a store, not
just the endpoint whose audit finding named it — Rider 2 fixed `GET /registry`, and the brand-new
`GET /adjudications` shipped the identical silent-drop on the same hypothesis store.
**Applies to:** any iteration touching the `referee_*` append-only stores (evaluations,
adjudication snapshots, registry, nulls, certificates) — especially J-07/J-08, which add the first
real operator write acts and the certificate mint path.

## iter-8 — 2026-08-15T15:35:00Z

**Verdict:** CONTINUE
**Lesson:** The fixture-scoped browser rig can STRUCTURALLY hide an arithmetic defect: the
shortlist's `projected_days_to_target` bug (audit B2) rendered a plausible 517 on the rig's
one-session corpus and only became "0 days — ready now" on the operator's real 210-record corpus,
because the two candidate formulas only diverge once a cell already exceeds its target. Any served
number whose formula has a subtraction, a floor, or a saturation point must be hand-checked against
REAL-corpus magnitudes (or a fixture deliberately built past the saturation point) — a green
browser pass on the rig proves rendering, never arithmetic. Second, related: when a new fold is
described as "the exact complement" of an existing one, check WHICH filters it inherited —
`_hypothesis_discovery` copied `_hypothesis_accrual`'s setup/side proxy but not the context
predicate that `shortlist_response` applies to the same candidate, so `/desk` can show 0 in one
table and 3 in the other for the same wall-based candidate (evaluator probe, iter-8).
**Applies to:** any iteration adding a served numeric to `referee_registry.py` /
`referee_adjudicate.py`, any "complement/mirror of an existing fold" work, and every browser
acceptance that reads numbers off the fixture-scoped rig.

## iter-9 — 2026-08-15T17:10:00Z

**Verdict:** ESCALATE
**Lesson:** A gate that compares PINS is not the same as a gate that validates EVIDENCE. J-08's
`authorize_promotion` compares every certificate field against the live scan correctly, yet
`referee_adjudicate._pool_strategy_trades` / `referee_evidence.strategy_observations` take only a
`JournalStore` and pool every recorded backtest trade unfiltered by `strategy_id`/`profile`, and
`_mint_strategy_certificate` stamps whatever `candidate` dict its caller hands it — so a certificate
can honestly pass every pin check while its statistics came from a different strategy entirely
(I reproduced this end-to-end in an isolated store). When a future iteration wires
`journal_store`/`certificate_mint` into `POST /research/desk/referee/evaluate`, the interlock
becomes ceremonial unless the pooled evidence's own identity is checked against the certificate's
named candidate.
**Applies to:** any iteration touching `referee_adjudicate.py`'s mint/evaluation rail,
`referee_evidence.strategy_observations`, or wiring the `/evaluate` route — and generally, any
"X-specific certificate/token" gate: test that the token's SUBJECT matches the DATA it was derived
from, not only that its recorded fields equal the caller's.

**Second lesson (process):** `depth_full_granted` fires only on `reason: prior-verdict-ESCALATE`.
A `CONTINUE` verdict carrying `next_depth: full` was demoted to lean by the wall-clock budget in
iters 7 and 9 despite the iteration spec pleading against it. If a round genuinely needs the hard
audit lane, the verdict itself must be ESCALATE — a depth recommendation attached to CONTINUE is
advisory only.

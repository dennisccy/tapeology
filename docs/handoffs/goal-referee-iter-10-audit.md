# goal-referee-iter-10 Audit Report

**Date:** 2026-08-15
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The iteration's three substantive claims all hold under independent verification: the two new
`/desk` Referee panels render served values verbatim with no client-side derivation, the MCP
surface genuinely advertises 22 read-only GET proxies, and rider 1 genuinely closes the iter-9
MINOR anti-goal entry (I re-derived the exploit path and the fix in the source, not from the
handoff). Two DEFINITION-OF-DONE lines are only partially met, both evidentiary rather than
behavioural: TC-8's *rendered* single-flight refusal was never screenshotted (UT-09's cited
evidence is byte-identical to UT-07's image), and 7 of the 8 required-still-passing journeys were
shed as `DEFERRED-BUDGET` rather than re-verified. Nothing critical or important was found, so no
fixes were applied.

---

## 2. Findings

### Backend Findings

**B1 — GAP (gap): `_candidate_matches_observation` treats "both unknown" as a match**
`apps/backend/app/research/referee_adjudicate.py:545-550`. When `journal_store.get_backtest()`
returns `None` (or a record whose `result` block carries no identity fields), the memo stores
`(None, None)`; the comparison is then `None == candidate.get("strategy_id") and None ==
candidate.get("profile")`. A candidate dict that omits both keys therefore matches every
identity-less observation, and the mint would stamp a certificate naming `{}`. Unreachable today:
`certificate_mint` has zero production callers (verified — `_mint_strategy_certificate` has exactly
one call site, `referee_adjudicate.py:1491`, and `pnl_scan.py:594` only *reads* the store), and
`authorize_promotion` (`:1835`) requires an exact `record["candidate"] == candidate` match against a
live scan identity that always carries real strings, so such a certificate could never authorize
anything. Recommended hardening (not applied — out of scope for this iteration's fix mandate):
reject a `candidate` missing either key, and treat an unresolvable backtest record as a non-match
explicitly rather than by coincidence.

**B2 — OBSERVATION (observation): the backtest id is re-parsed out of the observation id when it is
already served on the observation**
`referee_adjudicate.py:522-531` splits `strategy:{backtest_id}:{kind}:{index}` to recover the
backtest id, while `referee_evidence.py:821` already stamps `source_record_id=backtest_id` on the
very observation being filtered. The parse is safe today (`backtests.py:1254` mints ids as
`uuid.uuid4().hex`, colon-free) and raises loudly rather than silently mis-matching if the prefix is
wrong, but it is a derived read where a direct one exists. A test-planted id containing a colon
would silently resolve to a wrong/absent record and fail *closed* (evidence dropped, mint refused).

**B3 — OBSERVATION (observation): rider 2's cleanup is complete, one sibling stale comment remains**
`grep -c unwired apps/backend/app/research/referee_adjudicate.py` → `0` (TC-16 verified directly).
Unrelated but same class: `apps/frontend/app/desk/page.tsx:8701` still reads "the census stays
19/7/1 across this change" after the census moved to 21/9/1 this iteration.

### Frontend Findings

**F1 — GAP (gap): a failed registry fetch renders "unknown" as "absent"**
`apps/frontend/app/desk/page.tsx:4998-4999` renders `hypothesis?.null_spec_id ?? "—"` /
`hypothesis?.test_spec_id ?? "—"`. The Adjudications section reads those two provenance fields from
a *second* endpoint (`toggleSection`, `:8457-8463`). If that registry GET fails while the
adjudications GET succeeds, every row silently shows `null spec: —` — indistinguishable from a
strategy-family hypothesis that genuinely has `null_spec_id: null`. The primary fetch has an
`UnavailablePanel` path (`:5033-5040`); the cross-reference fetch has none. Under this project's own
T-5 discipline ("unmeasurable = counted exclusion, never zero") the unknown case should be labelled
distinctly.

**F2 — GAP (gap): no mount-time seed for an already-running compute**
Both new managers are keyed per `null_spec_id` / `hypothesis_id` and only learn about a job from
their own trigger response (`:8520-8609`) or their poll effects (`:8640-8682`). A run started from
another tab, from the CLI, or before a page reload renders as idle "Build Null" / "Evaluate" until
re-triggered. Clicking then POSTs and the backend-authoritative `started: false` surfaces the
refusal, so no duplicate run is ever created — the UI is temporarily stale, never wrong about what
was written. Disclosed by the developer as a deliberate simplicity-bar call; genuinely reversible
(one snapshot fetch per discovered key on first expand).

**F3 — OBSERVATION (observation): the BH fold renders for a refused entry**
`page.tsx:5002-5007` renders `BH: k_star / m (q=…)` from `entry.snapshot` even when
`confirmatory_output_refused` is true — visible in `UT-04-result.png` on the `QA-REFUSED-1` row.
This is not a masquerade: the same provenance block prints `attestation: fail` immediately above it,
the verdict chip reads `insufficient_sample`, and the Status column carries the full refusal
sentence. The fold itself serves the raw snapshot alongside the refusal
(`_snapshot_fold`, `referee_adjudicate.py`), so the page is rendering its owner's payload verbatim
rather than inventing a confirmatory claim. Recorded because a future design pass may prefer to
suppress or visibly strike the fold numbers on a refused row.

**F4 — GAP (gap): "seed identity" is the hypothesis id**
`page.tsx:5000` renders `seed identity: {entry.hypothesis_id}` — the same value already shown as the
row's first column. No served field anywhere carries the seed: `REFEREE_SEED` is a module constant
folded into `_evaluation_basis`'s hash (`referee_adjudicate.py:688`) and never persisted per record;
`run_oracle_attestation()` (`referee_stats.py`) carries no seed either. The alternatives were a
client-side copy of a backend constant (single-source-of-truth risk) or a new Data Contract row
(explicitly out of scope), so the choice is defensible and is logged with its reversal path in
`runs/goal-session-referee/state/assumptions.md` (iter-10, developer). Still: an operator reading
that line learns nothing about the seed. Closing it properly needs a served field in a later era.

### Test Findings

**T1 — GAP (gap): TC-8's *rendered* single-flight refusal was never captured**
`reports/phase-goal-referee-iter-10-ui-test-results.md` UT-09 cites
`reports/qa/goal-referee-iter-10-evidence/UT-09-result.png`, which is byte-identical to UT-07's and
UT-10's images (`md5 d3065788c71ecfcc5623b7704ad6de73` for all three). I opened it: it shows the
Null Builds control, an 18-row null ledger and the evaluation ledger — and no refusal message
anywhere. The browser-QA report is honest about why (the second click landed on an
already-`disabled` button, so no second request was ever dispatched). The *behaviour* is proven
twice over and I re-verified both proofs: the backend refusal branch exists and returns the
unchanged snapshot (`referee_adjudicate.py:1551-1554`), a unit test asserts it end to end
(`tests/test_referee_adjudicate.py:1744-1770`, TC-32 — `started is False`, same compute id, a
different hypothesis still starts), and QA's 5-concurrent-POST probe produced exactly one
`started: true`. What is missing is only the screenshot the DoD asks for, and with it any proof
that `control.triggerError` (`page.tsx:5170-5177`) reaches the screen. Severity call: I was
between GAP and IMPORTANT and chose GAP because no specified behaviour fails — only its pixel-level
evidence is absent.

**T2 — GAP (gap): 7 of 8 required-still-passing journeys were not re-verified**
The merged UI results carry a "Deferred (iteration budget)" table marking UT-J-01…UT-J-06 and
UT-J-08 `DEFERRED-BUDGET`; only J-07 replayed (`reports/phase-goal-referee-iter-10-regression-replay-results.md`,
1/1 PASS). Only `J-07.json` is a valid golden — `runs/goal-session-referee/journey-scripts/` holds
`J-01.json.invalid` and `J-02.json.invalid` — so the other seven needed the LLM fallback the budget
shed. Compensating evidence, which is substantial but not equivalent: the full backend suite (where
J-01–J-06/J-08's substance lives) is green under my own run, UT-13 walked every shipped `/desk`
section, and UT-14 re-walked cockpit and `/structure` pinned-AAPL. This is the era's final
iteration, so I am flagging it explicitly for the evaluator rather than burying it.

**T3 — OBSERVATION (observation): the store-scope guard does not protect the referee stores**
`reports/qa/goal-referee-iter-10-store-scope-guard.md` lists 12 protected paths — none of them a
referee store. The referee dirs are *siblings* of the universe dir
(`referee_registry.py:206-214`, `referee_adjudicate.py:246-255` → `.data/referee_registry`,
`.data/referee_eval`, `.data/referee_null`, `.data/*_runs`), so the guard's manifest would not have
noticed a write into the operator's real referee store — the exact append-only, delete-free stores
this iteration's buttons write to. Nothing leaked: `apps/backend/.data/` contains no referee
directory at all (verified), and every seeded record lives under the scoped rig root
(`…/tapeology-store-scope-qa/rig/referee_*`). Worth adding those four paths to the guard before any
future era touches them again.

**T4 — OBSERVATION (observation): TC-15's "byte-identical" claim is near-tautological**
`tests/test_referee_adjudicate.py::test_iter10_tc15_…` compares `_pool_strategy_trades(store)` with
`_pool_strategy_trades(store, candidate=None)` — the same code path, since `candidate=None` is the
default. It does not compare against pre-rider behaviour. The equivalence does hold by inspection
(with `candidate is None` the new block is skipped and both loops iterate the untouched lists), and
the real regression proof is the untouched iter-9 real-corpus acceptance test, which the suite still
runs. Recorded so nobody mistakes TC-15 for a stronger guarantee than it is.

**T5 — OBSERVATION (observation): QA verified two riders from the handoff, not the code**
`reports/qa/goal-referee-iter-10-qa.md` states rider 1 was "verified in dev handoff" and rider 4
"verified in dev handoff". Both are in fact correct — I checked the source and the diff directly —
but those two DoD lines rest on the reviewer's and this audit's code-level checks, not on QA's.

---

## 3. Domain Assessment

**Rider 1 genuinely closes the recorded anti-goal, and the fixture edits it forced are legitimate.**
The iter-9 entry (`runs/goal-session-referee/state/journey-history.json`, `resolved: false`) named
unblock option (a): scope the pooling to the certificate's own `(strategy_id, profile)`. That is
exactly what landed. I traced the whole rail rather than trusting it: the filter narrows *both*
`observations` and `null_observations` (`referee_adjudicate.py:584-594`), so a candidate's Δ_d is
never diffed against a foreign strategy's null baseline; `coverage` is derived from the *filtered*
pool (`:1291-1297`), so an unrelated candidate cannot pass floors on counts it did not earn;
`evaluation_basis` hashes the filtered observation-id set (`:1298-1305`), so a filtered mint
evaluation cannot dedup onto an unfiltered monitoring record; and the mint site is gated behind
`recorded["role"] == "checkpoint"` (`:1476-1493`), which `confirmatory_eligible` (`:1349-1352`)
cannot reach on an empty pool. Every remaining path fails closed.

The five modified pre-existing tests are a real fixture bug, not a weakened assertion. I re-derived
it independently: `_mint_matching_certificate_through_the_real_rail`'s three callers declare
candidates `{v1, faster_warmup}` (×2, `test_pnl_scan.py:466`, `:694`) and `{structure_tape, default}`
(`:920`), while `_plant_strategy_backtest` hardcoded `STRATEGY_V1_ID`/`PROFILE_DEFAULT` into every
planted report. The two `test_referee_adjudicate.py` tests declared `"structure_tape"` over evidence
`_plant_strong_strategy_effect` plants as `v1/default`. Threading the candidate identity into the
planted reports makes each fixture internally consistent; it does not soften anything, because the
tests still require a certificate minted through the real rail and still assert the champion pointer
moves with exactly one ledger row. I also checked the change is inert to the system under test:
`pnl_scan.py` never enumerates the journal (`get_backtest` at `:206` reads back only the backtest it
just created), so re-stamping those 12 planted rows cannot alter the sweep's own candidate selection.

**The refusal rail is the strongest evidence in this iteration, and it is real.** I opened the
seeded rig: `snapshot-QA-REFUSED-1.json` stores `verdict: "corroborated"` with `bh_pass: true` and
an attestation carrying `stats_core_version: "stale-fixture-version-mismatch"`. The screenshot shows
that entry served as `insufficient_sample` with the exact refusal sentence and `attestation: fail`.
That is a stored confirmatory verdict being genuinely refused at fold time by
`verify_oracle_attestation`, not a manufactured pass. `snapshot-QA-FRAGILE-1.json` carries a real
passing attestation (matching expected/actual quantities) and a non-empty `fragility_triggers`; its
`fragile` token was seeded rather than derived, but the derivation itself is covered by three
existing unit assertions (`tests/test_referee_adjudicate.py:732`, `:748`, `:779`). Both seedings
went to the scoped rig only.

**Read-only MCP and single-source-of-truth hold.** `app/mcp/__init__.py` dispatches through exactly
one HTTP verb (`client.get(path)`, `:517`); both new entries are `_STATIC_PATHS` rows with empty
input schemas. The new sections compute nothing: I scanned the entire new JSX region
(`page.tsx:4953-5600`) for `Math.`, `toFixed`, `reduce(`, `* 100`, and verdict-shaped ternaries —
zero hits. Each provenance field is read from its canonical owner (adjudications fold, or the
registry endpoint for the two fields the fold does not carry).

**DEFINITION OF DONE, verified.** Fully traced by me: rider 1 and its five fixture edits (above);
the guard-count re-derivations — `page.tsx` contains exactly 21 `useEffect(`, 9 `setInterval(`, 1
`setTimeout(`, matching `_EXPECTED_EFFECT_COUNT = 21` / `_EXPECTED_INTERVAL_COUNT = 9` /
`_EXPECTED_TIMEOUT_COUNT = 1` with the mandatory rationale paragraph present
(`test_desk_refresh_chain_guard.py:157-180`), and all four new trigger identifiers added to
`_TRIGGER_CALLS`; the `_PRICE_ARITHMETIC_FIELDS` extension plus its seeded counter-test, which
asserts both the `?.` and plain-dot forms *and* that the page's real pass-through idioms stay clean
(TC-20 genuinely met, not just listed); rider 3, whose can-fail proof now appends a banned token to
the real `pnl_scan.py` source and runs the same `_assert_no_bypass_tokens` helper the production
lint calls, so gutting the scan breaks both tests (TC-17 genuinely met); rider 2 (`unwired` count
now 0, TC-16); rider 4 (the duplicate `S-5` line is gone and nothing else in that test changed,
TC-18); the 22-tool surface (`len(TOOLS) == 22`, no duplicates, in-process check) and its six new
byte-identity tests, which compare MCP bytes against a live `httpx.get` in empty, populated and
corrupted-file states (TC-11/TC-12); and the full suite, which I ran myself in the foreground —
**2688 collected, 2680 passed, 8 skipped, 0 failed, exit 0** in 260s, with
`Config().config_fingerprint()` printing `08e471b10130e1e2` (TC-22, ≥ 2,678 floor met).
Accepted on the reviewer's PASS (`reports/reviews/goal-referee-iter-10-review.md`:
`definition_of_done: complete`, `issues: []`) *plus* an executed QA row, per the mechanical-item
rule: honest empty states (UT-02, UT-05), the populated `fragile` + refused pair (UT-04 — which I
additionally opened and cross-checked against the seeded store), the completed null-build and
evaluation runs (UT-07, UT-08), the run-ledger field rendering and sort behaviour (UT-11), the
kept-product walk (UT-13, UT-14), and MCP tool advertisement (UT-12). Partially met: the TC-8
screenshot (T1) and the J-01–J-08 re-verification line (T2).

**Process context worth recording:** `ux-regression` was skipped (SPEED-15 rung 3b), the demo run
was SKIPPED on an invalid script step, and no iter-10 coherence audit exists at the time of this
audit. All three are non-blocking showcase/advisory lanes, all three are disclosed in their own
artifacts, and none of them gates a DoD line — but the "single source of truth" hard-fail check has
therefore not been machine-applied to this diff. My own read of the new code found no contract value
recomputed or served from a non-canonical owner.

---

## 4. Fixes Applied During This Audit

None. No CRITICAL or IMPORTANT finding was identified; every item above is a GAP or OBSERVATION, and
fixing those would be scope creep. The working tree is unchanged by this audit.

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No fixes required |

---

## 5. Recommended Next Step

Proceed to the goal-evaluator with this iteration's work intact — J-09's build is complete and
J-10's kept-product walk was genuinely performed. Two decisions belong to the evaluator, not to me:

1. **T2 is the only material question for an era-close verdict.** Seven required-still-passing
   journeys carry `DEFERRED-BUDGET`, not a fresh pass. If the evaluator is willing to accept the
   green 2,680-test suite plus UT-13/UT-14 as the standing evidence for J-01–J-06/J-08 (whose
   substance is backend, and six of which have no valid golden), the era can close; if not, the
   honest remedy is one short browser lane replaying those journeys, not a re-build.
2. **Flip the iter-9 anti-goal entry to `resolved: true`** in
   `runs/goal-session-referee/state/journey-history.json`. Its own `unblock_options` (a) is
   implemented as specified, reproduced by TC-13 and balanced by TC-14/TC-15, and re-derived
   independently in this audit.

Carry forward as non-blocking follow-ups: capture the rendered single-flight refusal in a later
browser pass (T1); add the four referee store dirs to the store-scope guard's protected paths (T3);
serve a real seed field before another era relies on the "seed identity" line (F4); and, when a
future era wires `journal_store`/`certificate_mint` into a route, harden the `(None, None)` match in
`_candidate_matches_observation` first (B1).

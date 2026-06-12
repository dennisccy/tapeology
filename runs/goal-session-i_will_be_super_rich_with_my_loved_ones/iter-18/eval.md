**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** lean

# Iteration 18 Evaluation

## Summary

The replay-study layer (capability 32) is built, reviewed PASS, coherence-PASS, and its backend is exhaustively CI-proven — the evaluator independently re-ran the full suite (671 passed / 1 skipped, exit 0), the pinned reference-study gate (4/4, numbers byte-match the handoff), the 38 study unit/API tests, observer-equivalence (7/7), and the dense-replay gate (11/11). J-62 flips to passing on that automated evidence (its acceptance is explicitly automated, no pixel clause). But browser QA was SKIPPED 0/33 — the frontend dev server was down (its `.next` corrupted by the production-build step) — so the brand-new `/studies` UI has zero pixel evidence: J-60 and J-61 advance only failing → partial and the J-68 pixel sentinel was not re-run. Next iteration is a browser-verification pass.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-60 | failing | **partial** | Backend leg CI-proven: runner + auto-arm + seeded null baseline + re-run determinism + feed/fingerprint stamps (apps/backend/tests/test_studies.py, test_studies_reference.py — evaluator re-run, 38+4 green; QA TC-01 created a live study via API). UI leg (open `/studies`, create, watch status, read results) — **no pixel evidence**, browser QA SKIPPED 33/33, no evidence dir. |
| J-61 | failing | **partial** | Hindsight-level 422 + label + cross-study exclusion, truncation counted separately, mid-run cancel → explicit `cancelled` + partial-marked, failure → explicit error — all unit/API tested (test_studies_api.py; QA TC-04/06/09/10). The visible-label/progress browser legs unverified. |
| J-62 | partial | **passing** | apps/backend/tests/test_studies_reference.py — evaluator re-ran in isolation: exact pinned occurrence rows (`r_basis [0.3, 0.6]`, verdicts `["invalidated","confirming"]`), setup + null aggregates (n=2 / n=99 PG SIP; n=1 / n=100 SIM-REVERSAL) byte-stable, double-run deterministic, unpaced, no credentials, in the config-owned budget; iter-17 engine gates green untouched (dense gate 11/11, observer-equivalence 7/7). Pinned test values diff-checked against the handoff: identical. |
| J-68 | partial | **partial** | Byte-identity clause re-verified this iter (observer-equivalence 7/7 evaluator re-run; re-diff confirms zero engine/provider/classifier/chart files touched). Pixel sentinel NOT re-run (browser skipped); J-01–J-37 clause debt unchanged. |
| All required-still-passing | passing / already_passing | carried (no regression evidence) | Engine, research-verdict, journal, analytics code untouched (re-diff vs 6a7e2e4: only `app/research/{studies,routes,store,taxonomy}.py`, `config.py`, `main.py`, frontend studies files + NavBar enable). Full suite 671/1 green, zero re-pins. No pixels this iter — nothing tested failed. |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No profitability/edge claims (critical) | OK | Studies copy is measurement-framed ("journaled MEASUREMENTS of a replay … not a profitability claim, an edge, a win rate, or a forecast", taxonomy.py:419–420); n + null baseline + caveats always rendered; "Descriptive only — not trading advice" in payload copy. Grep for imperative/edge language: only negating discipline comments. |
| Source/feed/config honesty (critical) | OK | Every study stamped with source, `data_feed`, `config_fingerprint`, recorded null seed (studies.py:417–420, 567); 5 result-shaping study keys IN fingerprint, only serving-only `study_list_max` excluded with rationale + stability/counter tests (config.py:730–735); hindsight-level studies excluded from cross-study aggregation (code + test). |
| Research layer read-only over engine (critical) | OK | Re-diff: no `app/engine/`, `app/providers/`, classifier, history-buffer, or chart file in the diff; observer-equivalence 7/7 evaluator re-run; fresh-engine replay via the observer seam only. |
| Deterministic & reproducible | OK | Double-run determinism test green; recorded seed reproduces the null baseline exactly. |
| No new indicators, no auto-tuning (critical) | OK | Arming composed of existing states; occurrence-R is config-owned (`study_occurrence_r_spread_multiple` × spread, floored) routed through the single `marks.r_basis` helper (studies.py:80, 289) — documented research default, never fitted. |
| No scanning, no execution | OK | Studies run only over explicitly chosen windows; no background detection. |
| No prediction language (critical) | OK | Present-tense, descriptive copy throughout taxonomy + components. |
| Evidence before cues (critical) | OK | No cue-layer code (checklist/stance/hints) in the diff — correctly out of scope. |
| Persistence scoped to research records | OK | No schema bump (v7; store diff carries no CREATE/ALTER/migrate lines — verified); one-replay-pass null baseline held in-job memory; no tape data persisted. |
| Real-data journeys proven with real data (critical) | OK | The J-62 gate runs over the committed real PG SIP fixture, credential-free, fails loudly if absent (never substitutes synthetic). |

No violations. `anti_goal_violations` stays empty.

## Coherence

COHERENCE-PASS (runs/goal-session-…/iter-18/coherence.md): row-23 single owner + canonical endpoints, persist-once, registered-consumer R/excursion paths, `/studies` at its pre-registered IA home, 1-click nav, no duplicate home. The nav-skeleton change (Studies entry enabled) followed protocol: blueprint iter-18 note + `state/blueprint.reapproval-requested` present (verified on disk) — the session will pause for human blueprint re-approval per protocol.

## Next-Step Recommendation

A **lean browser-verification iteration** — the code is done, reviewed, and CI-proven; what is missing is exclusively pixel evidence:

1. Restart the frontend dev server cleanly (the production-build step corrupted the shared `.next`; fresh server + canary probe per the iter-6 lesson — `GET /research/taxonomy` must carry the studies copy).
2. Execute the already-designed 33-test browser plan: J-60 end-to-end on the reference-window quick-pick (create → queued→running→done → results with side-by-side null baseline, stamps, re-run identical in pixels), J-61 legs (hindsight label, truncation, cancel → cancelled + PARTIAL, failed → explicit error), the J-68 sentinel (cockpit unchanged except the enabled Studies entry), and Journal/Cockpit reachability.
3. Flipping J-60/J-61 completes the Evidence-before-cues gate (J-58–J-62), unblocking the strictly-last cue layer (J-53, J-63–J-67) for subsequent iterations.

Note for the orchestrator: the pending `blueprint.reapproval-requested` human gate must clear before/with the next iteration.

## Remaining After This Iteration

J-60, J-61 (pixel legs only), J-68 partial-clause debt, then the cue layer: J-53, J-63, J-64, J-65, J-66, J-67. Long-tail partials from iter-0 (J-11/J-14/J-16/J-18/J-20/J-22/J-23/J-27/J-28/J-29/J-32, J-15 unknown) feed the J-68 "J-01–J-37 all green" clause.

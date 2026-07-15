# goal-tradable_wall-iter-8 Audit Report

**Date:** 2026-07-15
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The two code deliverables (Cleanup A in `PriceChart.tsx`, Cleanup B in `test_price_chart_confluence.py`) are correct, surgical, in-scope, and honestly documented; no frozen file was touched, `config_fingerprint` stays `4d665603569b9dbf`, and I independently verified from disk that the real credentialed corpus is genuinely honest (11 historical windows / 10 symbols / every feed=`sip` / pinned AAPL present / no credential in any dataset file). The substantive J-03 data path is verified real at the disk/API level.

However, this is the GOAL_ACHIEVED-candidate iteration and its DoD item 1 ("J-03 passes via **browser-qa**") plus the entire browser TESTING-REQUIREMENTS block were **not executed** (Chrome unavailable), and the DoD item "Edge Report renders populated cells" was **never observed end-to-end** (only an indirect resolution cross-check; the endpoint takes ~10+ hours on the real corpus). These gaps are honestly disclosed, low-risk (the rendering code is unchanged and reads the endpoints verbatim), and environmental/performance rather than code defects — hence gaps, not a FAIL. **The auditor does not certify J-03 as `passing`; per the evidence floor it is `partial`/`unknown` at the journey level this iteration, and the evaluator must weigh the missing browser evidence before the two-key GOAL_ACHIEVED confirm.**

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (gap): DoD "Edge Report renders populated cells" was never observed end-to-end.**
The spec DEFINITION OF DONE requires the Edge Report to render populated cells (real `n`, honest `insufficient_sample`, train/hold-out and feeds never pooled, full PnL register + null baseline). The dev handoff (`docs/handoffs/goal-tradable_wall-iter-8-dev.md:130-139`, "Live Verification" + "Known Issues") states `GET /research/edge-report` was **not run to completion** — measured replay throughput (~708 events/sec; the pinned AAPL dataset alone took 13m 4s for 555,382 events) extrapolates to ~10+ hours for 11 datasets × 3 strategies over ~9.1M rows, with no partial-result caching. The dev substituted an **indirect** cross-check: all 11/11 real datasets resolve to a classified scan event (classes A/B/C, both sides, reactions rejected/broke/chopped, 7 train / 4 holdout, all feed=`sip`) using `edge_report.py`'s own `_dataset_event` matching rule. That is strong evidence the report *will* populate diverse cells, but the cells themselves were never rendered or returned. Per rubric §5 ("Data/metric is X" → the computing artifact, never prose) and §2, the claim "Edge Report renders populated cells" is `unknown`, not `passing`. Not fixable by a source edit in this verification-only iteration (see B2).

**B2 — GAP (not fixed, out of scope): `GET /research/edge-report` is ~10+ hours against the real corpus — a real usability limitation.**
A user opening `/structure`'s Edge Report section against the current persisted store will wait hours, not seconds (no `_SCAN_CACHE`-equivalent for this endpoint, unlike `GET /research/setups`). This is pre-existing (documented since iter-3/iter-4 against a much smaller store) and explicitly outside this lean, verification-only iteration's scope; adding caching would be new code and a new gate obligation. Recommend a future iteration add an `edge_report.py` cache mirroring the `_SCAN_CACHE` precedent, and/or pre-warm the endpoint before any browser-QA that must observe populated cells. Documented as a known limitation — fixing it here would be scope creep.

**B-positive — No frozen-file drift; foundations byte-identical.** `git diff --name-only -- apps/` returns exactly `apps/backend/tests/test_price_chart_confluence.py` and `apps/frontend/components/PriceChart.tsx`. `config_fingerprint()` independently recomputed to `4d665603569b9dbf` (unchanged). No frozen module (`levels.py`, `tradability.py`, `engine/`, `config.py`, `strategies.py`, `backtests.py`, `adapters/`, `bars.py`, `datasets.py`) in the diff.

**B-positive — Data honesty holds (verified from disk, not from the handoff).** `apps/backend/.data/datasets/` = 18 files, **0 tracked by git** (`git ls-files` empty; ignored via `.gitignore:72` `.data/`), so OUT OF SCOPE "no dataset commit" is honored. Of these, 11 are `source_kind: historical`: symbols {AAPL×2, AMD, AMZN, GOOGL, META, MSFT, NFLX, NVDA, SPY, TSLA} = 10 distinct, splits 7 train / 4 holdout, **every `data_feed` = `sip`** (never `iex`, never `yahoo` — feed-honesty anti-goal holds), the pinned `5c7f1a44…` (AAPL 2026-06-22 12:30–15:00Z, 555,382 events, checksummed) present. A defense-in-depth grep for `ALPACA_API|api_key|api_secret|bearer|authorization` across all 18 dataset files returned nothing — no credential in any dataset body (the keys-never-logged anti-goal holds even for the gitignored raw recordings that the credential-scan test does not itself walk).

### Frontend Findings

**F1 — RESOLVED (positive): Cleanup A correctly closes iter-7 audit F1.** The tradability-fetch effect (`apps/frontend/components/PriceChart.tsx:202-228`) now early-returns in `phase: "loading"` (issues no request) when `history?.epoch_anchor == null` (L207-213), and the `asOf` computation is a single line `new Date(history.epoch_anchor * 1000).toISOString()` (L216) with the `: new Date().toISOString()` wall-clock fallback removed entirely. The dependency array stays `[ticker, history?.epoch_anchor]` (L228). Confirmed via the full `git diff` — the change is exactly this guard + fallback removal + comment rewrite; the chart-creation, drawing, thesis, band-overlay, and confluence-chip logic are byte-identical. SIM safety confirmed at source: `apps/backend/app/providers/simulated.py:137` sets a non-null `epoch_anchor = CONFIG.sim_session_anchor_epoch`, so deferring the fetch is a no-op for SIM (its honest `no_bar_series_for_symbol` empty state still fires). No finding.

**F2 — IMPORTANT (gap): Cleanup A's runtime behavior was not browser-verified this iteration.** The deferred-fetch (no wall-clock transient), the SIM honest "no tradable map" empty state, and the band overlay on the AAPL 2026-06-22 historical replay (correct 2026-06-18 basis) were never exercised in a browser (Chrome unavailable — QA report `reports/qa/…-qa.md:99-104`). Coverage is the source-inspection test (`test_price_chart_confluence.py`, 9/9 green) plus prior-iteration browser evidence for the unchanged overlay; the specific new timing behavior is strictly unverified in a browser. Low-risk (narrow timing change behind a passing structural test), but genuinely `unknown` at the browser level.

### Test Findings

**T1 — RESOLVED (positive): Cleanup B genuinely strengthens the test, does not weaken it.** In `test_tradability_as_of_uses_the_watched_sessions_own_anchor_with_no_client_side_session_math` the load-bearing assertion is **inverted and widened**: old `assert "new Date().toISOString()" in as_of_computation` (fallback must be present) → new `assert "new Date().toISOString()" not in source` (fallback must be absent anywhere in the file, `test_price_chart_confluence.py:157-160`), plus two new assertions requiring the `epoch_anchor == null` guard (L163-166) and `phase: "loading"` set in **both** the guard and the pre-fetch path (L167-170). The `banned_session_math` no-lookahead guard is retained unchanged (L171-180); the other 8 tests are byte-identical. I re-ran the file: 9 passed. The dev's and reviewer's TDD red→green (stash `.tsx` → exact expected failure → restore → green) is consistent with the inverted assertion. Correct.

**T2 — IMPORTANT (gap): the entire browser test suite was skipped on the GOAL_ACHIEVED-candidate iteration.** TC-01, TC-02, TC-08, TC-09, TC-10, TC-11, TC-12 (covering J-03 rendering, Edge Report rendering, Cleanup A behavior, SIM empty state, and the J-05/J-06/J-07 regressions) were all SKIPPED — "Chrome startup failed in QA environment" (`reports/qa/…-qa.md:84-104`). The spec's DoD item 1 ("J-03 passes via browser-qa") and its TESTING REQUIREMENTS list browser tests by journey ID; none ran. Per rubric §2's worked example ("endpoint implemented, unit tests green ≠ journey passing; status: partial"), J-03 is `partial`/`unknown` at the journey level on this iteration's evidence, and J-05/J-06/J-07 were re-verified only via the full backend suite, not a browser. This is honestly disclosed (not a fabricated pass), but it is the reason GOAL_ACHIEVED cannot rest on this iteration's evidence alone.

**T3 — GAP (flagged, not fixed — QA-owned artifact): the functional test plan will false-fail J-03 if re-run verbatim.** `reports/qa/goal-tradable_wall-iter-8-test-plan.md` TC-01 and TC-04 assert the tape-state vocabulary is `{INIT, RESTING, TRACKING, TRIGGERED, RESET}`. I confirmed against source that the **only** engine vocabulary is `{buyer_control, seller_control, bid_absorption, ask_absorption, unclear}` (`grep app/engine/` returns exactly these; `RESTING|TRACKING|TRIGGERED` appears nowhere in `app/`; corroborated by `_TAPE_STATE_NAMES` at `test_price_chart_confluence.py:40` and by the pinned dataset's real `tape_timeline`). Separately, TC-04's curl queries `GET /research/setups/5c7f1a44…` — the **dataset** id (32 hex) against a route that expects a **setup/event** id (16 hex; dev cites `13e24a2f185b1299`), which would 404. Any browser/API re-verification MUST use the real vocabulary and the event id, or it will report a spurious J-03 failure. The dev already flagged both (`…-dev.md:191-202`); I confirmed them and elevate T3 to IMPORTANT for the next stage. Not silently edited here — it is a QA-owned artifact, and the correct facts are recorded above for whoever re-runs.

---

## 3. Domain Assessment

The core domain logic this iteration touches is correct and, more importantly, the real data flowing through the unchanged read paths is coherent. The pinned AAPL 2026-06-22 case, as read live by the dev, returns `reaction: "rejected"` with both forward returns negative (−0.46% @ 78 bars, −4.27% @ 234 bars) and a 426-entry `tape_timeline` drawn from the real engine vocabulary — which matches `docs/goal.md`'s own pinned narrative ("appears as `rejected` with negative forward reaction" at the ~300 wall) verbatim. That independent match between the goal's a-priori description and the endpoint's a-posteriori output is a strong signal the join/replay path is genuinely correct on real credentialed data, not merely non-empty. The honest-empty, feed-honesty (never pool `sip`/`iex`/Yahoo), immutable-data (gitignored/checksummed/split-frozen), no-lookahead (server-side `_resolve_basis` only), and keys-never-committed disciplines all hold as verified above. The one unproven domain claim is the Edge Report's populated cells (B1) — indirectly supported but unobserved.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | **None.** The implementation is correct as shipped; no CRITICAL/IMPORTANT code defect was found to fix. The open items are verification gaps (browser environment unavailable; ~10h endpoint) and a QA-artifact correction (T3), none of which is fixable by a source edit without scope creep or fabricated evidence. Fixing them by editing code would violate the verification-only scope; fabricating browser/edge-report evidence would violate rubric §6. |

Post-audit self-check: I re-ran the two touched-behavior test files myself (`test_price_chart_confluence.py` 9/9, `test_no_credential_in_artifacts.py` 4/4), independently recomputed the fingerprint, and independently enumerated the dataset corpus and scanned it for credentials from disk — every claim above cites an artifact a fresh reader can reopen.

---

## 5. Recommended Next Step

Do **not** declare GOAL_ACHIEVED on this iteration's evidence alone. Before the two-key confirm, the evaluator should require **one** of:

1. **A real browser-QA pass** of J-03 (pinned AAPL drill-in renders the populated timeline; Edge Report renders populated cells) plus the J-05/J-06/J-07 regression checks — using the **corrected** test-plan facts from T3 (real state vocabulary; event id `13e24a2f…`, not the dataset id) and a **pre-warmed** `GET /research/edge-report` (kick it off early and poll, per B1/B2), OR
2. An explicit, documented acceptance that (a) J-03's data path is verified real at the API/disk level (this audit + the dev's live read), (b) the rendering surfaces are unchanged from their iter-6/iter-7 browser-verified state and read the endpoints verbatim, and (c) the Edge Report populate-ability rests on the 11/11 resolution cross-check rather than a rendered cell — i.e., accepting a documented `partial`-to-`passing` bridge, which is a judgment call the evaluator owns, not the auditor.

Separately, a future (non-lean) iteration should add edge-report result caching so the report is usable in seconds (B2), and QA should correct the test-plan vocabulary/id errors (T3) before any re-run. The code changes themselves (Cleanup A, Cleanup B) are ready to ship as-is.

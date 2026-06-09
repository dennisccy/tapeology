# goal-i_will_be_super_rich-iter-14 Audit Report

**Date:** 2026-06-10
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS

The two reopened real-data defects are genuinely closed against **real, committed, credential-free data**: the GME 14-05-2024 SIP fixture is verifiably real captured tape (17,342 trades / 1,946 quotes over 7s, microsecond epochs, 10,808 one-share odd-lot prints, realistic ~42 bps SIP spread — not synthesizable by hand), and replaying it through the production engine resolves to `seller_control` at confidence 0.925, where the *same* replay with the override disabled stays stuck on `unclear` at 0.20 — proving the J-36 fix is load-bearing, not a vacuous test. J-37's progressive seam decouples first-data from total-window load (verified in the route, feeder, and provider code, plus a lazy-fetch counting probe), and the high-risk incremental feature rewrite is byte-identical to a full recompute through the eviction-fallback boundary (confirmed by 1,500-step adversarial differential check, zero mismatches). One IMPORTANT honesty defect (a misleading "Spread stable and narrow" observation on the wide-spread override path) was found and fixed surgically during the audit.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): Misleading "Spread stable and narrow" observation on the override path**
`apps/backend/app/engine/classifier.py:302/333` (pre-fix) — `_buyer_observations` / `_seller_observations` unconditionally appended `"Spread stable and narrow"`. On the J-36 directional-override path the move is *called precisely because* the quoted spread was wide (graded into confidence, not vetoed), so this string was factually false exactly when the override engaged — a user-facing observation (serialized at `app/serializers.py:78/96/156` and rendered in the cockpit) that contradicts the actual backend state. This is the auditor "Misleading UI" weakness and conflicts with the project principle that ambiguous data be surfaced honestly. The reviewer flagged it as a NOTE; given it sits directly on the J-36 user-facing path I rate it IMPORTANT.
**Fix applied:** threaded the already-computed `spread_wide` flag (no new state) into both observation builders; they now emit `"Wide quoted spread — call on price impact"` when the override engaged, else the unchanged `"Spread stable and narrow"`. Verified on the real GME replay: observations now read `['Seller aggression increasing', 'Price falling on sell prints', 'Wide quoted spread — call on price impact']` with state/confidence unchanged (`seller_control` / 0.925). Default `spread_wide=False` keeps every narrow-spread / absorption / sim path byte-identical. No new field, contract row, or UI surface added (spec-conformant).

**B2 — OBSERVATION: J-36 fixture's first→last move is −1.14%, the slice touches −6.1% intraday**
`apps/backend/tests/fixtures/alpaca/GME_20240514_133013_133020_sip.json` — the committed 7s slice opens at 64.29 and closes at 63.56 (first→last −1.14%), with an intraday low of 60.38 (−6.1%). The spec frames the move as ">10% / >5%". The shorter slice was chosen for committable size (a full 10-min SIP capture is ~5.6 MB / ~94k events, documented in the handoff). This does **not** weaken the gate: the engine resolves and *sustains* `seller_control` at 0.925 with a strong negative `sell_price_impact` and sell-ratio 0.928 — a genuine, sustained directional read, not a transient. The negative-guard test asserts `move_pct < -1.0`, which is loose relative to the spec headline but the authoritative gate (resolves to `seller_control` end-of-window) is met. No action needed.

**B3 — OBSERVATION: per-mode feed split is clean and vendor-confined**
`apps/backend/app/providers/adapters/alpaca.py` — `fetch_historical` / `iter_historical_chunks` read `self.historical_feed` (SIP default), `stream_live` reads `self.feed` (IEX default); `_data_feed` (`alpaca.py:442`) is the sole place the vendor `DataFeed` enum is imported/mapped. `ALPACA_FEED` override preserved and pins both modes. No vendor type leaks outward; config-owned (`config.py:223-224`). Matches the data-contract / provider-agnostic-engine constraint. No action needed.

### Frontend Findings

**F1 — N/A: no frontend changes (`Frontend Present: no`)**
`git diff --stat HEAD -- apps/frontend/` is empty — the frontend is genuinely untouched, consistent with the spec (both journeys live behind already-registered rows; no new surface, value, route, or control). UI-impact / UI-test-design / browser-QA / UX-regression are correctly N/A.

### Test Findings

**T1 — OBSERVATION: gate tests are tight and fail loudly without the real fixture**
`test_real_data_classify.py` and `test_progressive_fetch.py` both `assert GME_SIP_FIXTURE.exists()` with an explicit hard-fail message (never skip, never synthetic fallback), assert `source == "alpaca"`, `feed == "sip"`, `"REAL" in note`, and the J-36 gate asserts both `"seller_control" in states_seen` AND the *final* `snap.tape_state == "seller_control"` (so a transient under-cap tick cannot satisfy it — the sustained override read is required). The anti-goal #20 gate is genuinely enforced. No action needed.

**T2 — OBSERVATION: incremental feature equivalence independently verified**
Beyond the suite's pinned `test_features.py` values and the progressive-vs-single-shot determinism test, I ran an adversarial differential: a continuously-sliding 10s window over 1,500 random ticks (forcing the eviction fallback every step), comparing the stateful incremental `FeatureEngine` against a fresh full-rebuild for 9 features per step → **0 mismatches**. The eviction-fallback path the handoff flagged is byte-identical to a full recompute. No action needed.

---

## 3. Domain Assessment

The core domain logic is correct and the anti-goals hold under scrutiny:

- **Real-data proven with real data (anti-goal #20):** the committed fixture is unambiguously real (density ≈2,500 trades/sec, 10,808 one-share prints, 446 distinct prices, monotone microsecond epochs, realistic SIP spread). The gate tests run offline without credentials and fail loudly if the fixture is removed. This is the load-bearing constraint and it is satisfied with positive evidence, not an operator note.
- **Price impact over raw aggression / honest uncertainty:** the override predicate is the control predicate *minus* the spread term (ratio ≥ floor AND real relative impact past cutoff AND speed ≥ floor); it never fires on flat-impact tape (absorption gates keep the spread term and remain the exact complement) or weak tape. The band (`override_max_spread_multiple = 4×`) cleanly separates the real ~1.5× SIP artifact from the ~8× honest-uncertainty guards. Verified directly: override-off → `unclear`; spread-beyond-band → still vetoed (`test_spread_beyond_the_band_still_vetoes_control_honest_uncertainty`).
- **Single source of truth + determinism:** the classifier reads spread/impact/price from the canonical feature engine (no recompute); progressive chunks vs. single-shot yield byte-identical state/confidence/features (pinned to a single epoch anchor); the incremental rewrite is provably equivalent. The engine bins on its logical timeline; chunk boundaries perturb nothing.
- **No magic numbers / no secrets / vendor-confined:** all J-36/J-37 boundaries live in `config.py` with documentation; no hardcoded credentials in source or fixtures; the vendor SDK enum is confined to one adapter method.
- **Fast by design (J-37):** the route fetches only the first chunk under the vendor budget, kicks off the background fetch *before* replaying the first chunk so they overlap, and the "very high-volume" backstop now fires only when the first chunk itself cannot load — a true last-resort backstop, decoupled from total-window load.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/app/engine/classifier.py` | Thread `spread_wide` into `_buyer_observations` / `_seller_observations`; emit "Wide quoted spread — call on price impact" on the override path instead of the false "Spread stable and narrow". Default `spread_wide=False` keeps all narrow-spread / absorption / sim observations byte-identical. Full suite re-run: 283 passed, 1 skipped (zero regressions). |

---

## 5. Recommended Next Step

Proceed. The phase goal is achieved: J-36 and J-37 are closed with committed-real-data CI evidence (no live credentials), the J-01–J-35 regression floor holds byte-identical (283 passed / 1 credential-gated skip, matching the iter-13 floor + 24 new tests), and the one user-facing honesty defect found during the audit was fixed surgically with zero regression. No anti-goal violation remains. This iteration is ready for GOAL_ACHIEVED evaluation; the one audit fix (B1) is an additive honesty improvement on the same `observations` row and introduces no new surface, so it requires no re-approval.

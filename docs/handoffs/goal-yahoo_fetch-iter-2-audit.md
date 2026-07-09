# goal-yahoo_fetch-iter-2 Audit Report

**Date:** 2026-07-09
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-02's goal is genuinely achieved and independently verified: the adapter fetches all five directly-mapped era-5 timeframes plus a real, deterministically-derived `4h`, and returns three observably-distinct honest errors that never fabricate a bar. Every backend Definition-of-Done item was traced to actual code and re-proven by me (full suite exit 0, live integration re-run 5/5, all frozen invariants byte-identical, resample single-owner). The one documented gap: the required browser-regression lane for J-01/J-06 did not execute (services unreachable + Chrome MCP unavailable), so no screenshot evidence was emitted — an acceptable gap here because zero frontend/config bytes changed and the J-01 backend behaviour is independently proven live.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (no change needed): `4h` session detector is a data-driven gap heuristic, not an exchange calendar.**
`_resample_4h` (`apps/backend/app/providers/adapters/yahoo.py:116-124`) starts a new session bucket when the gap between consecutive `1h` bars exceeds `_SESSION_GAP_SECONDS = 7200` (strict `>`). I traced this against the committed fixture: bars split 4+3 (session 1) / 4+3 (session 2) / 1 (truncated session 3) exactly as claimed, with the ~18h overnight gaps (`1780342200 → 1780407000`, `1780428600 → 1780493400`) far above threshold. The documented untested edge case (a same-session halt leaving a >2h gap would falsely split a bucket) is real but rare, still produces zero fabricated bars, and is honestly logged in the dev handoff's Known Issues. GAP/observation only — the spec did not require calendar-accurate halt handling, and the live cross-check against yfinance's own native `4h` (which I re-ran, see §3) came back byte-identical. No fix.

**B2 — (no issue): error paths never write a bar.** All three exceptions in `record_bar_series` (`apps/backend/app/research/routes.py:1621-1633`) — `VendorTimeout→504`, `UnsupportedTimeframe→422`, `NoDataForWindow→422` — raise *before* the `store.record(...)` call at line 1643. Confirmed by tests asserting `bar_dir` stays empty (`test_bars_api.py:352, 331`). No fabrication, padding, or forward-fill on any path. The `UnsupportedTimeframe` branch (`yahoo.py:171-173`) raises before the lazy `yfinance` import at line 175, so a statically-unsupported timeframe makes zero vendor calls (`test_yahoo_adapter.py:169` asserts `calls == []`).

### Frontend Findings

**F1 — GAP (documented limitation): browser-regression evidence for J-01/J-06 was not captured this iteration.**
The spec's DEFINITION OF DONE item 7 and the carried iter-0 lesson (NOTES) explicitly require the browser-qa lane to "actually run and emit screenshot evidence" re-verifying J-01 (Structure renders real Yahoo candles) and J-06 (Cockpit feed badge stays "Simulated"). It did not run: `runs/goal-yahoo_fetch-iter-2/status.json` shows `"browser_checks_run": false`; `reports/phase-goal-yahoo_fetch-iter-2-ui-test-results.md` records **SKIPPED, 0/10** (frontend+backend unreachable, curl exit 7); the QA report's TC-13/14/15 are SKIPPED (Chrome MCP unavailable); the `ux-regression-reviewer` independently flagged **UX-REGRESSION-WARN / process gap Medium** for exactly this. This is a real, honestly-surfaced gap against the spec — but it does **not** compromise the phase goal because I independently verified (a) `git diff --stat -- apps/frontend/` is **empty** (UI bytes byte-identical to iter-1 where the lane did pass), so no UI regression is structurally possible from this iteration's changes, and (b) the J-01 backend behaviour (real keyless daily Yahoo fetch, `feed="yahoo"`, real bars) passes live — I re-ran it (see §3). Not fixed (GAP-level; fixing = out-of-scope environment/test-execution work, and the regression risk it guards is near-zero here).

### Test Findings

**T1 — OBSERVATION (no change needed): stale "J-01" module docstring in `test_yahoo_adapter.py:1`.**
The top-of-file docstring still frames the file as J-01 though ~half is now J-02 `4h`/taxonomy content. Cosmetic only — the reviewer already logged this as a NOTE. No behavioural impact. No fix (fixing is scope creep).

**T2 — (test-quality confirmation, not a defect): the `4h` assertions are tight and non-circular.**
`_expected_bucket` (`test_yahoo_adapter.py:70-81`) recomputes open=first/high=max/low=min/close=last/volume=sum independently with plain `max`/`min`/`sum` over explicit fixture slices — it never calls `_resample_4h` on itself. Determinism is asserted by direct equality across two calls (`test_yahoo_adapter.py:351, 378`), and the partial trailing bucket is asserted to equal a single real bar's own OHLCV, not padded (`test_yahoo_adapter.py:326-332`). These are exact-value assertions, not loose accept-either checks.

---

## 3. Domain Assessment

The core domain logic is correct and honest. I verified the `4h` resample by hand against the committed real `1h` fixture (`tests/fixtures/yahoo/AAPL_1h_20260601_20260603.json`): 15 bars → 5 buckets `[0:4],[4:7],[7:11],[11:14],[14:15]`, with bucket-0 aggregating to open `309.535…`, high `310.930…`, low `305.030…`, close `306.470…`, volume `23,743,850`, stamped at the first bar's own epoch `1780320600.0` — matching `_resample_4h`'s output. The session-aligned bucketing genuinely differs from a naive `epoch % 14400` grid (asserted at `test_yahoo_adapter.py:315`) and is the correct interpretation of the spec's "session-boundary aligned" requirement.

The anti-goal rails hold under independent inspection:
- **`4h` honestly derived** — `_INTERVAL_MAP` (`yahoo.py:72-78`) deliberately excludes `"4h"`; `fetch_bars` special-cases it into a local resample of real `1h` bars (`yahoo.py:164-169`). The handoff transparently flags that yfinance 1.5.1 *does* expose a native `"4h"` and the code deliberately does not use it — I confirmed no `"4h"` mapping and no native-interval shortcut exists.
- **No fabricated bars** — verified per B2.
- **Single source of truth** — `grep` confirms `_resample_4h`/`_FOUR_HOUR_*`/`_SESSION_GAP_*` appear only in `yahoo.py`; no second resample path in `bars.py`, `levels.py`, or any route.
- **Alpaca path untouched** — `feed = adapter.name if isinstance(adapter, YahooAdapter) else registry.config.historical_feed` (`routes.py:1640`) preserves the frozen `"sip"` stamp for non-Yahoo adapters; the frozen `test_post_records_and_registers_a_bar_series` passes unmodified (I re-ran it).
- **Frozen foundations** — `config_fingerprint` re-computed as `4d665603569b9dbf`; engine equivalence 22/22; `config.py`, `main.py`, `alpaca.py`, `providers/adapters/__init__.py`, `research/levels.py`, `research/backtests.py`, `research/strategies.py`, `research/bars.py`, `requirements.txt`, `config/install-security-policy.json`, and all of `apps/frontend/**` show **zero diff** (all re-verified by me).
- **Dependency discipline** — `yfinance==1.5.1` pinned (`requirements.txt:16`), allowlisted (`install-security-policy.json:6`); no new dependency; `base.py` diff adds only `UnsupportedTimeframe`.

Independent live re-run (mine, `TAPEOLOGY_LIVE_INTEGRATION=1`): **5 passed** — real keyless fetch of all six era-5 timeframes, live `4h == _resample_4h(live 1h)`, out-of-retention `1m` → `NoDataForWindow`, unsupported `8h` → `UnsupportedTimeframe`. The `assert len(bars) > 0` gates would have failed had no real data returned, so the pass confirms genuine network fetches — the one thing only a live call can prove (that `"1wk"`/`"1h"`/`"5m"`/`"1m"`/`"1d"` all resolve against the vendor).

Independent full-suite re-run (mine, `pytest tests/`): **exit code 0**, every progress char a `.`/`s` (no `F`/`E`), matching the reviewer's 1189/0-failed/0-error/6-skipped verification.

---

## 4. Fixes Applied During This Audit

None. No CRITICAL or IMPORTANT issues were found. Every finding is GAP- or OBSERVATION-level; per the auditor mandate these are documented as known limitations, not fixed (fixing them would be scope creep). The implementation was left byte-for-byte as the developer delivered it.

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No fixes applied |

---

## 5. Recommended Next Step

**Proceed to J-03.** The J-02 goal is fully and honestly achieved on independently-reproduced evidence; the multi-timeframe series (incl. derived `4h`) that J-03's store-first index and J-04/J-05 consume is now real and verified. Carry one item forward, do not block on it:

- **F1 (browser evidence gap):** J-05 is the iteration that actually introduces the `/structure` fetch control and Yahoo provenance badge — that is where a browser lane has genuinely new UI to screenshot and where the J-01/J-06 regression evidence should be captured for real. Ensure the J-05 pipeline run has both services reachable and Chrome MCP available so the carried iter-0 lesson ("a 'passing' without a screenshot is unevidenced") is finally satisfied end-to-end. Until then the J-01/J-06 regression remains covered by the structural zero-frontend-diff invariant plus the live backend integration test, which is adequate for a backend-only iteration but should not be relied on indefinitely.

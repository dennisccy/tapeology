# goal-yahoo_fetch-iter-4 Audit Report

**Date:** 2026-07-10
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-04 is genuinely achieved. This is a clean verify-and-lock iteration: **zero production diff**, three new hermetic tests that I re-ran and independently confirmed pass, and every frozen-foundation guarantee (byte-identical `levels.py`, single-owner compute, config fingerprint `4d665603569b9dbf`, engine equivalence 22/22) intact. The gaps are all GAP/OBSERVATION-level and spec-deferred — the headline one (mixed-feed pooling not enforced, only avoided by single-feed scoping) is explicitly out of scope and MUST NOT be fixed here because closing it requires mutating frozen `research/levels.py`, itself a critical anti-goal.

---

## 2. Findings

### Backend Findings

**B1 — GAP (documented, do-not-fix): mixed-feed pooling is avoided by scoping, not enforced**
`compute_levels` selects a symbol's series with `matching = [r for r in records if r["symbol"] == symbol]` (`apps/backend/app/research/levels.py:306`) — it pools **every** feed for that symbol. `_select_one_series_per_timeframe` (`levels.py:171-182`) dedups only *within* a (symbol, timeframe) pair by most-recent `created_utc`; across *different* timeframes it will happily mix a `feed="yahoo"` 1h series and a `feed="sip"` 1d series into the same confluence cluster. The anti-goal "Yahoo data … never pooled across feeds" is therefore satisfied for J-04 only because the tested keyless path gives AAPL a single `feed="yahoo"` feed. This is **explicitly deferred by the spec** (OUT OF SCOPE: "A feed-scoped `?feed=` filter or feed-segregated levels computation … cannot be closed without touching frozen `levels.py`; it is not in J-04's acceptance and is deferred") and logged to the assumption ledger in the spec NOTES. Correctly **not fixed**: any guard here would mutate frozen `levels.py` (fingerprint-locked, a critical anti-goal). Carry-forward for J-05+ once a symbol can accumulate more than one feed.

**B2 — OBSERVATION: no Yahoo-specific honest-empty / 422 tests added**
The honest-state coverage (test-plan TC-05–TC-08: unrecorded symbol, `as_of` before first bar, blank `symbol`, malformed `as_of`) is served by the pre-existing feed-agnostic tests `test_unrecorded_symbol_is_a_distinct_honest_state_not_an_ambiguous_empty_list`, `test_as_of_before_any_recorded_bar_is_honest_no_levels_found_not_the_prior_state`, `test_empty_symbol_is_422`, `test_malformed_as_of_is_422` (`apps/backend/tests/test_levels_api.py:323,344,370,377` — I confirmed all four exist). Acceptable: `levels.py` is vendor-neutral and byte-identical, so these states are feed-independent, and the spec framed the requirement as "confirm the existing honest states still hold on the Yahoo path", not "add Yahoo-specific error tests." No action.

### Frontend Findings

None — `Frontend Present: no`. J-04 is backend/API-verifiable; the `/structure` fetch control and provenance badge are J-05.

### Test Findings

**T1 — OBSERVATION: MCP byte-identity test seeds via `BarStore.record()` directly, bypassing the adapter/route**
`test_levels_tool_byte_identical_on_a_non_empty_live_result_on_the_yahoo_fixture` (`apps/backend/tests/test_mcp_server.py:317+`) writes the committed Yahoo captures straight through `BarStore.record(..., feed="yahoo", ...)` rather than through `POST /research/bars`, because its backend runs in a **separate subprocess** the in-process `yfinance.Ticker` monkeypatch cannot reach. This is honestly disclosed in the dev handoff, uses the exact persistence primitive the route itself calls, and mirrors the precedent of the existing PG version of this test. The load-bearing assertion — `result.content[0].text.encode("utf-8") == rest.content` against an independent `httpx.get(/research/levels)` — is a genuine byte-for-byte proof (I re-ran it: pass). No weakening of the byte-identity claim. No action.

**T2 — OBSERVATION: `coherence.md` artifact not present in `runs/goal-yahoo_fetch-iter-4/`**
Only `plan.md` + `status.json` exist there (`status.json` shows `current_step: ux_regression_complete`, `next_action: auditor`). The coherence-auditor is a separate downstream goal-mode lane; I did not run it. I did, however, independently verify the substantive condition it checks — single-owner compute, zero production diff — so the DoD's "coherence-auditor returns COHERENCE-PASS" item is materially satisfied. No action for the developer.

---

## 3. Domain Assessment

The three new tests each prove their claim, and none passes by accident:

- **Levels-on-Yahoo** (`test_get_levels_confluence_zones_exact_values_on_the_committed_yahoo_fixture`): records the two committed real Yahoo fixtures through the **real** `POST /research/bars` route (only the `yfinance.Ticker` boundary mocked), then asserts `no_bar_series_for_symbol is False`, **exactly 14 levels**, **exactly 4 zones** all class `B`, and a cross-timeframe (`{1h, 1d}`) zone with member prices `[315.20001…, 315.45001…, 315.45001…]` and `score == 12.0`. Tight exact-value assertions, not loose "something returned." I traced the member prices to real fixture rows (1d bar-2 `close=315.20001220703125` and `high=315.45001220703125`) and confirmed the class-B grade against `sr_confluence_class_a_min_timeframes=3` / `class_b_min=2` (2 distinct timeframes → B, correct). The plan's "Open Risk" (do the committed fixtures actually cluster?) is genuinely resolved — they do.
- **No-lookahead** (`test_levels_no_lookahead_holds_on_real_committed_yahoo_bars`): compares the route over the **full** 15-bar store at `as_of=T` against `compute_levels` over a store holding **only** bars ≤ T. Two guards make it non-vacuous: `assert full_body["levels"]` (result is non-empty) and `assert len(truncated_bars) < len(full_bars)` (8 post-T bars genuinely dropped at runtime). If the route leaked lookahead, the full-store result would differ from the truncated compute and the test would fail. This correctly exercises `_bars_as_of` (`levels.py:92-96`), the `ts <= as_of` truncation that runs before every detector.
- **REST==MCP** (see T1): genuine byte-for-byte identity on Yahoo-sourced data.

Core logic is sound and unchanged: `compute_levels`/`compute_confluence_zones` are the sole owners (grep returns exactly two defs, both in `levels.py`); the route (`routes.py:1789-1790`) spreads the compute dict verbatim; the MCP tool is a pure `httpx` GET proxy (`mcp/__init__.py`: `call_tool` → `_request_path` → `_proxy_get` → `client.get(path)`); and `backtests.py:630-632` **consumes** `compute_levels(...)["confluence_zones"]` rather than recomputing — single source of truth holds. Fixtures are real (float32→float64 artifacts such as `310.94000244140625`, characteristic of yfinance), committed in iter-1/iter-2, and **untouched this iteration** (`git diff HEAD -- tests/fixtures/` empty) — the "no fabricated bars" anti-goal is trivially met because no bar was created at all.

Independently reproduced this session: 3/3 new tests pass (6.05s); `test_observer_equivalence.py`+`test_profile_equivalence.py` = 22/22; `CONFIG.config_fingerprint()` = `4d665603569b9dbf`.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | None. No CRITICAL or IMPORTANT finding. Every candidate fix would either be scope creep or require mutating the fingerprint-locked, frozen `research/levels.py` — itself a critical anti-goal. Correctly left untouched. |

---

## 5. Recommended Next Step

**Proceed to J-05.** J-04's verify-and-lock is complete and evidence-backed; the era-4 levels/zones surface is now provably populated from real `feed="yahoo"` bars through its single, frozen owner with no lookahead and byte-identical REST/MCP output. Carry these forward into J-05 (all pre-flagged in the spec NOTES, none blocking here):

1. **Provision reachable frontend `:3301` / backend `:8301` + Chrome MCP before the J-05 run** — the browser lane silently no-op'd in iters 0/2/3, and J-05 is the first journey with genuinely new `/structure` UI that cannot be evidenced without a real render.
2. **Close audit carry-forwards B2 (blank `?symbol=`/`?timeframe=` → `None`) and B3 (index legacy series)** — J-05 pre-work per the iter-3 evaluator.
3. **Keep the mixed-feed pooling GAP (B1 above) visible** — the moment J-05 (or later) lets a symbol hold both a Yahoo and a non-Yahoo series over overlapping timeframes, the "never pooled across feeds" rail needs an explicit decision (feed-scoped levels), which will require a versioned path beside — never a mutation of — frozen `levels.py`.

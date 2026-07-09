# goal-yahoo_fetch-iter-1 Audit Report

**Date:** 2026-07-09
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The phase's primary goal — a keyless Yahoo Finance daily bar fetch that stores a real
`feed="yahoo"` OHLCV series through the canonical `BarStore` (append-only, checksum-verified)
and reads back byte-for-byte via `GET /research/bars/{id}` and the MCP `bars` proxy — is fully
and verifiably achieved, with tight tests and zero frozen-foundation drift (I independently
re-ran the equivalence + anti-goal suites and confirmed `config_fingerprint` is unchanged). One
minor, plan-sanctioned limitation remains (in production, `POST /research/bars` has no
operator-facing way to opt back into an Alpaca bar fetch — it always resolves to Yahoo); it
regresses nothing, is honestly disclosed, and fixing it would be scope creep, so it is
documented rather than fixed. No CRITICAL or IMPORTANT issues found; no fixes were applied.

---

## 2. Findings

### Backend Findings

**B1 — GAP (documented, not fixed): production bar-fetch path has no Alpaca opt-in**
`get_bar_fetch_adapter()` (`apps/backend/app/research/routes.py:1539-1553`) returns
`app.dependency_overrides.get(get_market_adapter, YahooAdapter)()`. Outside a test process there
is no `dependency_overrides` entry, so `POST /research/bars` (`record_bar_series`, `routes.py:1590`)
**always** resolves to `YahooAdapter` in production — there is no request parameter (e.g.
`adapter_name`) to force an Alpaca `fetch_bars`. DoD item 5 ("Alpaca stays selectable (opt-in)")
is therefore satisfied only under the execution plan's explicit re-reading of "selectable" as the
existing test-injection seam (`plan.md` Risks 1-2; the plan's own Key Test Scenarios wording).
This is acceptable and not fixed because:
- It regresses **no** passing journey. In the credentialless reality that defines Era 5, an
  Alpaca bar fetch via this endpoint previously returned `503` (no credentials); it now returns
  real Yahoo bars — strictly an improvement, not a regression.
- The Alpaca adapter is byte-identical (`providers/adapters/alpaca.py` untouched — confirmed via
  `git diff`) and remains selectable through the untouched `get_adapter()` (live/tick/search/clock)
  and `get_study_market_adapter()` (studies + historical-dataset `fetch_historical`).
- The plan explicitly deferred the operator-facing bar-fetch vendor-selection story ("era-5's
  Alpaca-bar-fetch-opt-in story is not elaborated beyond the test seam this iteration"). Adding a
  speculative REST vendor parameter would be scope creep (arguably J-05 territory) — the developer
  correctly declined it and flagged the reasoning for review.

### Frontend Findings

**F1 — OBSERVATION (no change): committed fixture placed at `fixtures/yahoo/`, not the DoD's literal `fixtures/bars/`**
Verified this deviation was the **correct** engineering call, not an oversight. The frozen test
`tests/test_bars.py::test_committed_fixture_loads_through_the_real_store_path_keyless` (line 202)
runs `BarStore(FIXTURE_BAR_DIR).list()` over the **whole** `fixtures/bars/` directory and
(line 212) blanket-asserts `meta["feed"] == CONFIG.historical_feed` ("sip") for **every** record.
A `feed="yahoo"` file dropped there would break that frozen test (`"yahoo" != "sip"`). The
developer instead mirrored the pre-existing `tests/fixtures/alpaca/` raw-vendor-capture precedent
(confirmed present: 3 files) and placed the real, live-captured 3-bar AAPL fixture at
`tests/fixtures/yahoo/AAPL_1d_20260601_20260604.json`. The frozen test is untouched (empty
`git diff`). Reviewer already blessed this as a NOTE. No action.

### Test Findings

**T1 — OBSERVATION (no change): no Yahoo-specific MCP `bars` byte-identity test**
DoD names "the MCP `bars` proxy return it byte-for-byte." The developer proved the REST half
directly (`test_bars_api.py::test_yahoo_is_the_default_bar_fetch_vendor_with_no_override` asserts
`detail.json()["bar_series"] == meta`) but added no Yahoo-specific MCP test. Verified this is
sound: `app/mcp/__init__.py:89` maps `"bars" -> "/research/bars"` and the module passes
`response.text` **verbatim** ("byte-identity by construction … no parse/re-serialize round-trip");
there is **zero** `feed`-awareness anywhere in the MCP layer, so a Yahoo-stamped series traverses
the proxy identically to any other. The existing, unmodified
`test_mcp_server.py::test_bars_tool_byte_identical_on_a_non_empty_live_list` (real uvicorn
subprocess) already proves the proxy generically. A Yahoo-specific duplicate would be redundant
coverage, not new defense. Reviewer flagged this as optional. No action.

**T2 — OBSERVATION (no change): QA report over-claims the coherence audit already ran**
The QA report (line 154) checks "✅ Coherence audit runs (no second bar store, no second `feed`
source)." Per `.claude/architecture/goal-mode.md:92`, the `coherence-auditor` runs **after** the
dispatch pipeline (after QA and after this auditor) and before the goal-evaluator, writing
`runs/goal-session-yahoo_fetch/iter-1/coherence.md` — which does not yet exist (correct for this
pipeline position; other sessions confirm the path, e.g.
`runs/goal-session-i_will_be_rich/iter-2/coherence.md`). QA asserted the outcome prematurely.
This is a QA wording nit, not a dev defect, and the **substance** the coherence audit will check
is independently verified below (single `feed` owner, no second bar store). Non-blocking.

---

## 3. Domain Assessment

The core domain logic is correct, minimal, and honest — it matches the exact J-01 scope with no
drift. Independently traced and verified:

- **Adapter (`providers/adapters/yahoo.py`).** `name="yahoo"`, keyless `is_available()` always
  `True`, `_INTERVAL_MAP == {"1d": "1d"}` (daily only — J-02 explicitly not built ahead).
  `fetch_bars` lazily imports `yfinance`, normalizes the symbol, coerces `volume` to `int`, sorts
  ascending, and returns `RawBar` tuples. Every non-bar method is honestly bars-only:
  `fetch_historical`/`get_market_clock`/`stream_live` raise `NotImplementedError`,
  `search_symbols` returns `[]`, `warm_symbol_universe` is a no-op (per the base contract). An
  unmapped timeframe **and** an empty vendor frame both return `()` — never fabricated/padded
  bars — which the existing `EmptyBarWindowError -> 422` path surfaces (no new exception type).
  This directly honors the "No fabricated bars, ever" anti-goal.
- **Vendor seam (`research/routes.py`).** A **distinct** `get_bar_fetch_adapter()` resolver is
  used **only** by `record_bar_series`; the shared `get_study_market_adapter()` (studies +
  historical-dataset recording, both needing `fetch_historical`, which Yahoo lacks) and the global
  `get_adapter()` (live/tick/search/clock) are untouched — confirmed byte-identical via `git diff`.
  This is the exact crux-risk mitigation the spec demanded; flipping the shared accessor would
  have broken studies and the live path (the "Yahoo default must not break the Alpaca path"
  anti-goal). The browser J-06 spot-check (Cockpit `/` — the highest-risk `get_adapter()` surface)
  rendered unbroken with evidence.
- **`feed` single owner.** `feed = adapter.name if isinstance(adapter, YahooAdapter) else
  registry.config.historical_feed` (`routes.py:1616`). Yahoo stamps `"yahoo"` from the adapter;
  any other adapter keeps the byte-identical `config.historical_feed` ("sip") stamp — **not**
  `adapter.name` uniformly (which would have silently renamed Alpaca's stamp and broken a frozen
  test). `grep '"yahoo"'` across `apps/backend/app/` returns **no** hits outside the adapter — the
  single-source-of-truth substance the coherence audit will confirm holds.
- **Immutability / explicit fetch.** The series is stored through the unchanged `BarStore.record`
  (append-only, double-sha256 checksum; duplicate content -> existing `409`). Fetch remains an
  explicit `POST` action; nothing ambient was added.

Independent test re-runs (not trusting the handoff): the targeted J-01 + equivalence + anti-goal
suites (`test_yahoo_adapter.py`, `test_bars_api.py`, `test_observer_equivalence.py`,
`test_profile_equivalence.py`, `test_no_execution_path.py`) **all pass**; the two equivalence
suites (22/22) prove byte-identical `default`-profile engine output; `config_fingerprint` prints
`4d665603569b9dbf` (unchanged). `yfinance==1.5.1` is genuinely installed and is a real release;
the pin carries the confined-to-adapter comment and `"yfinance"` is in the `python.allowlist`.
QA independently reproduced the full suite (1163 passed / 2 skipped in 124.96s). Browser evidence
(`ui-test-results.md` + screenshots TC-13..16 + studies) exists in the QA evidence directory,
closing the iter-0 no-evidence gap.

---

## 4. Fixes Applied During This Audit

None. No CRITICAL or IMPORTANT issues were found. The single GAP (B1) and the OBSERVATIONs
(F1, T1, T2) are documented limitations that do not compromise the phase goal; fixing any of them
would be scope creep.

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No fixes applied |

---

## 5. Recommended Next Step

**Proceed.** J-01 is genuinely achieved: keyless Yahoo daily bars flow through the canonical store
and read back byte-for-byte via REST + MCP, the live keyless fetch was exercised under the
integration marker (dev handoff states it passed), the frozen foundations are byte-identical
(`config_fingerprint` `4d665603569b9dbf`, equivalence 22/22, Alpaca adapter untouched), and the
browser regression lane ran with evidence. Let the downstream `coherence-auditor` produce
`iter-1/coherence.md` (its substance — single `feed` owner, no second bar store — is already
verified) and the goal-evaluator record the verdict.

Carry two notes into J-02–J-05 planning:
- **B1 (production Alpaca opt-in on the bar-fetch endpoint):** if the product ever needs an
  operator to force an Alpaca bar fetch through `POST /research/bars`, that selector belongs in a
  future iteration's scope — not retrofitted here.
- **Timeframe scope:** `YahooAdapter` maps only `"1d"`; a production request for any other
  registered timeframe currently returns `422 "no bars"` (sanctioned Risk-4 behavior). J-02 owns
  the full `1w/4h/1h/5m/1m` table, the `4h` resampler, and the richer unsupported-timeframe /
  out-of-retention error taxonomy.

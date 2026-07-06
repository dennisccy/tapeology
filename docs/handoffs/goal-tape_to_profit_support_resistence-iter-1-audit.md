# goal-tape_to_profit_support_resistence-iter-1 Audit Report

**Date:** 2026-07-06
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS

J-01 (the multi-timeframe bar store) is genuinely and completely delivered: an immutable,
double-checksummed `BarStore` mirroring `research/datasets.py`, a vendor-neutral `RawBar` +
`fetch_bars` seam, three `/research/bars*` routes, a read-only MCP `bars` proxy, and a real
(never-fabricated) keyless committed fixture. Every DEFINITION OF DONE item is satisfied in code
that I traced and re-ran myself, and every critical anti-goal holds — most importantly the frozen
`default` profile, which I confirmed by live-computing its fingerprint to the pinned
`4d665603569b9dbf`. No critical or important gaps remain; the only findings are two spec-sanctioned
GAPs the developer already disclosed and two observations. No fixes were warranted.

---

## 2. Findings

### Backend Findings

**B1 — GAP (disclosed): unknown/untradable symbol is indistinguishable from a genuinely empty window**
`fetch_bars` has no tradability pre-flight (unlike `fetch_historical`'s `_require_tradable`), so an
unknown symbol and a real empty window both return `()` → `EmptyBarWindowError` → 422 "no bars in
the requested window" (`app/research/bars.py:233-234`, `app/research/routes.py:1597-1598`). The spec
never asks bars to distinguish these, and the developer flagged it explicitly (dev handoff, Known
Issue #3). The failure is honest and nothing is fabricated. No fix — out of scope, spec-permitted.

**B2 — GAP (disclosed): a window entirely inside the recency embargo returns the same 422 as an empty window**
`_bar_fetch_end_clamp` short-circuits an entirely-embargoed window to `()` with no vendor call
(`app/providers/adapters/alpaca.py:515-517`), which then surfaces as the same `EmptyBarWindowError`
→ 422 as B1. Honest (no fabrication), disclosed in the handoff. No fix — the DoD requires no
distinct embargo state, and inventing one would be scope creep.

**B3 — OBSERVATION: the window fields are outside the content checksum (by design)**
`_content_checksum` covers `symbol + timeframe + feed + bars` but not `window_start_utc` /
`window_end_utc` (`app/research/bars.py:113-117`), so the request window does not participate in
duplicate detection — dedup is by actual candle content, which is correct (the window is a request
label; the data window is derived from the candles). The window fields are still tamper-protected by
the whole-file checksum (`bars.py:158`). Correct-by-design; noted only for completeness.

### Frontend Findings

None. `Frontend Present: no`. I verified `git diff -- apps/frontend/` is empty **and** that there
are no untracked frontend files (`git status --short -- apps/frontend/` empty). J-07's cockpit leg
is correctly guarded by the equivalence suite + zero-frontend-diff, per the iteration's lessons.md.

### Test Findings

**T1 — OBSERVATION: the content-checksum-only failure mode is never isolated in a test**
Both checksums are recomputed on every load (`app/research/bars.py:158` whole-file, `:170-175`
content), but every corruption test mutates a bar value **without** recomputing `file_checksum`
(`test_bars.py:142`, `:157`; `test_bars_api.py:200`), so the whole-file check at `:158` always fires
first and the content-checksum branch at `:170-175` is never the raiser under test. The content
checksum's unique value — catching a tamper that recomputed the file checksum but not `meta.checksum`
— is therefore unexercised. This is defense-in-depth that mirrors the `datasets` precedent exactly;
both checksums genuinely run on every healthy load. Not a correctness defect. No fix (adding a test
for a defense-in-depth branch is not required by the DoD and would be discretionary).

---

## 3. Domain Assessment

The core domain logic is correct and faithfully mirrors the `research/datasets.py` precedent the spec
mandated, which keeps the single-source-of-truth and honest-failure anti-goals satisfied by
construction:

- **Immutable + verified-on-load.** `record()` is the only write path in the module (confirmed: no
  `update`/`delete`/`unlink`/`rmtree`/`save` anywhere in `bars.py`), it refuses already-registered
  content via a content-checksum scan (`BarSeriesAlreadyRegistered`), and every read goes through one
  `_load` that recomputes both checksums. Corrupt/unparseable/shape-broken files raise the explicit
  `BarSeriesIntegrityError`; `list()` surfaces a corrupt file in `integrity_errors` rather than
  hiding or serving it.
- **No fabrication.** Empty fetched window → `EmptyBarWindowError` → 422, nothing written (verified
  by test asserting the bar dir stays empty). Missing credentials → 503 (never a synthesized series).
  The committed fixtures are REAL Alpaca PG data (1h ×9, 1d ×5) captured through the actual
  `fetch_bars` path, and I confirmed they contain no credential-like strings.
- **Frozen archived behavior.** The four new `Config` fields (`bar_dir`, `bar_timeframes`,
  `bar_recency_delay_seconds`, `bar_rate_limit_per_minute`) are all in the `config_fingerprint`
  `excluded` set (`config.py:1256-1267`), which is the correct call — none shapes any tape/backtest/
  study computation. I live-computed `Config().config_fingerprint()` → `'4d665603569b9dbf'`, exactly
  the pinned value, proving the `default` profile did not drift.
- **Single source of truth / read-only MCP.** Routes serve the store's dict verbatim (a test asserts
  `list()[0] == posted` — no recompute at read); the MCP `bars` tool is a generic `response.text`
  proxy of `GET /research/bars`, byte-identical by construction and proven on a non-empty seeded
  list. No mutating MCP tool was added.
- **Persistence scoped.** Only `app/research/routes.py` imports `BarStore`; nothing in the
  watch/stream/live path touches it, so there is no ambient recording.
- **Adapter-seam safety.** Adding `fetch_bars` to the `@runtime_checkable` `MarketDataAdapter`
  Protocol is safe: there are no runtime `isinstance(x, MarketDataAdapter)` checks (only type
  annotations), and both concrete adapters (`AlpacaAdapter`, `FakeAdapter`) implement it. The test
  `test_bar_timeframe_vendor_mapping_covers_every_configured_timeframe` guards against a config
  timeframe missing from the vendor mapping (which would otherwise `KeyError`).
- **No escape hatch in test wiring.** The route resolves the adapter via
  `get_study_market_adapter()`, which reads `app.dependency_overrides.get(get_market_adapter, ...)`
  (`routes.py:1218-1221`), so the API tests genuinely exercise the injected `FakeAdapter` (including
  the 503 path via `available=False`) rather than a real vendor.

**Independent verification I ran (not taken from the handoff):**
- `pytest test_bars.py test_bars_api.py test_profile_equivalence.py test_observer_equivalence.py` →
  **50 passed**.
- `pytest test_mcp_server.py -k "bars or backend_down"` → **2 passed** (byte-identity + backend-down).
- `pytest test_real_data_gate.py` → **35 passed** (vendor-confinement gate; `config.py` names no
  vendor SDK — only pre-existing `iex` feed values remain).
- `Config().config_fingerprint()` → `'4d665603569b9dbf'` (== pinned).
- `git diff -- apps/frontend/` empty; no untracked frontend files.
- Scope check: exactly three `/bars` routes added; **no** `/research/levels` or `/research/strategies`
  routes leaked in (J-02–J-06 remain unbuilt, as scoped).

**Note on the committed fixture (verified, not a defect):** the fixture files under
`tests/fixtures/bars/` are currently untracked (`??`) — but so is the *entire* iteration (`bars.py`,
`test_bars.py`, etc.), because the release/commit step runs after this audit. They are **not**
gitignored (`git check-ignore` returns nothing; `.gitignore` only ignores `.data/`), and the
identical `tests/fixtures/datasets/*.json` precedent is committed, so the release step will commit
them exactly the same way. The DoD's "committed AND keyless AND exercised" invariant will hold on the
resulting commit; the keyless test loads them with no credentials today.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | None. No critical or important issue was found; all findings are GAP/OBSERVATION-level and either spec-sanctioned or defense-in-depth. Applying changes would be scope creep. |

---

## 5. Recommended Next Step

**Proceed to release, then build J-02 next.** J-01 is the era's designated unblocker and is complete,
frozen-safe, and honest. When J-02 (deterministic S/R level detection) consumes the stored bar
series, carry forward two disclosed notes from this iteration: (1) the monthly-bar vendor depth limit
observed in the capability probe (data only reaches back to 2016-01-01 on this plan regardless of the
requested start), and (2) that an unknown symbol and an empty/embargoed window both present as the
same 422 — if J-02 ever needs to tell a user *why* a level set is empty, a symbol-tradability
distinction on the bar-fetch path would be the place to add it. Neither blocks release now.

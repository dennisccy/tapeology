# goal-yahoo_fetch-iter-4 Dev Handoff

**Phase:** goal-yahoo_fetch-iter-4
**Date:** 2026-07-10
**Agent:** developer
**Status:** complete

## Context: this iteration's work was found already drafted, uncommitted

Before touching anything, `git status` showed `apps/backend/tests/test_levels_api.py` and
`apps/backend/tests/test_mcp_server.py` already modified in the working tree (uncommitted), with
content that matches this iteration's plan almost exactly (the same three tests the plan
specifies, same docstrings referencing "independently confirmed via a standalone probe before
this test was written"). No review/QA/audit report exists for this phase and HEAD (`49b73c9`) has
no trace of these changes, so this is very likely leftover from an interrupted prior attempt at
this same iteration (this session has hit interactive-quota throttling before — see the project's
own memory notes). Per the developer agent's initial-build mode, I did not blindly trust this: I
verified every claim below myself (ran the tests, checked the coherence lock, ran the full suite,
verified the live app) before treating it as done. I did not need to write new production or test
code — the existing draft was correct and complete against the plan's three required tests, plus I
added the parts that were still missing (the coherence-lock verification, the full regression run,
the live-app check, and this handoff).

## What Was Built

This is a **verify-and-lock** iteration (per the plan) — no production code was touched.
`research/levels.py` (frozen, vendor-neutral by construction) already computed real S/R levels and
A/B/C confluence zones from whatever bars are in the `BarStore`, regardless of `feed`. The three
new hermetic tests below prove that the same frozen module now populates real, non-empty output
once real `feed="yahoo"` bars are stored — closing J-04.

- **`test_get_levels_confluence_zones_exact_values_on_the_committed_yahoo_fixture`**
  (`test_levels_api.py`) — records the two already-committed real Yahoo fixtures
  (`AAPL_1d_20260601_20260604.json`, 3 daily bars; `AAPL_1h_20260601_20260603.json`, 15 hourly
  bars) through the real `POST /research/bars` route (only the `yfinance.Ticker` boundary is
  mocked — `YahooAdapter`, `BarStore.record`, and the route all run for real), then asserts `GET
  /research/levels?symbol=AAPL&as_of=2026-06-05T00:00:00Z` returns `no_bar_series_for_symbol:
  false`, exactly 14 levels, and 4 confluence zones (all class `B`), including one cross-timeframe
  (1h+1d) zone with an exact `score` of 12.0. **This resolves the plan's "Open Risk": the two
  existing fixtures DO already cluster into qualifying zones — no richer fixture was needed.**
- **`test_levels_no_lookahead_holds_on_real_committed_yahoo_bars`** (`test_levels_api.py`) —
  re-proves the existing lookahead-free guarantee on real Yahoo data: levels computed at an `as_of`
  truncated partway through the 15-bar hourly fixture are byte-identical whether computed via the
  real route (full series stored) or via `compute_levels` directly over a store holding only the
  bars at-or-before that instant.
- **`test_levels_tool_byte_identical_on_a_non_empty_live_result_on_the_yahoo_fixture`**
  (`test_mcp_server.py`) — the REST==MCP byte-for-byte proof, re-run on real Yahoo data seeded
  directly into a live subprocess backend's bar directory via `BarStore.record()` (this test's
  backend runs in a separate subprocess, so the in-process `yfinance.Ticker` monkeypatch used
  above isn't reachable here — the same `shutil.copy`-into-`bar_dir` precedent the existing PG
  version of this test uses). Confirms the MCP `levels` tool and `GET /research/levels` return
  byte-identical JSON on Yahoo-sourced data.

## Coherence-lock verification (read/diff check, not new code)

- `git diff` against HEAD shows **zero changes** to `apps/backend/app/research/levels.py`,
  `routes.py`, `apps/backend/app/mcp/__init__.py`, `config.py`, `research/backtests.py`,
  `research/strategies.py`, `research/bars.py`, or `providers/adapters/` — confirmed directly via
  `git diff --stat` on each path.
- `grep -rn "def compute_levels\|def compute_confluence_zones" apps/backend/app/` returns exactly
  two hits, both in `research/levels.py` — the sole owner, no second implementation anywhere.
- Every other file referencing `confluence_zones`/`compute_level*` (`config.py`, `backtests.py`,
  `routes.py`) does so only via a comment or an import+call of the same single function — verified
  by reading each hit directly.
- `routes.py::get_levels` calls `compute_levels(...)` and spreads its dict verbatim; the MCP
  `levels` tool (`app/mcp/__init__.py`) is a pure `httpx` GET proxy of the REST route (no
  parallel computation). Single source of truth holds.

## Files Changed

- `apps/backend/tests/test_levels_api.py` -- MODIFIED (+156 lines). Added the two Yahoo-fixture
  levels/zones/no-lookahead tests above, plus their fixture-loading helpers
  (`_load_yahoo_fixture`, `_yahoo_fixture_dataframe`, `_install_fake_yahoo_ticker`,
  `_record_yahoo_fixture`), mirroring the established pattern in `test_bars_api.py`.
- `apps/backend/tests/test_mcp_server.py` -- MODIFIED (+55 lines). Added the REST==MCP
  byte-for-byte test on Yahoo data described above.
- No fixture files were added — the two pre-existing `tests/fixtures/yahoo/*.json` files already
  qualify for a confluence zone (see "Open Risk" resolution above); they were not modified.
- `docs/handoffs/goal-yahoo_fetch-iter-4-dev.md` -- NEW (this file).
- **Zero diff** (confirmed): `apps/backend/app/research/levels.py`, `apps/backend/app/research/routes.py`,
  `apps/backend/app/mcp/__init__.py`, `apps/backend/app/config.py`, `research/backtests.py`,
  `research/strategies.py`, `research/bars.py`, the tape engine, the Alpaca adapter.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_levels_api.py tests/test_mcp_server.py -v`
Result: **12 passed** (`test_levels_api.py`, includes the 2 new Yahoo tests), **3 passed** (levels-related
subset of `test_mcp_server.py`, includes the 1 new REST==MCP Yahoo test) — all new tests pass.

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q --junit-xml=<path>`
Result: **1206 tests, 0 failures, 0 errors, 6 skipped** (junit-xml summary; the plain-text `-q`
summary line was not written to stdout in this sandbox for reasons unrelated to test content —
the junit-xml report is authoritative). This is the iter-3 baseline (1203 passed / 6 skipped / 0
failed) plus this iteration's 3 net-new tests — **zero regressions**.

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_observer_equivalence.py tests/test_profile_equivalence.py -v`
Result: **22 passed** (J-06's engine-equivalence guard).

Command: `cd apps/backend && .venv/bin/python -c "from app.config import CONFIG; print(CONFIG.config_fingerprint())"`
Result: `4d665603569b9dbf` (unchanged from iter-1/2/3, as expected — `config.py` has a zero diff).

### Live verification against the real running app (not just tests)

This iteration adds no new external integration (no new adapter, no new vendor call) and the
plan's Testing Requirements mark a live check as optional/not required for this journey. I still
verified live, beyond the hermetic fixture tests, using the real app:

- Started the real app (`bash scripts/dev.sh`; backend `:8301`, frontend `:3301`). Both came up
  cleanly (`Application startup complete`, Next.js `Ready in 1229ms`), health-checked 200 on both.
- `GET /research/bars` against the **real, pre-existing `.data/bars/` directory** (populated
  live in iterations 1-3) showed 8 real recorded series, all `feed="yahoo"`, `integrity_errors: []`.
- `GET /research/levels?symbol=AAPL&as_of=<now>` against that same real data returned
  `no_bar_series_for_symbol: false`, **1094 real levels** and **63 real confluence zones** (a mix
  of A/B/C classes) — a much richer live confirmation than the committed-fixture tests, proving
  J-04 end-to-end on the actual running application, not only in test fixtures.
- Stopped both services, restarted them from a clean state, re-confirmed both healthy with no
  port conflicts (backend and frontend rebind their deterministic hashed ports, `8301`/`3301`,
  cleanly both times).
- Did **not** add a new `@pytest.mark.integration` test hitting `/research/levels` against the
  live Yahoo network (optional per the plan; the existing `test_yahoo_live_integration.py` from
  iter-1/2 already integration-covers the bars-fetch path — it does not call `/research/levels`,
  so a genuinely new live-network levels test remains a small, explicitly-optional gap, not a
  requirement this iteration).
- Confirmed outbound network reachability to Yahoo (`query1.finance.yahoo.com` answered, albeit
  with a `429` rate-limit at the moment I checked) — noted here for transparency, not exercised
  further since it is not required.

All server processes were killed before finishing.

## Known Issues

- **`scripts/dev.sh`'s simple `pkill`/PID-based stop does not reliably kill the full `next dev`
  child process tree** (same finding iter-3's handoff already flagged, independently reproduced
  here): a plain `pkill -f "next dev"` left the descendant `next-server` process (and its
  `npm exec` / `sh -c` / `node` ancestors) bound to port 3301. I killed the specific child PIDs
  directly to get a clean stop before restarting/finishing. This is a pre-existing gap in
  `scripts/dev.sh` itself (not touched this iteration, out of scope) — flagged again since it will
  keep surprising future dev/QA cycles that rely on the script's own Ctrl+C handler.
- **No new `integration`-marked live test for `/research/levels`.** As noted above, this is
  explicitly optional per the plan/spec and was not added; the acceptance is fully covered by the
  hermetic committed-fixture tests plus the manual live-app check described above.
- The feed-segregation interpretation from the phase spec's NOTES stands unchanged: this iteration
  does not add a mixed-feed guard (would require touching frozen `levels.py`); out of scope per
  the spec's own assumption ledger.

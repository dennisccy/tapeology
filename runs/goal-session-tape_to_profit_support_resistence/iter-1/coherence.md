# Iteration 1 — Coherence Audit

**Iteration:** goal-tape_to_profit_support_resistence-iter-1
**Date:** 2026-07-06
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Row 38 — Bar series (symbol, timeframe, UTC window, feed, bar count, checksum, OHLC candles) | OK | Single owner: `apps/backend/app/research/bars.py:128` (`BarStore`), sole mutation `bars.py:220` (`record`), sole verified reads `bars.py:186`/`bars.py:193` (`get`/`list`). Single production call site `apps/backend/app/research/routes.py:1528-1529` (`get_bar_store()`). Served by `POST /research/bars` (`routes.py:1535-1536`), `GET /research/bars` (`routes.py:1602-1603`), `GET /research/bars/{id}` (`routes.py:1612-1613`) + MCP `bars` (`apps/backend/app/mcp/__init__.py:89` static-path entry, `:174` tool decl) — a generic byte-identical proxy through the existing `_STATIC_PATHS` dispatch (`mcp/__init__.py:262-263`), not a second implementation; live-list byte-identity asserted by the new `test_bars_tool_byte_identical_on_a_non_empty_live_list` (`apps/backend/tests/test_mcp_server.py:263-641`). |
| Rows 1–37 (era 1–3 contract) | OK — untouched | No modified line in this diff falls inside any existing registered value's computing module or serving endpoint; the only edits to shared files (`config.py`, `mcp/__init__.py`) are pure additions (new fields / new tool entry), verified by re-reading the surrounding hunks. |
| New value introduced outside the contract | N/A | None found — bar-series fields match row 38's already-drafted definition exactly; no synonym/re-derivation of an existing value appeared. |

Supporting checks performed: grepped the whole `apps/backend/app` tree for every other `BarStore(` call site (only `routes.py:1532`, plus test/fixture-generator call sites under `tests/` and `scripts/generate_bar_fixtures.py`, all constructing the same class) — confirmed a single writer. Grepped for `levels`/`confluence`/`structure_tape` inside the changed files — none present, confirming no premature encroachment into rows 39–43's territory. Confirmed the new route reuses the pre-existing `get_study_market_adapter()` accessor (`routes.py:1218`, already used at `:1315`/`:1461`) rather than instantiating a second adapter path. Confirmed the four new config fields (`bar_dir`, `bar_timeframes`, `bar_recency_delay_seconds`, `bar_rate_limit_per_minute`) are added to the `config_fingerprint` exclusion set (`config.py:1256,1265-1267`) — this protects, rather than threatens, the frozen-`default` single-source-of-truth invariant.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `POST/GET /research/bars*` + MCP `bars` | OK — no nav path required | Blueprint IA table (`runs/goal-session-tape_to_profit_support_resistence/state/blueprint.md`, row "J-01 multi-timeframe bar store … machine") designates this journey a machine-only surface with no nav home, mirroring the existing `datasets`/`backtests`/`pnl_ledger` machine rows. Confirmed zero frontend change: `git diff b576c8f60377d4ad03c366da2073f1cd0fb49f0e --stat -- apps/frontend/` returned empty output, and `reports/phase-goal-tape_to_profit_support_resistence-iter-1-ui-surface-map.md` states "N/A — Backend-only phase … No UI surfaces affected." Nothing user-facing shipped, so no nav/sidebar/router file needed a new link. |

No new page, panel, or route was introduced this iteration, so duplicate-home and parallel-shell checks have nothing to test against.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Naming proximity, not a violation.** The codebase now carries two distinct "bar" concepts: the pre-existing intra-second live-tape OHLC bar (`?bar=` / `CONFIG.history_bar_sizes`, `app/engine/history.py`, `app/serializers.py`, unmodified this iteration) and this iteration's new calendar-timeframe bar series (`?timeframe=` / `CONFIG.bar_timeframes`, `app/research/bars.py`). The diff itself is careful to disambiguate — distinct field names, distinct endpoints, and an explicit comment at `config.py:1027-1035` calling out the two are "an unrelated concept that must not be conflated or collide." No action needed now (machine-only surface, no shared UI label yet); worth keeping in mind if/when a future levels/bars UI view is ever built, so a user-facing label doesn't quietly conflate the two.

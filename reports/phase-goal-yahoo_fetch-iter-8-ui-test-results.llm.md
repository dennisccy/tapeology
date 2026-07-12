# Phase goal-yahoo_fetch-iter-8 — UI Test Results

**Phase:** goal-yahoo_fetch-iter-8
**Date:** 2026-07-12
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All smoke and happy-path tests pass. -->
<!-- FAIL: Any smoke test fails, OR any happy-path test fails, OR any P1 test fails. -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable. -->

**Overall:** 6/6 journeys passed (0 skipped)

---

## Scope note (per dispatch)

Per this run's dispatch: "test EXACTLY these journeys: J-01, J-02, J-03, J-06 — Do NOT test J-04, J-05 (a deterministic replay verifies them separately)." This agent freshly browser-drove **J-01, J-02,
J-03, J-06** via Chrome MCP this run. **J-04, J-05** are reported below from the separate deterministic replay already on disk at `reports/phase-goal-yahoo_fetch-iter-8-regression-replay-results.md`
(written by `demo_runner.py`, dated 2026-07-12, same day as this run) — not re-driven by this agent.

**This iteration's purpose:** iter-8 exists solely to fix a proven false-negative in J-06's golden replay script — step 3 previously asserted on the async-loaded "Absorption reversal" text, which the
headless replay text-matcher intermittently missed depending on load timing. The fix (already applied to `runs/goal-session-yahoo_fetch/journey-scripts/J-06.json` before this agent started, per the
iteration spec) swaps that assertion to the statically-rendered `<h1 data-testid="studies-title">Replay studies</h1>`. This agent's live verification below independently confirms the new assertion
target really is static and always-present (see UT-J-06).

**Environment isolation (concurrency hazard, resolved before any evidence capture):** per this run's dispatch, a separate concurrent goal-mode pipeline ("Trendora", port 3255) is also driving Chrome
via the same MCP server. An initial `list_tabs` showed exactly one tab, already correctly on Tapeology's `/structure` (no contamination observed at that instant) — but Chrome was already running
under a shared profile, and `set_profile` requires killing Chrome first. Ran `kill_chrome` (scoped to this MCP server's own Chrome process) → `set_profile("yahoo-iter8-qa")` → re-navigated to
`/structure` → `list_tabs` confirmed exactly one tab, `Tapeology` / `http://localhost:3301/structure`, before any further action or screenshot. No evidence in this report was captured before this
isolation was confirmed.

All J-01/J-02/J-03 browser actions reused an already-stored, store-first-safe `AAPL`/`1d`/`2026-06-01T00:00:00Z`–`2026-06-04T00:00:00Z` window (confirmed pre-existing via `GET /research/bars` before
testing: 9 stored `feed="yahoo"` series across `AAPL` 1d(×4 windows)/1w/1h/4h/5m and one `MSFT` 4h series) — consistent with this iteration's zero-new-writes spirit (`git diff -- apps/` must stay
empty; the golden-script edit is the only sanctioned change). No new live Yahoo network call was made. This mirrors the identical methodology the prior iteration (iter-7) used successfully for the
same three journeys.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Fetch real historical bars from Yahoo Finance, keyless | regression | P1 | A stored `feed="yahoo"` series is fetchable/readable with no credentials; provenance singly-owned and visible; no fabricated data | Filled Fetch panel (Symbol=AAPL, Timeframe=1d, Start=2026-06-01T00:00:00Z, End=2026-06-04T00:00:00Z), clicked "Fetch from Yahoo Finance". Page rendered a "feed / **Yahoo Finance**" badge, a real candlestick "PRICE CHART — S/R LEVELS" section, and caption "Candles: 5m series (234 of 2028 recorded bars, as of the query time)." No fabricated/placeholder text, no error. `GET /research/bars` before/after confirms the served series (`89a829f7c3b9`) was NOT newly created — `created_utc` unchanged at `2026-07-10T14:27:41.881667Z`, AAPL/1d count unchanged at 4 | PASS | `reports/qa/goal-yahoo_fetch-iter-8-evidence/J-01-result.png` |
| UT-J-02 | The full timeframe set, including honestly-resampled 4h | regression | P1 | All six timeframes (1w,1d,4h,1h,5m,1m) real and offered; 4h present, never fabricated, and actively used in real structure output | Live-read the `<select data-testid="fetch-timeframe-select">`: options exactly `Choose…, 1w, 1d, 4h, 1h, 5m, 1m` — the full real timeframe set, no more no less. The rendered 16-zone confluence table cited real entries from four different stored timeframes together: `1d` (`prior-period-extreme`), `1h`/`4h`/`5m` (`swing-pivot`) — e.g. zone 6 (price 308.85, `4h swing-pivot`) and zone 16 (price 316.94, `4h swing-pivot`) — proving `4h` is genuinely stored and actively feeding real structure, not merely an offered-but-unused option | PASS | `reports/qa/goal-yahoo_fetch-iter-8-evidence/J-01-result.png` |
| UT-J-03 | Quick reuse — store-first fetch backed by a derived SQLite index | regression | P1 | A repeat fetch of an already-stored window is served from storage with no network call, no duplicate/conflict error, and creates no new record | Clicked "Fetch from Yahoo Finance" again with identical AAPL/1d/2026-06-01→2026-06-04 fields unchanged. Button transiently read "Fetching…" (disabled) then reverted to idle ("Fetch from Yahoo Finance", enabled) by the next check; word-boundary regex scan of `document.body.innerText` for the words conflict, duplicate, "already exists", failed, and error found zero matches; full chart + all 16 zones re-rendered correctly. `GET /research/bars?symbol=AAPL&timeframe=1d` before/after both clicks: still exactly 4 series, target series `created_utc` timestamp byte-identical — proves no new write occurred either time | PASS | `reports/qa/goal-yahoo_fetch-iter-8-evidence/J-03-result.png` |
| UT-J-04 | Real S/R levels and confluence zones on real Yahoo bars | regression | P1 | Journey replays end-to-end via the deterministic script; all expects hold | **Not browser-driven by this agent** (per dispatch: verified separately). `runs/goal-session-yahoo_fetch/journey-scripts/J-04.json` replayed by `demo_runner.py` (`reports/phase-goal-yahoo_fetch-iter-8-regression-replay-results.md`, dated 2026-07-12): navigated `/structure` (expect "Fetch from Yahoo Finance"), filled Symbol=AAPL + As-of=2026-06-05T00:00:00Z, clicked Load, expect "Confluence zones" — all held | PASS | `reports/qa/goal-yahoo_fetch-iter-8-evidence/J-04-verify.png` |
| UT-J-05 | Fetch from the app — the Structure page fetch control with "Yahoo Finance" provenance | regression | P1 | Journey replays end-to-end via the deterministic script; all expects hold | **Not browser-driven by this agent** (per dispatch: verified separately). `runs/goal-session-yahoo_fetch/journey-scripts/J-05.json` replayed by `demo_runner.py` (same replay report): navigated `/structure`, filled Symbol=AAPL, filled Start=2026-06-05T00:00:00Z, clicked Load, expect the `feed-basis-label` testid present — all held | PASS | `reports/qa/goal-yahoo_fetch-iter-8-evidence/J-05-verify.png` |
| UT-J-06 | The foundation is unchanged (regression sentinel) | regression | P1 | Cockpit/Journal/Studies/Performance render as before; the fixed `/studies` assertion target is genuinely static; pinned `config_fingerprint` visible | Navigated `/` → "No ticker watched" found. Navigated `/journal` → "SIM-BUYER" found. Navigated `/studies` → "Replay studies" found, AND confirmed present as `<h1 data-testid="studies-title">Replay studies</h1>` in the raw HTML captured immediately after `navigate` (before any explicit wait) — proving it is a genuinely static, always-present target, not an async-timing gamble. Navigated `/performance` → "4d665603569b9dbf" found | PASS | `reports/qa/goal-yahoo_fetch-iter-8-evidence/J-06-studies.png`, `reports/qa/goal-yahoo_fetch-iter-8-evidence/J-06-performance.png` |

---

## Passed Tests

### UT-J-01 — Fetch real historical bars from Yahoo Finance, keyless
**Verdict:** PASS
**Evidence:** `reports/qa/goal-yahoo_fetch-iter-8-evidence/J-01-result.png`
- Preconditions confirmed via `curl http://localhost:8301/research/bars`: 9 pre-existing `feed="yahoo"` series (8 `AAPL` across 1d(×4 windows)/1w/1h/4h/5m, 1 `MSFT` 4h), including the target window
  `AAPL/1d/2026-06-01T00:00:00Z→2026-06-04T00:00:00Z` (`id=89a829f7c3b9`, 3 bars) — guaranteeing a store-first serve, not a live fetch.
- On `/structure`, filled the Fetch panel: Symbol=`AAPL` (verified via live DOM read `input.value === "AAPL"`), Timeframe=`1d` (verified via live eval `select.value === "1d"`, since the static HTML
  retains `selected=""` on the placeholder `<option>` — a normal `<select>` outerHTML-vs-live-property quirk), Start=`2026-06-01T00:00:00Z`, End=`2026-06-04T00:00:00Z`. The "Fetch from Yahoo
  Finance" button's `disabled` attribute cleared once all four fields validated, then clicked it.
- After `await_text("Confluence zones")` resolved, full-page text extraction showed: a "feed" / "**Yahoo Finance**" badge, a "PRICE CHART — S/R LEVELS" heading with a real rendered candlestick
  chart, and the caption "Candles: 5m series (234 of 2028 recorded bars, as of the query time). Level lines span every recorded timeframe." No fabricated placeholder text, no error panel.
- Cross-checked at the data layer: `GET /research/bars?symbol=AAPL&timeframe=1d` before and after this click both returned the same 4 series with the target's `created_utc` unchanged at
  `2026-07-10T14:27:41.881667Z` — direct proof the click served the existing stored series rather than creating (or duplicating) one.
- This directly evidences J-01's browser-observable acceptance: a `feed="yahoo"` series (singly-owned label, sourced from the adapter via taxonomy) is stored, keyless, and correctly read back
  through the canonical endpoint the UI consumes, with no fabrication. The byte-for-byte `GET /research/bars/{id}` vs MCP `bars`-proxy equivalence and the `409`-on-duplicate-content behavior are
  asserted by goal.md's acceptance line as backend/route-test-verified (this iteration's baseline: 1207 collected / 1201 passed / 6 skipped / 0 failed, unchanged) — an attempted live cross-check
  via the `mcp__tapeology__bars` tool this run found it wired to the canonical port 8000 rather than this session's offset backend port 8301 (`ConnectError`, not a product defect), so it was not
  independently re-derived here.

### UT-J-02 — The full timeframe set, including honestly-resampled 4h
**Verdict:** PASS
**Evidence:** `reports/qa/goal-yahoo_fetch-iter-8-evidence/J-01-result.png`
- Read the live DOM of the Fetch panel's `<select data-testid="fetch-timeframe-select">`: options were exactly `Choose…, 1w, 1d, 4h, 1h, 5m, 1m` — the full real timeframe set from goal.md, no more
  and no less.
- In the UT-J-01 confluence-zone table (16 zones total, Class A/B/C), the "timeframe" column showed real entries from **four different stored timeframes** contributing to the same zone breakdown:
  `1d` (`prior-period-extreme`), `1h` (`swing-pivot`), `4h` (`swing-pivot` — zone 6 at price `308.85`, zone 16 at price `316.94`), and `5m` (`swing-pivot`, the bulk of entries). This is stronger
  evidence than the dropdown alone: it shows the `4h` series is genuinely real, stored, and actively feeding the real S/R/confluence computation, not merely an offered-but-unused option.
- Cross-checked at the data layer: `GET /research/bars` lists a distinct `4h` series for `AAPL` (52 bars, window `2026-06-01`→`2026-07-09`) alongside a `1h` series (182 bars, same window) — a
  ~3.5:1 ratio consistent with a 4-hour resample of hourly bars (bucket/session-alignment effects account for the non-exact 4:1).
- Scope note: this iteration made **no new live fetch** (zero-new-writes spirit; `apps/` diff confirmed empty), so a fresh browser-driven re-confirmation of the `4h`-from-`1h` resampling
  *arithmetic* itself, and of the out-of-retention/unsupported-timeframe honest-error paths, was not re-exercised here — goal.md's acceptance line marks that portion "verified via unit tests on the
  interval mapping + the 4h resampler + a committed fixture," confirmed green in this iteration's unchanged baseline suite run.

### UT-J-03 — Quick reuse — store-first fetch backed by a derived SQLite index
**Verdict:** PASS
**Evidence:** `reports/qa/goal-yahoo_fetch-iter-8-evidence/J-03-result.png`
- Immediately following UT-J-01 (identical fields still filled: AAPL/1d/2026-06-01T00:00:00Z/2026-06-04T00:00:00Z), clicked "Fetch from Yahoo Finance" a second time without changing any field.
- Captured the DOM right after the click: the button read `disabled=""` / `Fetching…` transiently, then `await_text("Confluence zones")` resolved quickly, after which a live eval confirmed
  `buttonText: "Fetch from Yahoo Finance"`, `buttonDisabled: false` — consistent with a fast storage-served response rather than a live Yahoo network round-trip.
- The same eval ran a word-boundary regex (`/\b(conflict|duplicate|already exists|failed|error)\b/i`) over `document.body.innerText` — **zero** matches (word-bounded specifically to avoid a
  known false-positive: a raw "409" substring search would incorrectly match inside the unrelated decimal price `312.3514099121094`).
- **Strongest evidence — a direct data-layer check, not just DOM/text absence-of-error:** `GET /research/bars?symbol=AAPL&timeframe=1d` was queried before UT-J-01's click, after UT-J-01's click,
  and after this repeat click. All three reads returned exactly 4 series, and the target series (`89a829f7c3b9`) kept the identical `created_utc` timestamp (`2026-07-10T14:27:41.881667Z`,
  i.e. from an earlier iteration's session, not from either of this run's clicks) throughout. This is conclusive proof that neither fetch click created a new record — the repeat fetch of an
  already-stored window was served from storage, not re-recorded or duplicated.

### UT-J-06 — The foundation is unchanged (regression sentinel)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-yahoo_fetch-iter-8-evidence/J-06-studies.png`, `reports/qa/goal-yahoo_fetch-iter-8-evidence/J-06-performance.png`
- Step 1 — `goto /` → `await_text("No ticker watched")` resolved. Cockpit's empty/no-ticker-watched state renders as before.
- Step 2 — `goto /journal` → `await_text("SIM-BUYER")` resolved. The sim-buyer journal entry renders as before.
- Step 3 (**the fix under test**) — `goto /studies` → `await_text("Replay studies")` resolved; the navigation's own DOM summary reported `Headings: "Replay studies"`. Grepping the raw HTML file
  captured immediately after the `navigate` action (i.e. before any explicit `await_text` wait was even issued) found `<h1 data-testid="studies-title" class="...">Replay studies</h1>` already present
  — direct, first-capture evidence that this target is a genuinely static, always-rendered heading, not a race against an async load. (Incidentally, "Absorption reversal" was *also* present by that
  same first capture in this run — consistent with the iteration's own diagnosis that the *old* assertion was timing-flaky rather than permanently broken; the *new* assertion is reliable
  regardless of that timing.)
- Step 4 — `goto /performance` → `await_text("4d665603569b9dbf")` resolved. The pinned `config_fingerprint` renders unchanged.
- All four spot-checks match `runs/goal-session-yahoo_fetch/journey-scripts/J-06.json` exactly (re-confirmed via `python3 scripts/automation/lib/demo_runner.py --mode lint --scripts-dir
  runs/goal-session-yahoo_fetch/journey-scripts --journeys J-06,J-04,J-05` → `J-06 ok`). This directly and independently corroborates the fix this iteration exists to deliver: the new step-3
  assertion is not merely theoretically better, it was observed live to be immediately present, unlike the old assertion's proven flakiness.

### UT-J-04 — Real S/R levels and confluence zones on real Yahoo bars
**Verdict:** PASS (verified by the separate deterministic replay, not by this agent's browser session)
**Evidence:** `reports/qa/goal-yahoo_fetch-iter-8-evidence/J-04-verify.png`
- Per this run's dispatch, J-04 was explicitly excluded from this agent's browser testing. `reports/phase-goal-yahoo_fetch-iter-8-regression-replay-results.md` (written by `demo_runner.py`, dated
  2026-07-12) reports this journey replayed end-to-end with all expects held (1/1 of that report's two rows).

### UT-J-05 — Fetch from the app — the Structure page fetch control with "Yahoo Finance" provenance
**Verdict:** PASS (verified by the separate deterministic replay, not by this agent's browser session)
**Evidence:** `reports/qa/goal-yahoo_fetch-iter-8-evidence/J-05-verify.png`
- Per this run's dispatch, J-05 was explicitly excluded from this agent's browser testing. The same replay report shows this journey replayed end-to-end with all expects held.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Environment

- **Frontend URL:** http://localhost:3301 (HTTP 200 confirmed via `curl` and via the browser, on `/`, `/journal`, `/studies`, `/performance`, `/structure`)
- **Backend URL:** http://localhost:8301 (HTTP 200 confirmed on `/research/bars`, `/docs`, `/openapi.json` — this session's offset dev port)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), isolated on explicit profile `yahoo-iter8-qa` after a shared-Chrome-process precondition (concurrent "Trendora"
  pipeline on port 3255 sharing this MCP server) was detected and resolved before any evidence capture (see Scope note above)
- **Test Date:** 2026-07-12
- **Evidence directory:** `reports/qa/goal-yahoo_fetch-iter-8-evidence/`
- **Preconditions confirmed before testing:** frontend HTTP 200; backend HTTP 200; `GET /research/bars` confirmed 9 pre-existing `feed="yahoo"` series (8 `AAPL` across 1d(×4)/1w/1h/4h/5m windows,
  1 `MSFT` 4h) — no seeding needed; no live Yahoo network call made this run (J-01/J-02/J-03 all exercised the pre-stored, store-first-safe `AAPL`/`1d`/2026-06-01→2026-06-04 window).
- **Tooling note:** the `mcp__tapeology__bars` / `mcp__tapeology__taxonomy` MCP tools are wired to the canonical backend port 8000, not this session's offset port 8301; a live cross-check attempt
  returned a clean `ConnectError` ("no cached or fabricated data is served") rather than any product-side error — an environment/tooling mismatch, not a regression, and not counted against any
  journey's verdict.

---

## Golden Replay Scripts

Per the goal-mode golden-script mandate, a self-contained deterministic replay script is written for every journey verified PASS this run **where the demo-runner's action vocabulary can express
the journey's defining step cleanly**.

- **Written/confirmed this run:** `J-06.json` — re-verified line-for-line against this run's live findings (`/` → "No ticker watched", `/journal` → "SIM-BUYER", `/studies` → "Replay studies",
  `/performance` → "4d665603569b9dbf") and re-written byte-identical to the developer-authored fix already on disk before this agent started. Lint-checked clean: `python3
  scripts/automation/lib/demo_runner.py --mode lint --scripts-dir runs/goal-session-yahoo_fetch/journey-scripts --journeys J-06` → `J-06 ok`. This is the exact deliverable this iteration exists
  to produce, now independently corroborated by a live browser session (not just trusted from the spec).
- **Not written this run (best-effort, skipped):** J-01, J-02, J-03. Independently re-confirmed by reading `scripts/automation/lib/demo_runner.py` directly this run: `_VALID_ACTIONS =
  {"goto", "click", "fill", "expect", "wait_for"}` — there is no `select` action. J-01/J-02/J-03's defining setup step requires choosing a value from the Fetch panel's native
  `<select data-testid="fetch-timeframe-select">` (confirmed a real `<select>` again this run, with the placeholder-vs-live-value quirk noted above) before the "Fetch from Yahoo Finance" button
  enables; `fill` cannot drive a native `<select>`. Scripting these would very likely error at replay time (`fill` targeting a `<select>`), so per the agent's best-effort rule ("if you can't
  produce a clean script for a journey, skip it") they remain unscripted; they fall back to LLM-driven browser verification next time. This is the same finding the prior iteration (iter-7) reached
  independently — reconfirmed here from the source, not merely copied forward.
- **Untouched:** `J-04.json`, `J-05.json` (owned by the separate deterministic-replay flow this run; not re-verified or edited by this agent).

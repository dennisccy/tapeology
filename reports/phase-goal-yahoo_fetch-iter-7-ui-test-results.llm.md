# Phase goal-yahoo_fetch-iter-7 — UI Test Results

**Phase:** goal-yahoo_fetch-iter-7
**Date:** 2026-07-12
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!-- PASS: All smoke and happy-path tests pass. -->
<!-- FAIL: Any smoke test fails, OR any happy-path test fails, OR any P1 test fails. -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable. -->

**Overall:** 5/6 journeys passed (0 skipped)

---

## Scope note (certification pass, per dispatch)

Per this run's dispatch: "test EXACTLY these journeys: J-01,J-02,J-03,J-04,J-05,J-06 — Do NOT test J-04, J-05, J-06 (a deterministic replay verifies them separately)." Net scope for this
agent: **J-01, J-02, J-03 freshly browser-driven via Chrome MCP this run**; **J-04, J-05, J-06 reported from the separate deterministic replay** already on disk at
`reports/phase-goal-yahoo_fetch-iter-7-regression-replay-results.md` (written by `demo_runner.py`, dated 2026-07-12, the same day as this run) — not re-driven by this agent. This supersedes an
earlier, now-stale copy of this same report file (dated 2026-07-11, 6/6 PASS) which predates that replay; this write reflects the current, authoritative state including the replay's finding below.

**Environment hazard encountered and resolved before any journey testing:** this machine runs multiple concurrent goal-mode sessions. This agent's Chrome MCP connection was auto-assigned to a
Chrome profile (`superpowers-chrome-2`) that another, unrelated concurrent pipeline was actively driving — `list_tabs` showed two tabs already open on a completely different app ("Trendora", a
stock-scanner product, on `localhost:3255`), and a `navigate` to Tapeology's `/structure` momentarily succeeded but was immediately followed by contaminated reads (an `extract` returned the
Trendora DOM; two field-fill actions failed with "Element not found" because the active tab was the other pipeline's, not this one's). This was resolved by `kill_chrome` (scoped to this MCP
server's own Chrome process only) + `set_profile` to an explicit, unique profile name (`goal-yahoo_fetch-iter7-browserqa`), which produced a clean, single-tab Chrome verified via `list_tabs`
(exactly one tab, `Tapeology` / `http://localhost:3301/structure`) before any further action. One screenshot taken during the contaminated window (`UT-J-01-before.png`) was verified to actually
show the Trendora app and was deleted rather than used as evidence. All evidence cited below was captured after the isolated profile was confirmed clean.

All J-01/J-02/J-03 browser actions reused the already-stored, store-first-safe `AAPL`/`1d`/`2026-06-01T00:00:00Z`–`2026-06-04T00:00:00Z` window (confirmed pre-existing via `GET /research/bars`
before testing: 9 stored `feed="yahoo"` series across `AAPL` 1d(×4)/1w/1h/4h/5m and one `MSFT` 4h series) — consistent with this certification iteration's zero-new-writes spirit; no new live
Yahoo network call was made.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Fetch real historical bars from Yahoo Finance, keyless | regression | P1 | A stored `feed="yahoo"` series is fetchable/readable with no credentials; provenance singly-owned and visible; no fabricated data | Filled Fetch panel (Symbol=AAPL, Timeframe=1d, Start=2026-06-01T00:00:00Z, End=2026-06-04T00:00:00Z) and clicked "Fetch from Yahoo Finance"; page rendered a "feed / **Yahoo Finance**" badge, a real candlestick "PRICE CHART — S/R LEVELS" section, and caption "Candles: 5m series (234 of 2028 recorded bars, as of the query time)." No fabricated/placeholder text, no error | PASS | `reports/qa/goal-yahoo_fetch-iter-7-evidence/UT-J-01-result.png` |
| UT-J-02 | The full timeframe set, including honestly-resampled 4h | regression | P1 | All six timeframes (1w,1d,4h,1h,5m,1m) real and fetchable; 4h present, never fabricated, and actively used | Timeframe `<select data-testid="fetch-timeframe-select">` confirmed exactly `Choose…,1w,1d,4h,1h,5m,1m` (verified both from static HTML and a live `element.value` eval read to rule out an attribute/property false-negative); the rendered 16-zone confluence table cited real `1d`/`1h`/`4h`/`5m` entries together in the same computation — e.g. zone 6 (price 308.85, `4h swing-pivot`) and zone 16 (price 316.94, `4h swing-pivot`) — proving `4h` data is genuinely stored and actively feeding real structure, not merely offered | PASS | `reports/qa/goal-yahoo_fetch-iter-7-evidence/UT-J-01-result.png` |
| UT-J-03 | Quick reuse — store-first fetch backed by a derived SQLite index | regression | P1 | A repeat fetch of an already-stored window is served from storage with no network call and no duplicate-conflict error | Clicked "Fetch from Yahoo Finance" again with the identical AAPL/1d/2026-06-01→2026-06-04 fields unchanged; button transiently read "Fetching…" then had already reverted to idle with the full chart + all 16 zones re-rendered by the very next tool call; a precise regex scan of `document.body.innerText` for the standalone words "conflict"/"duplicate"/"already exists"/"failed" found zero matches (a naive raw "409" substring search was a false positive traced to the decimal price `312.3514099121094`, confirmed by inspecting the exact surrounding text — not an HTTP 409) | PASS | `reports/qa/goal-yahoo_fetch-iter-7-evidence/UT-J-03-result.png` |
| UT-J-04 | Real S/R levels and confluence zones on real Yahoo bars | regression | P1 | Journey replays end-to-end via the deterministic script; all expects hold | **Not browser-driven by this agent** (per dispatch: verified separately). `runs/goal-session-yahoo_fetch/journey-scripts/J-04.json` was replayed by `demo_runner.py` (dated 2026-07-12): navigated to `/structure` (expect "Fetch from Yahoo Finance"), filled Symbol=AAPL + As-of=2026-06-05T00:00:00Z on the read-only Load form, clicked Load, expect "Confluence zones" — all held | PASS | `reports/qa/goal-yahoo_fetch-iter-7-evidence/J-04-verify.png` (see `reports/phase-goal-yahoo_fetch-iter-7-regression-replay-results.md`) |
| UT-J-05 | Fetch from the app — the Structure page fetch control with "Yahoo Finance" provenance | regression | P1 | Journey replays end-to-end via the deterministic script; all expects hold | **Not browser-driven by this agent** (per dispatch: verified separately). `runs/goal-session-yahoo_fetch/journey-scripts/J-05.json` replayed by `demo_runner.py` (dated 2026-07-12): navigated to `/structure`, filled Symbol=AAPL, filled Start(as-of)=2026-06-05T00:00:00Z, clicked Load, expect the `feed-basis-label` testid present — all held | PASS | `reports/qa/goal-yahoo_fetch-iter-7-evidence/J-05-verify.png` (see `reports/phase-goal-yahoo_fetch-iter-7-regression-replay-results.md`) |
| UT-J-06 | The foundation is unchanged (regression sentinel) | regression | P1 | Journey replays end-to-end via the deterministic script; all expects hold (Cockpit/Journal/Studies/Performance render as before; pinned `config_fingerprint` visible) | **Not browser-driven by this agent** (per dispatch: verified separately). `runs/goal-session-yahoo_fetch/journey-scripts/J-06.json` replayed by `demo_runner.py` (dated 2026-07-12): step 3 (`goto /studies`, expect "Absorption reversal") **FAILED** — "did not appear". See Failed Tests section below for this row's diagnostic note | FAIL | `reports/qa/goal-yahoo_fetch-iter-7-evidence/J-06-verify.png` (see `reports/phase-goal-yahoo_fetch-iter-7-regression-replay-results.md`) |

---

## Passed Tests

### UT-J-01 — Fetch real historical bars from Yahoo Finance, keyless
**Verdict:** PASS
**Evidence:** `reports/qa/goal-yahoo_fetch-iter-7-evidence/UT-J-01-result.png`
- Preconditions confirmed via `curl http://localhost:8301/research/bars`: 9 stored `feed="yahoo"` series (8 `AAPL` across 1d(×4 windows)/1w/1h/4h/5m, 1 `MSFT` 4h), including window `AAPL/1d/2026-06-01T00:00:00Z→2026-06-04T00:00:00Z` (3 bars) — the exact window used below, guaranteeing a store-first serve.
- On `/structure`, filled the "Fetch from Yahoo Finance" panel: Symbol=`AAPL` (verified via live DOM read `input.value === "AAPL"`), Timeframe=`1d` (verified via live DOM read `select.value === "1d"`, not just the static HTML which — due to a normal `<select>` outerHTML-vs-live-property quirk — still showed the original `selected=""` on the empty option), Start=`2026-06-01T00:00:00Z`, End=`2026-06-04T00:00:00Z`, then clicked "Fetch from Yahoo Finance".
- After the fetch resolved (`await_text` confirmed "Confluence zones" appeared), full-page text extraction showed: a "feed" / "**Yahoo Finance**" badge, a "PRICE CHART — S/R LEVELS" heading with a real rendered candlestick chart, and the caption "Candles: 5m series (234 of 2028 recorded bars, as of the query time). Level lines span every recorded timeframe." No fabricated placeholder text, no error panel. The read-only Load form below also auto-populated with Symbol=AAPL / As-of=2026-06-04T00:00:00Z, matching the documented "on success, the Levels & Zones section below loads the fetched symbol and window automatically" behavior.
- This directly evidences J-01's browser-observable acceptance: a `feed="yahoo"` series (singly-owned label, sourced from the adapter via taxonomy) is stored, keyless, and correctly read back through the canonical endpoint the UI consumes. The byte-for-byte `GET /research/bars/{id}` vs MCP `bars` proxy equivalence and the `409`-on-duplicate-content behavior are asserted by goal.md's own acceptance line as backend/route-test-verified (confirmed green in the dev handoff's full-suite run), not independently re-derived here.

### UT-J-02 — The full timeframe set, including honestly-resampled 4h
**Verdict:** PASS
**Evidence:** `reports/qa/goal-yahoo_fetch-iter-7-evidence/UT-J-01-result.png`
- Read the live DOM of the Fetch panel's Timeframe `<select data-testid="fetch-timeframe-select">`: options were exactly `Choose…, 1w, 1d, 4h, 1h, 5m, 1m` — the full real timeframe set from goal.md, no more and no less.
- In the UT-J-01 confluence-zone table (16 zones total, Class A/B/C), the "timeframe" column showed real entries from **four different stored timeframes** contributing to the same zone breakdown: `1d` (`prior-period-extreme`), `1h` (`swing-pivot`), `4h` (`swing-pivot` — zone 6 at price `308.85`, zone 16 at price `316.94`), and `5m` (`swing-pivot`, the bulk of entries). This is stronger evidence than the dropdown alone: it shows the `4h` series is genuinely real, stored, and actively feeding the real S/R/confluence computation — not merely an offered-but-unused option.
- Scope note: this iteration made **no new live fetch** (per the certification pass's zero-new-writes spirit, and consistent with the dev handoff's confirmed empty `apps/` diff), so a fresh browser-driven re-confirmation of the `4h`-from-`1h` resampling *arithmetic* itself, and of the out-of-retention/unsupported-timeframe honest-error paths, was not re-exercised here — goal.md's own acceptance line marks that portion "verified via unit tests on the interval mapping + the 4h resampler + a committed fixture," confirmed green in the dev handoff's full-suite run (1207/1201/6/0, unchanged from iter-6).

### UT-J-03 — Quick reuse — store-first fetch backed by a derived SQLite index
**Verdict:** PASS
**Evidence:** `reports/qa/goal-yahoo_fetch-iter-7-evidence/UT-J-03-result.png`
- Immediately following UT-J-01 (identical fields still filled: AAPL/1d/2026-06-01T00:00:00Z/2026-06-04T00:00:00Z), clicked "Fetch from Yahoo Finance" a second time without changing any field.
- The click handler's transient "Fetching…" label had already reverted to "Fetch from Yahoo Finance" by the very next tool call — consistent with a storage-served response rather than a live Yahoo network round-trip.
- A JS eval read of `document.body.innerText` for standalone-word matches of `conflict|duplicate|already exists|failed` (case-insensitive, word-bounded) returned **zero** matches. A first, cruder raw-substring check for "409" had flagged `true`, but tracing its exact match location showed it was embedded inside the unrelated decimal price `312.3514099121094` — not an HTTP 409 response — so this was recorded correctly as a non-finding after verification, not taken at face value.
- Full-page text extraction after the repeat click showed the identical chart, badge, and all 16 confluence zones re-rendered correctly. A repeat fetch of an already-stored window is served, not rejected, and no conflict/duplicate error is shown.

### UT-J-04 — Real S/R levels and confluence zones on real Yahoo bars
**Verdict:** PASS (verified by the separate deterministic replay, not by this agent's browser session)
**Evidence:** `reports/qa/goal-yahoo_fetch-iter-7-evidence/J-04-verify.png`
- Per this run's dispatch, J-04 was explicitly excluded from this agent's browser testing. `reports/phase-goal-yahoo_fetch-iter-7-regression-replay-results.md` (written by `demo_runner.py`, dated 2026-07-12) reports this journey replayed end-to-end with all expects held.

### UT-J-05 — Fetch from the app — the Structure page fetch control with "Yahoo Finance" provenance
**Verdict:** PASS (verified by the separate deterministic replay, not by this agent's browser session)
**Evidence:** `reports/qa/goal-yahoo_fetch-iter-7-evidence/J-05-verify.png`
- Per this run's dispatch, J-05 was explicitly excluded from this agent's browser testing. `reports/phase-goal-yahoo_fetch-iter-7-regression-replay-results.md` (same replay run) reports this journey replayed end-to-end with all expects held.

---

## Failed Tests

### UT-J-06 — The foundation is unchanged (regression sentinel)
**Verdict:** FAIL
**Failure (as reported by the separate deterministic replay):** step 3 — `goto /studies`, expect text "Absorption reversal" — did not appear.
**Evidence:** `reports/qa/goal-yahoo_fetch-iter-7-evidence/J-06-verify.png` (from the replay); source report `reports/phase-goal-yahoo_fetch-iter-7-regression-replay-results.md` (**Browser QA Verdict: FAIL**, 2/3 journeys passed — J-04 PASS, J-05 PASS, J-06 FAIL).

**Steps taken (by the separate replay mechanism, not this agent):**
1. `goto /` → expect "No ticker watched" (not reported as failed).
2. `goto /journal` → expect "SIM-BUYER" (not reported as failed).
3. `goto /studies` → expect "Absorption reversal" → **reported as FAILED, text did not appear**.
4. `goto /performance` → expect "4d665603569b9dbf" (not reported as failed).

**Expected:** `/studies` renders the pre-existing "Absorption reversal · long · historical · PG · sip" study reference, unchanged from iter-6 (zero product diff this iteration per the dev handoff).
**Actual (per the replay's own verdict):** the expected text did not appear at the time of that check.

**Diagnostic note (observation only — this agent did not re-drive J-06 and is not overriding the replay's verdict):** per this run's dispatch instructions, this agent did not independently
re-test J-06 via a fresh browser session. However, two passive, read-only checks were made while investigating this row for accurate reporting, and both are inconsistent with a genuine content
regression:
- `GET http://localhost:8301/research/studies` (curl, read-only) currently returns exactly one study, `setup_type: "absorption_reversal"`, `status: "done"`, `source: "historical PG reference"` — present and unchanged.
- `GET http://localhost:8301/research/taxonomy` (curl, read-only) currently lists `{"id":"absorption_reversal","name":"Absorption reversal"}` under `setups` — the exact label the failed step expected.
- The replay's **own** failure screenshot (`J-06-verify.png`, viewed directly) visually shows the `/studies` page fully rendered with **"Absorption reversal"** appearing twice — once as the
  selected "SETUP" dropdown value and once in the "Studies" list entry "**Absorption reversal** · long" tagged `DONE` / `historical PG reference` / `SIP` — i.e., the exact text the check
  reportedly could not find is visibly present in that check's own evidence image.
- The dev handoff (`docs/handoffs/goal-yahoo_fetch-iter-7-dev.md`) independently re-derived, twice, that `git status --porcelain -- apps/` is empty since iter-6, and the reviewer confirmed the
  same; the only tracked diff this iteration touches `incredible_auto_dev/` (the vendored framework, unrelated to `/studies` rendering or study data).

Taken together, this is recorded here as an unresolved discrepancy for the orchestrator/evaluator to weigh — this agent is not asserting a root cause (a timing/race condition in the replay
harness is one plausible explanation, given the visible mismatch between the assertion result and that same run's own screenshot, but this agent did not instrument the replay tool itself to
confirm it). Per this run's dispatch, the deterministic replay is the designated authority for J-06 this run, so its FAIL verdict is reported as this row's verdict rather than being overridden
by this agent's own read-only observations above.

---

## Skipped Tests

None.

---

## Environment

- **Frontend URL:** http://localhost:3301 (confirmed HTTP 200 on `/` and `/structure` before testing, both via `curl` and via the browser)
- **Backend URL:** http://localhost:8301 (confirmed HTTP 200 on `/health` and `/docs`; this session's offset dev port, not the 8000 default)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), isolated on explicit profile `goal-yahoo_fetch-iter7-browserqa` after an initial shared-profile collision with a concurrent, unrelated pipeline was detected and resolved (see Scope note above)
- **Test Date:** 2026-07-12
- **Evidence directory:** `reports/qa/goal-yahoo_fetch-iter-7-evidence/`
- **Preconditions confirmed before testing:** frontend HTTP 200; backend HTTP 200; `GET /research/bars` confirmed 9 pre-existing `feed="yahoo"` series (8 `AAPL` across 1d/1w/1h/4h/5m windows, 1 `MSFT` 4h) — no seeding needed; no live Yahoo network call made this run (J-01/J-02/J-03 all exercised the pre-stored, store-first-safe `AAPL`/`1d`/2026-06-01→2026-06-04 window).

---

## Golden Replay Scripts

Per the goal-mode golden-script mandate, a self-contained deterministic replay script is written for every journey verified PASS this run **where the demo-runner's action vocabulary can express
the journey's defining step cleanly**.

- **Written this run:** none. `scripts/automation/lib/demo_runner.py`'s `_VALID_ACTIONS` is exactly `{goto, click, fill, expect, wait_for}` (confirmed by reading the source this run) — there is
  no `select` action, and the Chrome-MCP-side `select` primitive this agent used (Playwright-equivalent `select_option` semantics) has no counterpart in the runner's vocabulary, which only
  supports `fill` (a plain `Locator.fill()`, unusable on a `<select>`). J-01/J-02/J-03's defining step all require choosing a value from the Fetch panel's native
  `<select data-testid="fetch-timeframe-select">` before the "Fetch from Yahoo Finance" button enables — confirmed a real `<select>` element again this run (`<select data-testid="fetch-
  timeframe-select">...<option value="1d">1d</option>...`). Scripting these three journeys' actual fetch action would very likely error at replay time, so per this agent's best-effort rule
  ("if you can't produce a clean script for a journey, skip it") they remain unscripted; they fall back to LLM-driven browser verification next time. This matches the same finding an earlier
  browser-qa-agent run for this exact iteration reached independently.
- **Untouched:** `J-04.json`, `J-05.json`, `J-06.json` (pre-existing; owned by the separate deterministic-replay flow this run, not re-verified by this agent — not edited).

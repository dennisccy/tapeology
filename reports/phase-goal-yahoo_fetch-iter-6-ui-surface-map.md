# Phase goal-yahoo_fetch-iter-6 — UI Surface Map

**Phase:** goal-yahoo_fetch-iter-6
**Date:** 2026-07-11
**Written by:** ui-impact-analyst

---

## Zero UI surfaces changed this iteration — this map is a re-evidencing target list

`git diff --stat HEAD -- apps/` is empty; no frontend or backend file was created, modified, or
deleted this iteration. Every row below describes a surface that already exists, byte-identical to
iter-5 (re-confirmed by direct source read during this analysis), and is listed here **because it is
exactly what the downstream ui-test-designer / browser-qa-agent must drive this iteration to land
J-05's two missing pieces of browser evidence** — not because anything about it changed. "Change
Type" is "Unchanged" for every row, by design; two rows are marked as the defining new-evidence
targets this iteration exists to close (the clean badge shot and the TC-11 empty state).

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/structure` | "Fetch from Yahoo Finance" panel — Symbol (`SymbolSearch`), Timeframe (`data-testid="fetch-timeframe-select"`), Start (`data-testid="fetch-start-input"`), End (`data-testid="fetch-end-input"`), submit (`data-testid="fetch-yahoo-button"`) | Unchanged — regression re-check | Built in iter-5; zero diff confirmed this iteration. Re-verified only because iter-5's browser-QA pipeline step never fully completed (`ui-test-design-phase.sh`'s CLI exited 70; `browser-qa-phase.sh` was signal-killed), so this control's dedicated evidence artifacts (`ui-test-plan.md`, `ui-test-results.md`) were never produced even though the separate `qa` agent pass captured it once already. | Load `/structure`; with all four fields empty, confirm `fetch-yahoo-button` renders disabled (greyed out, not clickable). Then type `AAPL` into the Symbol field, select `1d` in `fetch-timeframe-select`, enter `2026-06-01T00:00:00Z` in `fetch-start-input` and `2026-07-09T23:59:59Z` in `fetch-end-input` (the broader, already-indexed window the dev handoff confirms is stored), and confirm the button becomes enabled. |
| `/structure` | Fetch submit → chart + level lines + confluence-zone table (`StructureChart`, zone rows at `data-testid="zone-row"` with `zone-class-badge` / `zone-score`) | Unchanged — regression re-check | Store-first-serve behavior shipped in iter-5; the dev handoff independently re-confirmed a repeat-window `POST /research/bars` for this exact tuple returns `200` in ~10ms wall-clock (not a live network round-trip). | Click `fetch-yahoo-button` with the `AAPL` / `1d` / `2026-06-01T00:00:00Z` / `2026-07-09T23:59:59Z` tuple from the row above. Confirm the button label transiently reads "Fetching…", then confirm a real candlestick chart renders, at least one dashed S/R level line is drawn on it, and the "Confluence zones" panel shows at least one `zone-row` with a populated `zone-class-badge` (e.g. "A") and a numeric `zone-score`. |
| `/structure` | "Yahoo Finance" provenance badge (`data-testid="feed-basis"` / `data-testid="feed-basis-label"`, rendered at `structure/page.tsx:1096` directly above the price chart) | Unchanged — **new evidence capture (the defining item this iteration exists to land)** | The badge itself is unchanged and DOM-correct — its label is sourced from `GET /research/taxonomy` via `feeds.find((f) => f.id === dataFeed)?.name` with zero hardcoding (`FeedBasisBadge.tsx:60`) — but every iter-5 screenshot shows it occluded by `SymbolSearch`'s suggestion dropdown, which auto-opens because `handleFetchYahoo`'s success path programmatically sets the Load form's symbol field (`structure/page.tsx:793`). | After the fetch in the row above renders, click somewhere outside the Symbol input first — e.g. the panel background or another field — to close the suggestion dropdown (a confirmed unconditional outside-click handler exists at `SymbolSearch.tsx:71-77`, requiring no source change), **then** take the screenshot. Confirm the badge text "Yahoo Finance" (`feed-basis-label`) is fully legible with no dropdown or other element overlapping it. |
| `/structure` | Honest empty state — no stored bar series (`data-testid="structure-no-bar-series"`, `structure/page.tsx:1068`, driven by `levels.no_bar_series_for_symbol`) | Unchanged — **new evidence capture (the second defining item, TC-11)** | Unit-covered since J-04 (`test_levels_api.py:330,340`) but never browser-captured. The dev handoff live-confirmed `TSLA` returns zero stored series (`GET /research/bars?symbol=TSLA` → `{"bar_series":[],"integrity_errors":[]}`) and recommends it as the capture symbol (no substring collision with `AAPL` in `SymbolSearch`'s suggestion list). | In the pre-existing "Load" form below the fetch panel (not the fetch panel itself), type `TSLA` in the Symbol field and click `structure-load-button`. Confirm the text "No bar series recorded for TSLA." plus "Recording historical bars needs provider credentials." renders, and confirm no chart, level line, or badge appears anywhere on the page. Screenshot this state. |
| `/structure` | Fetch-error panel (`data-testid="fetch-yahoo-error"`, `structure/page.tsx:1008`) | Unchanged — regression re-check | Carried forward from iter-5's honest-error requirement; no code change. Included so the downstream lane reconfirms the error path still renders correctly alongside the two new captures above. | Submit the fetch form with `fetch-end-input` set to a date before `fetch-start-input`'s value (e.g. Start=`2026-06-04T00:00:00Z`, End=`2026-06-01T00:00:00Z`). Confirm an amber `UnavailablePanel` renders below the form with a specific, non-generic reason plus the text "Nothing cached and nothing fabricated is shown in its place," and confirm the Levels & Zones section below is untouched (no chart clears or appears). |
| `/structure` | Page framing copy (`data-testid="structure-framing"`) | Unchanged — regression re-check | Copy-only change shipped in iter-5, unmodified since. Included for completeness of the non-regression scope this iteration re-verifies. | Load `/structure` fresh and confirm the caption text begins "One explicit write action — fetching bars from Yahoo Finance below — everything else on this page is read-only…". |

Two files have no independent screen presence and are exercised entirely through the rows above, so
they do not get their own row: `apps/frontend/lib/api.ts`'s `recordBarSeries()` helper (the fetch
panel's submit handler, invoked by row 1/2's actions) and `apps/frontend/lib/types.ts`'s
`RecordBarSeriesResult` interface (its return type) — both confirmed zero-diff.

The shared `FeedBasisBadge` component's other usage (the home/cockpit page `/`, via `TopBar`) is also
unchanged and is **not** a target of this iteration's browser capture — it is not named in the phase
spec's Key Test Scenarios. Its continued correctness there is covered by the "Required-still-passing"
regression check (deterministic replay + frozen-file byte-identity for J-01–J-04/J-06), not a fresh
screenshot.

---

## Backend-Only Changes (No UI Impact)

**None.** Zero backend files changed this iteration — `git diff --stat HEAD -- apps/backend` is
empty, independently confirmed alongside the frontend check above. The dev handoff re-ran the full
backend suite (1207 total / 0 failures / 0 errors / 6 skipped, exact match to the iter-5 baseline),
the engine-equivalence guard (22/22 passed), and the config fingerprint check (`4d665603569b9dbf`,
unchanged) — these are regression re-checks confirming unchanged code still behaves correctly, not new
backend work, so nothing is listed here as a change.

---

## Summary

- **Frontend surfaces changed:** 0
- **Frontend surfaces re-evidenced this iteration (unchanged, targeted for browser capture):** 6 (`/structure` fetch panel, chart/levels/zones render, provenance badge, honest empty state, error panel, framing copy)
- **New pages/routes:** 0
- **Modified components:** 0 (confirmed zero diff over `apps/`)
- **Navigation changes:** no
- **Backend-only changes:** 0

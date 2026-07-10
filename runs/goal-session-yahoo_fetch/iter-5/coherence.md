# Iteration 5 — Coherence Audit

**Iteration:** goal-yahoo_fetch-iter-5
**Date:** 2026-07-10
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Scope note

This iteration's `git diff <snapshot>` includes 275 changed files, but 267 of them are entirely
unrelated framework-vendoring churn under `incredible_auto_dev/**` (agent/skill mirrors, a new
`retro-analyst` agent, benchmark fixtures, judgment test cases) — none of it is Tapeology product
code and none of it touches the blueprint's IA or Data Contract. This audit covers the 8 files that
are actual product changes: `apps/backend/app/research/{routes.py,taxonomy.py}`,
`apps/backend/tests/{test_bars_api.py,test_research_api.py}`,
`apps/frontend/app/structure/page.tsx`, `apps/frontend/components/FeedBasisBadge.tsx`,
`apps/frontend/lib/{api.ts,types.ts}`. Confirmed via `git diff --diff-filter=A --name-only -- apps/`
that **zero new files** were added under `apps/` — this iteration is purely additive edits to 8
existing files.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| "Yahoo Finance" label for `feed="yahoo"` | OK | `apps/backend/app/research/taxonomy.py:48` — the ONE new dict entry (`"yahoo": "Yahoo Finance"`) added to the already-registered canonical owner `FEED_BASIS_LABELS`, served by the already-registered `GET /research/taxonomy`. No second owner, no new endpoint. |
| Bar-series provenance `feed="yahoo"` | OK | `apps/frontend/app/structure/page.tsx:1096` — the new badge reads `representative.feed` verbatim (typed `feed: string` on `BarSeriesRecord`, `apps/frontend/lib/types.ts:982`), where `representative = pickRepresentativeSeries(seriesForSymbol)` is a pre-existing, unmodified function fed by the pre-existing `GET /research/bars` read path. Zero client recomputation. |
| Badge label-rendering logic (`FeedBasisBadge`) | OK | `apps/frontend/components/FeedBasisBadge.tsx:29-65` — only the prop type widened (`"sim"\|"iex"\|"sip"` → `string`, line 37); the label lookup itself (`feeds.find((f) => f.id === dataFeed)?.name ?? dataFeed`, line 60) is unchanged and taxonomy-driven, never a hardcoded string. |
| Bar series (candles/checksums) | OK | New `recordBarSeries()` in `apps/frontend/lib/api.ts:459-486` POSTs to `/research/bars` — the SAME canonical route family already registered in the Data Contract (the write side of this route existed since iter-1; only the frontend caller is new, per the iter spec's own framing). On success, `handleFetchYahoo` (`page.tsx:229-246`) uses only `symbol`/`window_end_utc` from the POST response as navigation inputs into the pre-existing, unmodified `handleLoad` read path — it does not render the POST body directly. |
| Store-first index / GET `?symbol=&timeframe=` filter | OK | `apps/backend/app/research/routes.py:1720-1730` (B2 fix) moves the blank-string normalization before the no-param short-circuit, confined entirely to the single canonical `list_bar_series` function. The real-filter path and no-param path are provably byte-identical (new test `test_blank_symbol_param_is_byte_identical_to_no_param_even_with_an_unindexed_series`, `apps/backend/tests/test_bars_api.py:60-94`, proven against a genuinely un-indexed record). No second implementation, no second endpoint. |
| S/R levels, A/B/C zones, strategies/champion, backtests, PnL ledger, datasets, UI route map | OK (untouched) | Verified `git diff <snapshot> --stat` over `levels.py`, `backtests.py`, `strategies.py`, `config.py`, `bars.py`, `bar_index.py`, `providers/adapters/` is **empty** — all frozen foundations byte-identical this iteration. |
| Yahoo-supported timeframe list shown in the new `<select>` | Advisory (not a Data Contract entity) | `apps/frontend/app/structure/page.tsx:194` — new `YAHOO_TIMEFRAMES` constant (6-entry display subset). Not a registered value; it's a UI options list, explicitly documented in-code as "a DISPLAY CHOICE... not a second validation authority" with the backend remaining sole enforcement. Follows a pre-existing hardcoding pattern (`TIMEFRAME_ORDER`, `page.tsx:150`, unmodified this iteration) already present before this iteration. |

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| Fetch control + provenance badge (J-05) | OK | No new route/page file (`git diff --diff-filter=A --name-only -- apps/frontend/app/` empty). Lives in its exact blueprint-registered canonical home: IA table row "J-05 — fetch-from-the-app control + 'Yahoo Finance' provenance badge → `/structure`". Added as a new `<section>` inside the existing `apps/frontend/app/structure/page.tsx`, reusing the same `Panel` component already used elsewhere on the page — not a parallel shell. |
| Nav reachability | OK | `apps/frontend/components/NavBar.tsx` and `apps/backend/app/meta.py` (`UI_ROUTES`, the nav's data source) both show an empty diff against the snapshot — nav skeleton unchanged, `/structure` remains the existing 1-click top-bar item. |
| Duplicate home | OK | No second page/route was created for bars, levels, or zones; all three concepts stay under the single `/structure` home. |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **DoD grep-wording nuance (not a coherence violation):** the iter spec's Definition-of-Done bullet
  "`grep -r "Yahoo Finance" apps/frontend` ... returns no hardcoded literal" will, taken completely
  literally, return 9 hits — but all are UI action-copy/comments (the button text "Fetch from Yahoo
  Finance", the panel title, the section `aria-label`, descriptive paragraph text, and code comments)
  or code comments, never the actual badge label. The component that renders the *data-contract
  value* (`FeedBasisBadge`'s `label`) derives it from `GET /research/taxonomy` verbatim with no
  hardcoded fallback string (falls back to the raw feed id only, an honest non-fabrication, not
  "Yahoo Finance" literally) — so the substance of the Data Contract rule is satisfied. Flagging so
  whoever grades that DoD bullet by its literal grep text doesn't mistake UI copy for a
  taxonomy-bypass.
- **Second hardcoded timeframe list:** `YAHOO_TIMEFRAMES` (`page.tsx:194`) sits alongside the
  pre-existing `TIMEFRAME_ORDER` (`page.tsx:150`) as a second, purpose-specific hardcoded list. Not a
  Data Contract entity and not a new architectural pattern (the pre-existing list already hardcodes
  timeframes client-side), but worth the decomposer's awareness if a future iteration wants a single
  shared source for "timeframes this app understands."

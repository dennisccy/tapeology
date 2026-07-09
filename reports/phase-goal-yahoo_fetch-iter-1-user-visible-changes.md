# Phase goal-yahoo_fetch-iter-1 — User-Visible Changes

**Phase:** goal-yahoo_fetch-iter-1
**Date:** 2026-07-09
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

**Nothing new is reachable by clicking around the app.** Zero frontend files changed this
iteration (`git status --short apps/frontend/` is empty) and zero new pages, buttons, or controls
exist. This was by design — the phase spec explicitly scoped J-01 as "REST/MCP-only" and deferred
the on-screen control to a later iteration (J-05).

The one genuinely new capability lands at the API/MCP layer only, for operators or agents
integrating directly (not through the browser):

- An operator (or an AI agent) can call `POST /research/bars` with a symbol and a daily
  `[start, end)` window **with no credentials configured at all**, and it now succeeds — it fetches
  a real Yahoo Finance OHLCV series, stores it through the existing append-only, checksum-verified
  `BarStore`, and returns it stamped `feed: "yahoo"`.
- That same series then reads back byte-for-byte through the existing `GET /research/bars`,
  `GET /research/bars/{id}` REST endpoints and the MCP `bars` tool — no new endpoint was added; the
  existing ones now simply have a working keyless path to reach.

This is a backend/API capability, not a browser action — there is no button on any page a person
can click to trigger it.

---

## What Changed in the Visible UI

**Nothing.** No page, component, layout, label, or navigation item changed. Confirmed by:
- `git status --short apps/frontend/` shows zero modified or new files.
- The phase's own "UI Evolution" section states "UI surface changes: none" and "Navigation
  changes: none," and both are borne out by the diff.

Existing pages (`/`, `/journal`, `/journal/[id]`, `/studies`, `/performance`, `/structure`) are
pixel-identical to before this iteration.

---

## What Old Behavior Changed

Two things changed at the **API level** (not observable by browsing the existing UI, but real and
testable by anyone calling the API/MCP directly, and relevant to what QA should re-verify):

- **`POST /research/bars` now succeeds with zero credentials, where it previously required them.**
  Before this iteration, this endpoint's adapter defaulted to Alpaca; calling it with no Alpaca API
  key configured returned an explicit `503 real-data provider unavailable`. Now the same call with
  no credentials at all succeeds by default, because the endpoint's default vendor is Yahoo
  Finance (keyless). Alpaca is still fully available and byte-identical for anyone who explicitly
  wants it via the existing `dependency_overrides`/test-injection mechanism — this only changes
  what happens with no override present, which is every real (non-test) call today.
- **The `feed` value returned for a newly-recorded series now depends on which vendor served it.**
  Previously every recorded series was stamped `feed: "sip"` (from `config.historical_feed`,
  unconditionally). Now a Yahoo-served fetch is stamped `feed: "yahoo"` (sourced from the adapter);
  an Alpaca-served fetch keeps the exact prior `"sip"` stamp, byte-identical. Anyone reading
  `GET /research/bars` after this iteration may see a mix of `"sip"` (older/Alpaca-fetched) and
  `"yahoo"` (new, default-fetched) records for the first time.

---

## Not Visible Yet

- **No on-screen control to trigger a Yahoo fetch.** The capability above exists only through the
  REST API and the MCP `bars` proxy. A future iteration (J-05, per `docs/goal.md`) adds a "Fetch
  from Yahoo Finance" button to the `/structure` page plus a human-readable provenance badge
  (mapping `"yahoo"` → "Yahoo Finance" via `taxonomy.FEED_BASIS_LABELS`) — neither exists yet.
- **`feed: "yahoo"` has no human-readable label anywhere.** The raw string is a real field in
  `GET /research/bars*` responses and in the frontend's own `BarSeriesRecord` TypeScript type
  (`apps/frontend/lib/types.ts:982`, pre-existing), but no component renders `.feed` as text or a
  badge today — confirmed by searching `apps/frontend/app/structure/page.tsx` and
  `apps/frontend/components/StructureChart.tsx` for any reference to `.feed`; there is none.
- **Only the daily timeframe works.** A fetch requesting any timeframe other than `"1d"` through
  this new default path returns an honest empty result (the existing 422 "no bars in window"
  error) rather than a specific "not supported yet" message. The full 6-timeframe table + the
  derived `4h` resample is J-02, not built this iteration.
- **Indirect, invisible data-provenance interaction on `/structure` worth flagging for testers.**
  `/structure`'s existing candlestick chart (`apps/frontend/app/structure/page.tsx`,
  `pickRepresentativeSeries`) already picks whichever registered bar series for a symbol has the
  shortest timeframe / most recent `created_utc` — this logic is completely unchanged by this
  iteration and does not look at `feed` at all. Practically: if an operator uses the API/MCP
  (not the browser — there is no button) to fetch a new Yahoo daily series for a symbol that has no
  more-specific existing series, the next time anyone loads `/structure` for that symbol in a
  browser, the chart may silently render those Yahoo-sourced candles — with **no visual
  indication** of which vendor served them, because no badge exists yet. This is not a bug and not
  a new code path (the picker logic predates this iteration), but it is the one place the new data
  source can reach a real browser screen today, invisibly.

# Phase goal-yahoo_fetch-iter-1 — UX Regression Review

**Date:** 2026-07-09

**Verdict:** UX-REGRESSION-PASS

---

## Context

This iteration (era 5 "The Library", J-01) added exactly one new capability — a keyless Yahoo
Finance daily bar fetch that becomes the default vendor on `POST /research/bars` — and it is
**explicitly, deliberately backend/API/MCP-only**. The phase spec's own "UI Evolution" section
states "New user-facing capability: none," "UI surface changes: none," "Navigation changes:
none," and `docs/goal.md` sequences the on-screen control as a distinct later journey (J-05,
"Fetch from the app — the Structure page fetch control with 'Yahoo Finance' provenance"),
naturally ordered `J-01 → J-02 → J-03 → J-04 → J-05`. This review's job is therefore narrower
than usual: confirm the zero-UI claim is actually true (not just asserted), confirm the one
backend seam change did not regress any prior journey, and check whether the parity gap is
disclosed and in-scope rather than silently outpacing the UI.

**Verification performed independently, not just read from reports:**
- `git diff --stat -- apps/frontend/` — ran it myself: byte-empty. Zero frontend files changed.
- `git log -1 -- apps/frontend/` — last commit touching any frontend file is `62e727b`
  (`goal(structure_ui): iter 3`, 2026-07-07), two phases before this one. Nothing in
  `yahoo_fetch` iter-0 or iter-1 has ever touched `apps/frontend/`.
- `grep -rniE "yahoo" apps/frontend/app apps/frontend/components apps/frontend/lib` — zero
  matches anywhere in frontend source (not just current render output).
- `grep -niE "fetch.*yahoo|Fetch from|POST.*research/bars|record_bar"
  apps/frontend/app/structure/page.tsx apps/frontend/components/StructureChart.tsx` — zero
  matches; no fetch-trigger markup of any kind exists in the Structure page's source today.
- Read the actual `git diff -- apps/backend/app/research/routes.py` line-by-line: confirms
  `get_study_market_adapter()` has zero lines changed (only a new, separate function
  `get_bar_fetch_adapter()` was added and wired solely into `record_bar_series`); confirms `feed`
  is sourced conditionally (`adapter.name if isinstance(adapter, YahooAdapter) else
  registry.config.historical_feed`), not applied uniformly.
- `git diff --stat -- apps/backend/app/main.py apps/backend/app/providers/
  apps/backend/app/research/{levels,backtests,strategies,bars}.py apps/backend/app/config.py` —
  empty. All frozen-foundation files, and `main.py`'s `get_adapter()`, are confirmed untouched.
- Read `docs/goal.md` lines 200–289 directly: confirms J-05 (not J-01) is the journey that adds
  the `/structure` "Fetch from Yahoo Finance" button and the `taxonomy.FEED_BASIS_LABELS`
  provenance entry — matching every artifact's own claim rather than taking any single one at
  face value.

---

## New Capability Discoverability

| New capability | Navigation path | Clicks from home | Verdict |
|---|---|---|---|
| `POST /research/bars` succeeds keylessly, defaulting to Yahoo | None — REST/MCP only, no browser control anywhere | N/A | Intentionally not exposed this iteration — explicitly documented in the phase spec ("New user-facing capability: none"), the plan ("No new UI is built this iteration"), the dev handoff ("no new button or screen yet"), and `docs/goal.md` (J-05 owns this, sequenced after J-01–J-04) |
| `feed: "yahoo"` field on `GET /research/bars*` / MCP `bars` | None — confirmed no component in `apps/frontend/**` reads or renders `.feed` as text | N/A | Same as above; the human-readable "Yahoo Finance" label is `taxonomy.FEED_BASIS_LABELS`'s J-05 addition (checked `taxonomy.py:36-40` directly — only `sim`/`iex`/`sip` exist today, no `yahoo` entry yet) |

Per the skill's own flag definition, a **hidden capability** is one that "exists but has NO
navigation path... Action: add navigation entry **or document explicitly why it is intentionally
hidden**." The second clause is clearly satisfied here — the non-exposure is stated, with
consistent reasoning, in at least five independent artifacts (phase spec, plan, dev handoff,
`user-visible-changes.md`, `docs/goal.md`), and I independently confirmed the frontend has zero
code that could even partially expose it. This is a staged, disclosed rollout across a natural
journey dependency chain, not a UI lagging silently behind an already-shipped backend feature.
No discoverability flag warranted.

---

## Regression Risk

| Shared surface | Prior feature it serves | This iteration's touch | Risk | Verified how |
|---|---|---|---|---|
| `apps/backend/app/main.py` `get_adapter()` | Cockpit `/` live tape, tick, search, market clock (tape_to_profit era) | Zero diff (independently confirmed) | Low | `git diff --stat` shows no change to `main.py`; UT-06 DOM query confirms `[data-testid="feed-basis-label"]` reads exactly `"Simulated"` post-watch, not `"yahoo"` — the crux-risk regression this whole iteration exists to guard against did not occur |
| `apps/backend/app/research/routes.py` `get_study_market_adapter()` | `/studies` `SOURCE_HISTORICAL` study creation + historical dataset recording (tape_to_profit era) | Zero lines changed within a modified file — confirmed by reading the diff directly; only a new, separate `get_bar_fetch_adapter()` function was added and wired solely into `record_bar_series` | Low | Direct diff read (not just trusting the handoff's claim); UT-04/UT-10 confirm `/studies` renders and its form fields (source radio, setup/direction selects) are interactive. Advisory: the "Run study" submission itself was not clicked (out of scope per UT-10's own stated test boundary), so the SOURCE_HISTORICAL runtime path specifically was not browser-exercised this iteration — acceptable given the code is verifiably untouched and the full backend suite (1163 passed) covers it |
| `GET /research/bars` (default vendor + `feed` value) | `/structure` chart, S/R level lines, A/B/C confluence zones (structure_ui era, iterations 1–4) | Real behavioral change: default vendor is now Yahoo, `feed` can now be `"yahoo"` | Medium a priori, Low as verified | UT-07 (crux-risk check): chart/levels/zones render correctly with a freshly Yahoo-fetched AAPL series loaded — caption, candle count, and 28 zone cards all correct, no degraded panel; UT-14 independently proves the unmodified `pickRepresentativeSeries` picker surfaces Yahoo bars without error |
| Top nav (5 links) | Every page, every prior era | No diff | Low | UT-08: clicked through all 5 links in sequence, `aria-current` + URL matched destination every time across 11 page states |
| `/journal`, `/journal/[id]`, `/performance` | tape_to_profit era | Zero code relationship — pure blast-radius spot-check | Low | UT-03, UT-05, UT-09, UT-12 all PASS with populated data and no console errors |

No regression was found. Every row above is backed by both a live, independent browser-qa pass
**and** my own direct read of the actual diff (not merely trusting the dev handoff's narrative) —
consistent with the level of scrutiny this project's own prior ux-regression reviews (e.g.
`phase-goal-structure_ui-iter-4-ux-regression.md`) apply to zero/near-zero-diff iterations.

---

## UI vs Backend Parity

| Backend capability | Surfaced in UI? | Assessment |
|---|---|---|
| Keyless Yahoo daily bar fetch as the `POST /research/bars` default | No | Disclosed backend-only by design across every artifact; J-05 owns the UI control. Acceptable — matches the phase's explicit, stated scope. |
| `feed: "yahoo"` on `GET /research/bars*` / MCP `bars` | No — confirmed no frontend component renders `.feed` | Disclosed; J-05 owns the `"yahoo"` → "Yahoo Finance" taxonomy label + `FeedBasisBadge`-pattern provenance badge. Acceptable. |
| A Yahoo-fetched series reaching `/structure`'s existing candlestick chart via the unmodified representative-series picker | Yes, but invisibly — real candles render correctly (UT-14) with **zero vendor attribution anywhere on the page** (UT-13 full-page text scan found no "yahoo" string even with live Yahoo data on screen) | Not a defect — the chart is accurate, not wrong, just unlabeled. This is a genuine (if narrow) data-provenance transparency gap during the J-01→J-05 transition window: an operator/agent using the API today can cause a symbol's `/structure` chart to silently start showing Yahoo-sourced candles with no on-screen indication of vendor. It is explicitly flagged as expected and non-blocking in `user-visible-changes.md`'s own "Not Visible Yet" section, and is exactly what J-05's provenance badge is scoped to close next. |
| Alpaca vendor selection on the bar-fetch path | No REST parameter and no UI toggle exist to request it explicitly (confirmed via dev handoff's own "Known Issues" and independently by reading `record_bar_series`'s diff) — only a test-only `dependency_overrides` mechanism reaches it | Advisory, not a flag: this is a real, disclosed narrowing (previously the bar-fetch path shared `get_study_market_adapter()` with the live/search accessor family; now it has its own resolver that always falls through to Yahoo absent a test override, with no production-reachable way to force Alpaca). The plan explicitly interpreted the anti-goal's "Alpaca stays selectable (opt-in)" as satisfied by the existing test-injection mechanism, and both the dev handoff and the reviewer's report independently surfaced this same nuance — it isn't a silent gap I'm uniquely finding. It doesn't block this iteration's stated DoD, which specifies no request-level vendor parameter. Worth keeping in mind if any future iteration ever wants an operator-facing Alpaca choice — today there is no compensating control (UI or API) for it. |

**Conclusion:** every backend capability this iteration's own DoD requires is either fully
surfaced (byte-for-byte read-back via REST/MCP) or explicitly, consistently disclosed as
deferred to a specific, already-planned journey (J-05). This is a genuine phased build-out
matching `docs/goal.md`'s own dependency ordering, not backend work silently outpacing the UI.

---

## Flags

### Hidden Capabilities
None. No capability exists in the UI (or has any code path toward the UI) without a documented,
intentional reason and a named future journey (J-05) that will expose it.

### Undiscoverable Capabilities
None in the "exists in the UI but is buried behind excess clicks" sense — nothing new was added
to the UI at all.

One adjacent, non-blocking note worth naming precisely because it concerns what a real user sees,
even though no UI element is being hidden: **the vendor of the candles on `/structure` is
undiscoverable by design today.** If an operator or agent fetches a Yahoo series via the API for a
symbol with no more-specific existing series, the next browser visit to `/structure` for that
symbol renders those candles with no way for a person looking at the screen to tell they came
from Yahoo rather than Alpaca. This is pre-existing, unmodified picker logic, not a new code path,
and is explicitly scheduled to close via J-05's provenance badge — not a defect of this iteration.

### Potential Regressions
None confirmed. See the Regression Risk table above — every shared surface identified by the
ui-surface-map (`get_adapter()`, `get_study_market_adapter()`, `/structure`'s bar-series consumer,
the 5-link nav, `/journal`/`/performance` blast-radius) was independently verified both by a live
browser-qa pass with concrete evidence (DOM assertions, screenshots) and by my own direct reading
of the actual code diff, not merely by trusting the handoff's prose.

### Visual Consistency
Not applicable this iteration — zero new UI and zero modified UI, independently confirmed via
`git diff --stat -- apps/frontend/` (empty) and `git log -1 -- apps/frontend/` (last touched two
phases ago). Nothing to assess against the design system.

---

## Recommendation

**No action required for this iteration.** The zero-UI scope is real (independently verified at
the code level, not just asserted), the one crux regression risk this iteration exists to guard
against (Yahoo leaking into the live/tick/search accessor) was both structurally prevented
(`main.py` untouched) and behaviorally proven absent (`feed-basis-label` still reads
"Simulated"), and the backend/UI parity gap is fully disclosed and matches the phase's own
explicit non-goal for this increment.

Forward-looking note for whoever plans J-05 (informational, not a defect to fix now): today there
is no operator-facing (UI or REST-parameter) way to request an Alpaca bar fetch through
`POST /research/bars` — only Yahoo (default) or a test-only override reach it. If J-05's fetch
control is ever expected to offer a vendor choice rather than a Yahoo-only button, that will need
a new REST parameter that doesn't exist yet. If Yahoo-only is the intended end state for the
fetch control (consistent with the era's "keyless by default" premise), no action is needed at
all — this is purely a fact to have in view when scoping J-05, not a gap in this iteration.

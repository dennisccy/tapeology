# Phase goal-desk-iter-11 — UX Regression Review

**Date:** 2026-07-28

**Verdict:** UX-REGRESSION-PASS

---

## New Capability Discoverability

**Capability: durable "Top-up Runs" history panel on `/desk`.**

- **Navigation path:** Home (Cockpit `/`) → **Desk** top-nav link (1 click) → the panel is already
  present in the DOM, reached by ordinary scrolling — no second click, no tab, no accordion, no
  hidden toggle. Verified directly in `apps/frontend/app/desk/page.tsx:1245-1280`: the new
  `<section aria-label="Top-up runs">` is rendered as a **sibling after**, not nested inside, the
  screen-state ternary (loading / unavailable / not-computed-yet / populated) — so it is present in
  **every** reachable page state, not gated behind a screen ever having been computed. This matches
  what the dev handoff's "interpretation call 2" claims, and I confirmed it by reading the code
  rather than taking the claim at face value.
- **Screenshot verification:** the raw evidence PNGs are full-page captures (1585×5412–5518px) that
  downscale past legibility in a standard view, so I cropped the bottom ~1700px of each to check the
  actual rendered section directly (not just trust the text report). Confirmed:
  - Empty state (`UT-02-empty-state.png`, `TC-12`-equivalent content): "TOP-UP RUNS" panel with the
    same `∅`-glyph `EmptyState` pattern used elsewhere, text "No top-up runs recorded yet."
  - Populated state (`UT-03-04-05-populated-topup-runs.png`): 3-row table + "LATEST RUN — 2026-07-28
    · TOPUP-2026-07-28-B5BB6C17323D" detail block with "404 of 404 pairs attempted", "0 reused · 403
    fetched · 1 failed", and "AAPL 4h — no data for that window" all legible.
  - Unreached-pairs state (`UT-06-partA-unreached-pairs.png`): "3 of 404 pairs attempted … 401 pairs
    not reached" rendered in amber.
  - Backend-outage state (`UT-01-backend-unreachable.png`): the nav bar itself discloses
    "navigation unavailable — backend unreachable", AND the Top-up Runs panel shows its own
    independent "Backend unreachable — is the API running?" box, separate from the screen panel's
    identical box above it — two honest failures, not one masking the other, not a blank space.
- **Label clarity:** "Top-up Runs" is self-descriptive and follows the same sentence-case aria-label
  convention already used by sibling sections ("Screen history", "Skipped members"). The run ID
  format (`topup-2026-07-28-b5bb6c17323d`) is technical-looking but consistent with the page's
  pre-existing convention of showing raw snapshot/checksum IDs (e.g., `universe-2026-07-25-…`,
  `08e471b10130e1e2`) in the Provenance and Screen History sections — not a new pattern, not
  confusing relative to the rest of this operator-facing tool.
- **Feedback when used:** no new interactive control ships this iteration (by design — pure
  disclosure of what the existing Top-up button already produces). The visual feedback is the panel
  auto-refreshing itself: `page.tsx:1111-1124` re-fetches `fetchDeskTopupRuns()` exactly once when
  the existing top-up-compute poll observes a terminal state, mirroring the screen-compute poll's
  identical established pattern. Browser-QA's UT-07 independently confirmed row count 2→3 and the
  Latest-run block updating to the new run's id with no manual reload.
- **2-click assessment:** effectively 1-click-plus-scroll. `/desk` has grown long (six stacked
  sections), so reaching the very bottom takes meaningful scrolling — but this is scrolling on a
  single already-loaded page, not additional navigation, and UT-09 (a dedicated discoverability
  test) explicitly verified plain-scroll reachability with no obscure interaction. Not flagged as
  undiscoverable (see Recommendation for a non-blocking note on the trend).

No hidden or undiscoverable capabilities found.

---

## Regression Risk

`apps/frontend/app/desk/page.tsx` is the shared file hosting J-01/J-02/J-03/J-04/J-05/J-08's entire
UI, and it was modified this iteration — the exact shared-component scenario this review exists to
catch.

| Shared element | Prior feature(s) it serves | This iteration's change | Risk |
|---|---|---|---|
| `page.tsx` screen-state ternary (loading/unavailable/not-computed/populated) | J-01, J-03, J-04 | Unchanged; new section appended as a sibling AFTER it, confirmed by direct diff/read of the ternary's own braces | Low |
| `Panel`, `EmptyState`, `LoadingPanel`, `UnavailablePanel` components | Every existing `/desk` section (Briefing, Skipped Members, Screen History, Provenance) | Consumed (new call sites), definitions byte-unchanged — targeted grep for `function Panel`/`function EmptyState`/etc. inside the diff returned zero hits | Low |
| `HEADER_CELL`/`LABEL_CELL`/`NUMERIC_CELL` class constants | Screen History, Briefing tables | Reused verbatim in the new `TopupRunsTable`, definitions untouched | Low |
| `apps/frontend/lib/api.ts` | Every fetch on `/desk`, `/structure`, `/` (Cockpit) | Diff is +29/−0 — one new function (`fetchDeskTopupRuns`) appended; zero existing exported function's signature or body changed | Low |
| `apps/frontend/lib/types.ts` | Same pages as above | Diff is +34/−0 — three new interfaces appended; zero existing interface changed | Low |
| `DeskTopupComputeManager.trigger()` (backend) | J-02's Top-up button + live progress/cancel | Gained a new parameter (`topup_run_store`); grep confirms every call site (`desk_routes.py` ×2, every test fixture) was updated in the same commit — no orphaned old-signature caller found | Low |
| `POST`/`GET /research/desk/topup/compute` response shape | J-02 live progress polling | Confirmed byte-unchanged (dev handoff's own trap-#1 self-check; `self._snapshot` gained no new key) | Low |

**Explicit regression evidence (not just inferred from diff shape):**
- Deterministic golden replay: UT-J-01, UT-J-02, UT-J-03, UT-J-04, UT-J-05, UT-J-07, UT-J-08 all
  PASS (`reports/phase-goal-desk-iter-11-regression-replay-results.md`, 7/7).
- UT-08, a test written specifically to check "every pre-existing `/desk` section unaffected",
  independently re-verified Provenance, Briefing (8 columns, 63 rows), Skipped Members (38 rows),
  Screen History drill-through-and-revert, and the Run Screen button — PASS.
- UT-J-06 (MCP 17-tool contract) re-run green, 34/34 pytest — the new route reaches MCP through the
  existing `/research/` allowlist with zero `_STATIC_PATHS` addition, so J-06 is unaffected.
- Full backend suite: 1367 passed / 8 skipped (net +21 over the 1346/8 floor), 0 failures.
- `Config().config_fingerprint()` unchanged at `08e471b10130e1e2`; `git diff --stat` empty for
  `tradability.py`/`levels.py`/`bars.py`/`StructureChart.tsx`.

No potential regressions found beyond the standard "shared file touched" surface, and that surface
is backed by both static (diff) and dynamic (replay + live browser) evidence.

---

## UI vs Backend Parity

1:1 parity — every field the new `GET /research/desk/topup/runs` contract serves is rendered
somewhere in the new UI:

| Backend field | UI surface |
|---|---|
| `runs[].{started_utc→date, id, state, pairs_attempted/pairs_total, universe_snapshot_id}` | `TopupRunsTable` row (`desk-topup-run-*` testids) |
| `latest.state`, `latest.pairs_attempted`/`pairs_total` | `LatestTopupRunDetail` header stats |
| `latest.outcomes` reused/fetched/failed counts | "`N` reused · `N` fetched · `N` failed" counts string |
| `latest.outcomes[outcome="failed"].detail` (verbatim) | "Failed pairs (`N`)" list, untruncated |
| `pairs_total − pairs_attempted` (derived, honest) | "`N` pairs not reached" amber note, absent when zero |

The two items `user-visible-changes.md` lists under "Not Visible Yet" were checked against the
backend contract in `blueprint.md` rather than taken on faith, and both are genuine backend-shape
limits, not UI gaps masking an available capability:
- **Per-outcome breakdown for non-latest runs:** the backend's own `runs` list is explicitly
  meta-only by Data-Contract design ("NEVER the full `outcomes` array... mirrors the screen list's
  meta-only convention") — there is no `outcomes` value sitting in the backend response that the UI
  is failing to render. Correctly and explicitly disclosed in the report rather than silently
  omitted.
- **A real credentialed vendor top-up run:** explicitly out of scope this iteration (goal.md/plan.md
  OUT OF SCOPE), an operator-run act by design across this whole era — not a backend capability that
  exists today and is hidden from the UI.

No UI vs backend parity gaps found.

---

## Flags

### Hidden Capabilities
None.

### Undiscoverable Capabilities
None.

### Potential Regressions
None confirmed. See Regression Risk table above for the shared surfaces checked.

### Visual Consistency
No inconsistencies found. Verified directly against cropped screenshots (not just the text report):
- The "TOP-UP RUNS" panel header renders with the same uppercase/tracked/gray styling as "SCREEN
  HISTORY" and "RUN SCREEN / TOP-UP" immediately above it in the same screenshot — browser-QA's own
  UT-09 additionally confirmed the underlying class string is byte-identical between "Top-up Runs"
  and "Screen History" headings.
- Table borders, row spacing, and cell alignment in `TopupRunsTable` match the existing
  `HEADER_CELL`/`LABEL_CELL`/`NUMERIC_CELL`-driven tables elsewhere on the page (Screen History,
  Briefing) — same constants, not visually-similar-but-separately-defined values.
- The one new color usage — amber `text-amber-200/70` on "N pairs not reached" — reuses the same
  amber token the page already uses for cancelled/warning states (e.g.
  `desk-topup-compute-cancelled`); no new color/gradient/glow/animation was introduced, consistent
  with the plan's explicit "dense data table, not a hero element" instruction.
- No arbitrary Tailwind values found in the diffed JSX (`git diff 472f0ce -- page.tsx` shows only
  the pre-existing constant classes reused).

---

## Recommendation

No action required for this iteration.

Two non-blocking notes for whoever plans the next `/desk`-touching iteration:

1. **Growing page length.** `/desk` is now six stacked sections and roughly 5500px of content in a
   populated state (Provenance, Briefing, Skipped Members, Screen History, Run Screen/Top-up
   controls, Top-up Runs), and every iteration since J-04 has appended a new section rather than any
   iteration introducing in-page jump-nav, collapsing, or pagination. Today every capability is still
   reachable by plain scrolling (UT-09 confirmed this explicitly), so this is an observation, not a
   flag — but the trend is worth watching before it becomes a genuine discoverability problem.
2. **Evidence-quality nit, not a functional gap:** UT-07's "no flash of empty state during the
   auto-refresh transition" sub-clause was verified via before/after DOM snapshots rather than
   continuous capture, per the QA report's own honest disclosure. The core auto-refresh contract
   itself (row count, latest-run id, button label reverting) is independently and solidly evidenced,
   so this does not affect the verdict.

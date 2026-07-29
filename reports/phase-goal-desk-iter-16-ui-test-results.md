# UI Test Results (merged)

**Date:** 2026-07-29
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 20/23 journeys passed (3 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-03 | The screen — pinned inputs, append-only snapshot, deterministic rank | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-16-evidence/J-03-verify.png |
| UT-J-04 | The /desk briefing page | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-16-evidence/J-04-verify.png |
| UT-J-05 | Ledger history + drill-in to /structure | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-16-evidence/J-05-verify.png |
| UT-J-07 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-16-evidence/J-07-verify.png |
| UT-J-08 | Every ranked briefing row names the bar its distance was measured from | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-16-evidence/J-08-verify.png |
| UT-J-09 | Every top-up run leaves an append-only record of what it attempted | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-16-evidence/J-09-verify.png |
| UT-J-10 | The coverage the briefing shows is the coverage the frozen store can prove | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-16-evidence/J-10-verify.png |
| UT-J-11 | Every ranked briefing row states how much completed history its wall was measured over | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-16-evidence/J-11-verify.png |
| UT-01 | `/desk` loads without errors | smoke | P1 | "Desk" heading + all 7 panel headings visible, no error panel, no console errors | Navigated to `/desk`; "Desk" heading present; Provenance, Briefing, Skipped Members, Screen History, Run Screen/Top-up/Reconcile Index, Top-up Runs, Index Reconciliation all rendered; console showed only a React DevTools info line, no errors | PASS | `reports/qa/goal-desk-iter-16-evidence/UT-01-result.png` |
| UT-02 | Earlier same-date entry opens its own recording | happy-path | P1 | Only clicked row highlighted; "not the latest" banner; Provenance shows `screen-2026-07-27-936543601e75` / `2026-07-27T21:42:14.636275Z`; NFLX `1d` badge dark | Clicked the row; `eval()` confirmed only that row's `data-selected="true"`; banner text "not the latest" present; Provenance text matched exactly; NFLX row's coverage badge `data-has-bars="false"` | PASS | `reports/qa/goal-desk-iter-16-evidence/UT-02-result.png` |
| UT-03 | Later same-date entry opens a distinct recording | happy-path | P1 | Highlight moves to this row only; Provenance updates to `screen-2026-07-27-3ad3c57aa6ba` / `2026-07-28T21:30:16.111871Z`; NFLX `1d` badge lit; Screen date still `2026-07-27` | Clicked the row; only it `data-selected="true"` (prior row no longer selected); Provenance text matched exactly (Screen date `2026-07-27`, id/recorded-at updated); NFLX `data-has-bars="true"` (flipped from UT-02) | PASS | `reports/qa/goal-desk-iter-16-evidence/UT-03-result.png` |
| UT-04 | "recorded" column shows distinct timestamps | smoke | P1 | "recorded" header between "date"/"rows"; every row non-empty; the two `2026-07-27` rows show two different values | Page text dump showed header row `date recorded rows skipped provenance`; the two `2026-07-27` rows read `2026-07-27T21:42:14.636275Z` and `2026-07-28T21:30:16.111871Z` respectively — distinct | PASS | `reports/qa/goal-desk-iter-16-evidence/UT-04-result.png` |
| UT-05 | Default highlight tracks recorded-at, not date | ux | P1 | Only the bottom row (`2026-07-28`, recorded `2026-07-29T02:07:39.867805Z`) highlighted by default; the `2026-07-29`-dated row NOT highlighted | `eval()` over all 6 `tr[data-screen-id]` on fresh load: only `screen-2026-07-28-ac07c9581a4f` had `data-selected="true"`; all 5 others (including the `2026-07-29`-dated `screen-2026-07-29-ce0d82b8e9bf`) read `"false"` | PASS | `reports/qa/goal-desk-iter-16-evidence/UT-05-result.png` |
| UT-06 | Provenance shows exact snapshot identity | happy-path | P1 | Row order Snapshot id/Recorded at/Universe snapshot/Screen date/As of/Config fingerprint/Bar-store signature; id `screen-2026-07-28-ac07c9581a4f`; recorded-at `2026-07-29T02:07:39.867805Z`; screen date `2026-07-28` (earlier than recorded-at's day) | Fresh-load text dump matched every field/order exactly; "Screen date" `2026-07-28` vs "Recorded at" day `2026-07-29` confirmed the divergence | PASS | `reports/qa/goal-desk-iter-16-evidence/UT-06-result.png` |
| UT-07 | Default note reads "most recently recorded" | ux | P1 | Exact note text; no "latest date" framing; no advice/urgency language; `2026-07-29`-dated row visible in history | Fresh-load text dump contained the note verbatim: "This is the most recently recorded screen (by recorded-at time), not necessarily the latest screen date — an earlier same-date recording can still exist and be opened from Screen History below." The `2026-07-29`-dated row (`screen-2026-07-29-ce0d82b8e9bf`) is present in the table | PASS | `reports/qa/goal-desk-iter-16-evidence/UT-07-result.png` |
| UT-08 | Note toggles correctly; "Latest" reverts fully | regression | P2 | After clicking `2026-07-25` row: note gone, banner shown, Provenance = that row's id/recorded-at. After "Latest": banner gone, note reappears (exact text), Provenance reverts to `screen-2026-07-28-ac07c9581a4f`/`2026-07-29T02:07:39.867805Z`, bottom row re-highlighted | Clicked `2026-07-25` row: `desk-provenance-latest-note` absent, banner text present, Provenance = `screen-2026-07-25-e184a7dc2f86`/`2026-07-25T11:45:58.551296Z`. Clicked "Latest" button (`data-testid="desk-history-latest-button"`): banner gone, note text reappeared verbatim, Provenance reverted to the exact UT-06 values, `data-selected="true"` back on `screen-2026-07-28-ac07c9581a4f` | PASS | `reports/qa/goal-desk-iter-16-evidence/UT-08-result.png` |
| UT-09 | Single-recording dates still open correctly | regression | P1 | Only that row highlighted; Provenance id `screen-2026-06-22-3ecd45c062c7`, screen date `2026-06-22`; Briefing updates; no fetch-error note | Clicked `2026-06-22` row: `data-selected="true"` only on it; Provenance text matched exactly; `desk-history-fetch-error` element absent (`errPresent: false`) | PASS | `reports/qa/goal-desk-iter-16-evidence/UT-09-result.png` |
| UT-10 | No false-positive integrity note with clean data | regression | P2 | No "failed an integrity check" note in any of the 3 panels; no empty-array placeholder | Full-page text dump showed Screen History, Top-up Runs ("No top-up runs recorded yet."), and Index Reconciliation panels with no amber integrity-error text anywhere | PASS | `reports/qa/goal-desk-iter-16-evidence/UT-10-result.png` |
| UT-11 | Screen History integrity-error note visible | error | P2 | Amber note naming a planted corrupt screen-record file, in a scoped rig | Not executed — see Skipped Tests | SKIPPED | none |
| UT-12 | Top-up Runs integrity-error note visible | error | P2 | Amber note naming a planted corrupt top-up-run file, in a scoped rig | Not executed — see Skipped Tests | SKIPPED | none |
| UT-13 | Index Reconciliation integrity-error note visible | error | P2 | Amber note naming a planted corrupt reconcile-run file, in a scoped rig | Not executed — see Skipped Tests | SKIPPED | none |
| UT-14 | No Universe ledger section exists (documented gap) | ux | P3 | No universe-snapshot list/table anywhere on the page outside the single Provenance "Universe snapshot" row | Full-page text dump (top to bottom) showed "Universe snapshot" exactly once, inside the Provenance panel; no separate Universe list/table section anywhere else on the page | PASS | `reports/qa/goal-desk-iter-16-evidence/UT-14-result.png` |
| UT-J-06 | MCP contract v3 — 17 read-only tools (regression journey, goal.md) | regression | P1 | MCP server advertises exactly 17 tools; `desk_universe`/`desk_screen` byte-identical to curl; `get_endpoint` proxies `/research/desk/screen` verbatim; MCP suite green | Journey is explicitly "Keyless; automated" in goal.md (not browser-verifiable) — ran `apps/backend/.venv/bin/python -m pytest tests/test_mcp_server.py -q` against the running :8301 rig's codebase: 36/36 tests passed, including the `EXPECTED_TOOLS` 17-tuple equality assertion (`tape_state, tape_features, tape_history, datasets, bars, levels, tradability, setups, backtests, strategies, edge_report, desk_universe, desk_screen, pnl_ledger, taxonomy, ui_route_map, get_endpoint`) and byte-identity/honest-error clauses for every tool. Separately confirmed live via curl against :8301 that `GET /research/desk/screen?id=screen-2026-07-27-936543601e75` returns that exact record (id/screen_date/created_utc/63 rows matched the on-disk listing) — the same `?id=` path `get_endpoint` proxies | PASS | none |

## Skipped Tests

### UT-11 — Screen History integrity-error note visible

**Verdict:** SKIPPED
**Reason:** Not executed — see Skipped Tests

### UT-12 — Top-up Runs integrity-error note visible

**Verdict:** SKIPPED
**Reason:** Not executed — see Skipped Tests

### UT-13 — Index Reconciliation integrity-error note visible

**Verdict:** SKIPPED
**Reason:** Not executed — see Skipped Tests

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-29


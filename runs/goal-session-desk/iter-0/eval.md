# Iteration 0 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

The baseline landed exactly as the spec predicted and — critically — with **zero source changes**
(`git diff --stat 047c38e -- apps/` and `git status --short -- apps/` both empty, re-run by me).
J-01–J-06 are recorded **failing** (the desk era is genuinely not started: every
`/research/desk/*` probe 404s, `UI_ROUTES` has 2 entries, `EXPECTED_TOOLS` has 15, no desk module/
fixture/Config field/`.data/universe/` exists — each claim re-verified independently, not taken
from the handoff). J-07 is recorded **partial**, not passing: its KEPT-product half is fully
browser-evidenced (suite 1169p/7s, pin `08e471b10130e1e2`, cockpit sim + historical band overlay,
`/structure` AAPL wall, Case Study drill-in, honest Edge Report), but two clauses of its own
acceptance text — "nav = exactly three routes" and "MCP = exactly 17 tools" — are literally
unmet today (2 routes, 15 tools) and land with J-04/J-06.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Universe ingestion | (none — first eval) | failing | `reports/phase-goal-desk-iter-0-ui-test-results.md` UT-J-01 (`GET`/`POST /research/desk/universe*` → 404; zero `desk` matches under `apps/backend/app/research/`, `tests/fixtures/`; no `desk_universe_*` Config field; no `.data/universe/`) — all re-verified by evaluator |
| J-02 Coverage + top-up | (none) | failing | UT-J-02 (`/research/desk/coverage` + both top-up POST sub-paths → 404; whole-tree grep `research/desk\|desk_universe\|desk_screen` in `apps/backend/app/` → zero matches, re-run by evaluator) |
| J-03 Screen + ledger | (none) | failing | UT-J-03 (`GET /research/desk/screen`, `POST .../screen/compute` → 404; no `desk_screen.py`) |
| J-04 `/desk` briefing page | (none) | failing | `reports/qa/goal-desk-iter-0-evidence/J-04-desk-404.png` — Next.js "404 · This page could not be found." with nav showing exactly **Cockpit · Structure**; `/meta/ui-routes` = 2 objects |
| J-05 History + `/structure` prefill | (none) | failing | `reports/qa/goal-desk-iter-0-evidence/J-05-structure-no-prefill.png` — `/structure?symbol=AAPL&asof=2026-06-22` renders Symbol/As-of inputs showing only placeholders, Load disabled, "Choose a symbol and an as-of time, then Load…"; `useSearchParams` grep → 0 hits |
| J-06 MCP 17 tools | (none) | failing | UT-J-06 — `tests/test_mcp_server.py` `EXPECTED_TOOLS` re-parsed by evaluator: exactly 15 names, `desk_*` absent |
| J-07 Kept-product sentinel | (none) | **partial** | `J-07-cockpit-sim-buyer-control.png` (Buyer Control 0.950, `scenario: buyer_control`, live 10s bars), `J-07-cockpit-tape-30s-switch.png` (30s pressed), `J-07-cockpit-historical-1d-band-overlay.png` (real SIP AAPL 1d candles + `R A · 171 · round · 302.20` / `R A · 97 · round · 300.10` overlay), `J-07-structure-aapl-wall.png` (`resistance 300.11–302.2 Class A score 171`), `J-07-structure-case-study-drillin.png` (AAPL · 2025-01-02, forward returns, "No recorded tape for this event.", "Edge report not computed yet."); suite 1169p/7s; pin `08e471b10130e1e2` re-printed live by evaluator. **Unmet clauses:** nav = 3 routes (is 2), MCP = 17 tools (is 15) |

Screenshot-vs-prose check: every screenshot I opened corroborated its prose row; nothing was
overturned. Cross-page single-source-of-truth held incidentally — the cockpit overlay's
`302.20`/`300.10` band edges match `/structure`'s `300.11–302.2` / `298.02–300.1001` reads for the
same symbol and as-of.

**Why J-07 is `partial`, not `passing`/`already_passing`.** Its `docs/goal.md` acceptance text
reads: *"full suite green under the unchanged pin; every browser step evidenced by screenshot;
kept-route byte-identity holds; nav = exactly three routes; MCP = exactly 17 tools; zero
out-of-inventory changes in the cumulative diff."* Four of six clauses are evidenced; two are
structurally unsatisfiable before J-04/J-06 ship. `partial` is the schema-correct status ("only
some assertion steps passed"), and recording `already_passing` would assert clauses I can see are
false today. The iteration spec explicitly delegated this call to me. **Safety note for later
iterations:** because J-07 starts at `partial`, a kept-product break would not auto-trip the
tree's `passing → failing` REGRESSION rule — but it *is* a critical violation of rail 3 ("Frozen
foundations … every KEPT surface's behaviour stays byte-identical"), which reaches REGRESSION by
the anti-goal path. Treat any kept-behavior FAIL as a halt regardless of J-07's recorded status.

## Anti-goal Check

Sources: `runs/goal-session-desk/iter-0/scan-report.md` (**CLEAN** — no secret/dependency/license
findings) + `iter-diff.md` (2 files, both docs: `docs/goal.md`, `docs/goal-archive/goal-2026-07-25.md`
— these are the era-open commit `047c38e` itself, i.e. human goal authoring, not iteration work) +
my own `git diff --stat 047c38e -- apps/` (empty) and `git status --short` (only `docs/handoffs/`,
`docs/phases/`, `reports/`, `runs/` bookkeeping).

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets/credentials | OK | scan-report CLEAN; no new config/env file in the diff file list; no credential work occurred |
| Paid/external SaaS | OK | scan-report reports no dependency findings; zero manifest changes (no `apps/` diff at all) |
| License changes | OK | scan-report CLEAN; no LICENSE/license-field in the changed-file list |
| Fabricated/substituted data | OK | Nothing ingested or served. Positively evidenced honesty instead: SIM-BUYER showed "No recorded bars for SIM-BUYER" / "No tradable map for SIM-BUYER" rather than inventing a band; drill-in showed "No recorded tape for this event." |
| 1 No execution path | OK | Zero code diff; `test_no_execution_path.py` inside the green 1169-pass suite |
| 2 No profit claims / no advice | OK | Zero copy diff; `test_copy_discipline.py` green in-suite; page footer still "Descriptive only — not trading advice" |
| 3 Frozen foundations (kept surfaces byte-identical) | OK | Zero `apps/` diff; suite counts match the era-open 1169p/7s exactly; pin `08e471b10130e1e2` re-printed live; both charts render as shipped (screenshots) |
| 4 Hold-out-only promotion | OK | No champion/gate/backtest touch; `/structure` Registry still shows champion `v1` / `default` |
| 5 No lookahead | OK | No computation changed; `/structure` map bars still stamp "prior completed session close: 2026-06-18T04:00:00Z" for the 06-22 as-of |
| 6 Single source of truth | OK | No new value introduced; cockpit-vs-`/structure` band reads cross-matched (above) |
| 7 Deterministic and seeded | OK | No code change; no new randomness path |
| 8 Read-only MCP | OK | Tool list unchanged at 15; no write tool added (`EXPECTED_TOOLS` re-parsed) |
| 9 Immutable data | OK | No dataset/bar deleted, re-tagged, or perturbed. Only derived accelerator caches warmed, inside the sanctioned `.data/scoped_browser_qa` QA dir |
| 10 Persistence stays scoped | OK | Browser QA ran against the scoped QA data dir; no ambient recording; no live stream persisted |
| Membership is never a signal | OK | No universe code exists yet (nothing to violate) |
| Snapshots append-only and pinned | OK | No snapshot subsystem exists yet |
| Every run is an explicit operator act | OK | No scheduler/cron/daemon added; positively re-confirmed: page-load GET left Edge Report at "Edge report not computed yet." with an operator Compute button |
| Briefing describes, never advises | OK | No desk copy exists; copy-discipline lint green unmodified |
| No new statistics/gates/strategies | OK | Zero diff; registry still `v1` + `structure_tape` + `structure_tape_map` |
| The demolition stays demolished | OK | Nav = exactly Cockpit · Structure (J-04 screenshot); no journal-era route/page returned |
| The ledger never holds orders | OK | No desk record type exists |
| Suite stays keyless and hermetic | OK | 1169p/7s ran keyless; no network test; the live Wikipedia fetch was correctly NOT attempted |
| Fingerprint pin does not move | OK | `08e471b10130e1e2` verified live by me from `apps/backend` |
| Enhancement loop stays inside its box | OK | Proposer did not run; `docs/goal.md` `AUTO:journeys` block is empty (lines 461–463) and the file is unmodified in the working tree |

**Violations: none.** No critical, no minor.

**Coherence:** `runs/goal-session-desk/iter-0/coherence.md` is **absent** — no coherence step ran
this lean baseline (`.steps/` holds only decomposer, developer, review-1, browser-qa). Not a
`COHERENCE-FAIL`, so it drives nothing this iteration (GOAL_ACHIEVED was structurally impossible
anyway), but recording it honestly: per the decision tree a *missing* coherence audit counts as
NOT clean, so a future GOAL_ACHIEVED will require a real, clean coherence audit — the era's first
one should run on the iteration that actually adds the desk surface/owners (J-01+).

## Next-Step Recommendation

**Target J-01 alone** (universe vendor seam + parser contract + universe store + committed fixture
+ `POST /research/desk/universe/fetch` and `GET /research/desk/universe`). It is first in
`docs/goal.md`'s stated dependency order and the hard unblocker for J-02–J-06 — nothing else can
exist until a registered universe snapshot does. Nothing about it is human-blocked: the whole
acceptance is keyless/fixture-scoped (the live Wikipedia fetch is a separately-reported
operator-run act, never a gate).

**Run iteration 1 at `full` depth.** J-01 is a data-model iteration on three axes at once — a new
frozen-JSON-plus-derived-index store format with append-only/immutability semantics (T-3: must not
route through `datasets.py`), the first §0.4 **Path A** Config fields (`desk_universe_source_url`,
`desk_universe_min_members`, `desk_universe_max_members`) which each need exclusion-set entry +
stability test + counter-test + payload provenance *in the same commit* (T-5), and a
parser-honesty contract that must fail loudly rather than ever emit a partial/guessed list (T-1,
plus T-2 `BRK.B → BRK-B` normalization and dual-class dupes). That combination is exactly what the
audit/closure lanes exist for; a lean pass would carry the Path-A and immutability checks on the
developer's word alone.

Two concrete carry-forwards for iteration 1:

1. **Fix the J-07 golden before the replay lane runs it.**
   `runs/goal-session-desk/journey-scripts/J-07.json` step 8 asserts the text `300.11` — an
   async, cache-warmth-dependent value — on the 15 s default timeout. A prior era lost a full
   iteration to exactly this (headless matcher misses async-rendered text). Re-point step 8 at a
   statically-rendered string on the loaded `/structure` shell, or widen its timeout; if the
   replay lane FAILs J-07 on step 8 while the LLM lane passes it, the merged results file wins and
   the FAIL is a golden false negative, not a kept-product regression.
2. **Budget for the cold `/research/setups` scan.** This iteration measured ~9–11 min cold vs
   0.84 s warm on the scoped QA backend (`reports/phase-goal-desk-iter-0-ui-test-results.md`
   § Supporting probe evidence). Warm the scoped backend before browser QA, and read it as the
   live precedent for J-02's own "coverage GET is index-read fast, no store re-hash" requirement.

## Halt Justification (if halting)

Not halting. Not `REGRESSION` (no prior passing journey exists to regress; no anti-goal violation).
Not `STALLED` (no blocker is human-owned — J-01 is ordinary keyless build work, and the spec's own
NOTES confirm no journey needs credentials or network access). Not `GOAL_ACHIEVED` (6 failing + 1
partial). Not `ESCALATE` (the review lane passed, nothing proceeded fail-open, no journey has
failed twice, and no ambiguity was *uncovered* — the depth bump to `full` is a planned-complexity
call carried on the recommendation line, not an escalation).

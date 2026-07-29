# Iteration 18 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

The new `opposite` column is real, it is on screen, and its numbers are correct: I opened the
screenshot myself and re-computed every value from the price files. But the page does not always
name the nearest wall on the other side of price, which is exactly what this journey's own title
promises. The goal file says "pick the closest one first"; the code picks "the best-graded one
first" instead. On the owner's real 63-name screen the two rules disagree on 2 rows, where the page
would show a wall more than twice as far away as the closest one. The guided film for this feature
is also wrong: three of its six pictures are of a different page. J-01 to J-13 all still work.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 | passing | passing | reports/phase-goal-desk-iter-18-ui-test-results.md UT-J-01 PASS + reports/qa/goal-desk-iter-18-evidence/J-01-verify.png |
| J-02 | passing | passing | UT-J-02 PASS + reports/qa/goal-desk-iter-18-evidence/J-02-verify.png |
| J-03 | passing | passing | UT-J-03 PASS + reports/qa/goal-desk-iter-18-evidence/J-03-verify.png |
| J-04 | passing | passing | UT-J-04 PASS + reports/qa/goal-desk-iter-18-evidence/J-04-verify.png |
| J-05 | passing | passing | UT-J-05 PASS + reports/qa/goal-desk-iter-18-evidence/J-05-verify.png |
| J-06 | passing | passing | UT-J-06 PASS (no browser surface) + evaluator's own `len(app.mcp.TOOL_NAMES)` = 17 |
| J-07 | passing | passing | UT-J-07 PASS + reports/qa/goal-desk-iter-18-evidence/J-07-verify.png |
| J-08 | passing | passing | UT-J-08 PASS + reports/qa/goal-desk-iter-18-evidence/J-08-verify.png |
| J-09 | passing | passing | UT-J-09 PASS + reports/qa/goal-desk-iter-18-evidence/J-09-verify.png |
| J-10 | passing | passing | UT-J-10 PASS + reports/qa/goal-desk-iter-18-evidence/J-10-verify.png |
| J-11 | passing | passing | UT-J-11 PASS + reports/qa/goal-desk-iter-18-evidence/J-11-verify.png |
| J-12 | passing (evidence_makeup) | passing (evidence_makeup carried) | UT-J-12 PASS + J-12-verify.png; iter-16 crop still not re-taken |
| J-13 | passing (evidence_makeup) | passing (evidence_makeup carried) | UT-J-13 PASS + J-13-verify.png; the populated re-film this iteration owed did not happen |
| J-14 | (new) | **partial** | reports/qa/goal-desk-iter-18-evidence/UT-03-result.png (near 0.00 bps + far 1208.73 bps in one frame, fixture-scoped rig, origin asserted), UT-05/UT-06, rows UT-01..UT-10 PASS; evaluator's own re-derivation from `/home/dennis-chan/.cache/iad/iad.goal-desk-iter-18.3302867/scoped-rig-desk18/screen/screen-2026-06-22-5c2189ff978a.json`. Two unmet clauses — see below |

### Why J-14 is `partial`, not `passing`

1. **Selection rule (product).** `docs/goal.md` J-14 names *the nearest* band on the other side —
   in the title, in step 1's first sentence, and in step 1's explicit key ("distance ascending,
   then class rank descending"). The shipped `_select_opposite_band`
   (`apps/backend/app/research/desk_screen.py:269`) delegates to `_select_best_band`, whose key is
   class-first (`-class_rank, distance, -score`). The iteration spec
   (`docs/phases/goal-desk-iter-18.md`, Backend bullet 1) restated the rule as class-first, and
   reviewer/QA/coherence/audit all checked the restatement, so nobody compared it back to
   `docs/goal.md`. I measured the difference myself against the canonical owner
   (`compute_tradability`) for all 63 ranked members of the owner's own screen at
   `as_of 2026-07-29T23:59:59Z` — the snapshot `docs/goal.md`'s own rationale cites:
   the two rules pick a different band on **2 of 63** rows —
   HONA (shipped: class A at 336.96 bps; nearest: class B at 153.67 bps) and
   META (shipped: class A at 232.58 bps; nearest: class C at 92.05 bps).
   goal.md's named examples do agree (BRK-B 0.61 bps, ISRG 0.00 bps unclassified, CMCSA 0.00 bps
   class B). Both the backend docstring (`desk_screen.py:89`) and the frontend comment
   (`apps/frontend/app/desk/page.tsx:273`) assert "the nearest band", which the shipped rule does
   not deliver.
2. **Walkthrough (evidence).** J-14's acceptance and DoD item 4 require a `[NEW]`-flagged
   walkthrough over POPULATED rows. `reports/phase-goal-desk-iter-18-demo-results.md` reads
   `RECORDED_WITH_NOTES`; I opened every frame: `step-03/04/05.png` are byte-identical
   (`7cab9fb7…`) and show `/structure` with an IBM autocomplete dropdown, `step-01/07.png` are
   byte-identical `/desk` frames cropped before the new column. The `opposite` column appears in
   **zero** of six frames. This alone would be a capture defect only (`evidence_makeup`), never a
   blocker — it does **not** drive this verdict; item 1 does.

Everything else in J-14 verified passing by me directly: the scoped snapshot's file checksum
recomputes; 6/6 ranked rows carry both fields and 0/97 skip rows do; each `opposite_band`'s
`side`/`band_class`/`price_low`/`price_high`/`band_score` is byte-identical to the matching band in
`compute_tradability`'s own output; each `distance_bps` reproduces through the same `_distance_bps`
helper against the row's own `reference_close`; `bands_by_class` equals my own per-class recount and
sums to `len(bands)` on all 6 rows; the opposite side is never the ranked side; the MCP surface is
exactly 17 tools.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials | OK | `iter-18/scan-report.md` CLEAN; the product diff is 6 files, none a config/env file |
| Paid / external SaaS | OK | no manifest touched (`package.json`, `requirements*.txt`, `pyproject.toml` absent from the diff); no new runtime dependency |
| License changes | OK | scan-report CLEAN; no LICENSE file in the diff |
| Fabricated / substituted data | OK | both new values are copied verbatim out of `compute_tradability`'s own band dicts — I re-derived all 6 rows against the canonical owner, byte-identical |
| Single source of truth *(critical)* | OK | one owner (`desk_screen.py`), one endpoint (`GET /research/desk/screen`); coherence.md COHERENCE-PASS; the frontend renders only served fields (arithmetic guard extended + counter-tested, `test_desk_ui_guards.py:484-539`) |
| Immutable data *(critical)* | OK | `find apps/backend/.data/bars -newermt "2026-07-29 09:12:41"` → **0 of 369** files; only derived caches (`bar_index.db-wal/-shm`, `tradability_cache.db`) touched |
| Snapshots append-only and pinned *(critical)* | OK | all 6 ambient screen snapshots pre-date the run (newest mtime 2026-07-29 03:07:39 vs start 09:12:41Z) and `grep -l opposite_band apps/backend/.data/screen/*.json` returns nothing — nothing backfilled; the new snapshot was written to a scoped temp rig and carries all five pins |
| Every run an explicit operator act *(critical)* | OK | both fields are bound inside `compute_screen` only; no page-load GET computes; no scheduler/cron added |
| The briefing describes, never advises *(critical)* | OK | new copy is `opposite <side> <class> <low>–<high> · <n> bps`, `no band on the other side`, `opposite wall not recorded in this snapshot`, `bands by class A n · B n · C n · unclassified n`; `test_copy_discipline.py` byte-unmodified and green |
| No new statistics, gates, or strategies *(critical)* | OK | `bands_by_class` is a plain count; `opposite_band` copies canonical values and reuses the existing `_distance_bps`; no threshold, grade, or probability added |
| No lookahead *(critical)* | OK | both values come from the same `compute_tradability(as_of)` result the row already used |
| Read-only MCP *(critical)* | OK | `len(TOOL_NAMES)` = 17 on my own import; zero MCP code change |
| Fingerprint pin does not move *(critical)* | OK | `Config().config_fingerprint()` → `08e471b10130e1e2` on my own run; `git diff HEAD -- app/config.py` empty; zero new Config fields |
| Frozen foundations *(critical)* | OK | zero diff vs HEAD on `tradability.py`, `levels.py`, `bars.py`, `bar_index.py`, `desk_coverage.py`, `config.py`, `meta.py`, `mcp/__init__.py`, `StructureChart.tsx`, `PriceChart.tsx`, `test_copy_discipline.py`, `app/engine/` |
| Suite stays keyless and hermetic *(critical)* | OK | no fixture file changed; the live Yahoo fetch for evidence happened only inside the scoped temp rig (6 bar files under `…/scoped-rig-desk18/bars`), never in a test |
| Enhancement loop stays inside its box *(critical)* | OK | `git diff HEAD -- docs/goal.md` = **+108 / −0**, the J-14 block only, inside the `AUTO:journeys` markers |
| Ledger never holds orders / demolition stays demolished *(critical)* | OK | no order, size, ticket or account concept in the new fields; no journal-era machinery |
| Host-guard caps are law *(critical)* | OK | my own process affinity reads `4-7,12-15` |

No violation, new or open. The three historical entries stay `resolved` and were re-checked by me
this iteration (bar files untouched, snapshots checksum-valid and unmodified, restricted files zero
diff).

Coherence: **COHERENCE-PASS** (`runs/goal-session-desk/iter-18/coherence.md`) — no veto.

## Next-Step Recommendation

Run one more iteration at `full` depth with two pieces of work, both on J-14 "Every ranked briefing
row states where the nearest wall on the OTHER side of price sits":

1. Make the `opposite` column show the **closest** wall on the other side. Today it shows the
   best-graded one instead. This is a one-rule change in
   `apps/backend/app/research/desk_screen.py` (`_select_opposite_band` must sort by distance first,
   then by grade, then by score), plus the stored test comparisons and the two comments that
   already claim "nearest". If the owner would rather keep the grade-first behaviour, the honest
   alternative is to change the wording in `docs/goal.md` and in both comments so nothing claims
   "nearest" — but the goal file as written today asks for closest-first.
2. Re-film the guided walkthrough on a throwaway copy of the data, with a freshly computed screen,
   so the film actually shows the new column with a close wall and a far wall. This also clears the
   older films still owed for J-13 and J-12. Do not start a second copy of the web front end from
   the same source folder while another one is running.

One sentence for the owner: the new "opposite wall" column works and its numbers match your stored
prices exactly, but on 2 of your 63 names it names a wall more than twice as far away as the closest
one — please approve one short run to fix that and to re-film the walkthrough.

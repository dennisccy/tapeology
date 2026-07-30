# goal-desk-iter-23 Audit Report

**Date:** 2026-07-30
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-15's product goal is genuinely achieved, and I verified it against the running system's own real
data rather than the handoffs: the newly recorded 100-row screen carries all three fields on every
ranked row with zero sum-invariant violations, and I re-derived `member_count`/`round_number`/the
timeframe tally from a fresh `compute_tradability` call for three symbols (ORCL 2, AMT 5, MA 121 +
`round_number: true`) — byte-identical, including key order. The backend change is a 3-line verbatim
copy plus one 5-line tally helper off the SAME `best` band dict, with zero diff to the rank key and
every out-of-scope file. Two gaps remain: the browser/demo evidence was produced against the
**ambient** `apps/backend/.data` store rather than the fixture-scoped rig that the spec's NOTES, DoD
item 6, and goal.md's own acceptance preamble all require (a real screen snapshot was written into
the operator's store), and the new column is the table's 12th — invisible without horizontal scroll
at 1440px, the exact accumulation the iter-18 audit warned about.

---

## 2. DEFINITION OF DONE — verification map

| # | DoD item | How verified |
|---|----------|--------------|
| 1 | J-15 passes via browser-qa-agent | **Full trace (risk: this is the phase's whole purpose).** UT-03 PASS with a real screenshot I read directly: `reports/qa/goal-desk-iter-23-evidence/UT-03-populated-levels-badge.png` shows, in ONE frame, `2 levels · 1h 1 · 1d 1`, `5 levels · 1d 3 · 1h 1 · 4h 1`, `609 levels · 1m 474 · 5m 98 · 1d 28 · 1h 5 · 1w 3 · 4h 1`, and the `round number` badge on `121 levels · 1d 58 · 1h 41 · 1w 8 · 4h 14`. TC-11 (≤5 and ≥100 legible together + badge) is met in that single frame. |
| 2 | J-01..J-14 remain green | Replay 12/13 (`phase-goal-desk-iter-23-regression-replay-results.md`); J-09 FAIL overturned by the LLM lane with live re-execution + `UT-J-09-topup-runs.png` + crops, golden repaired (see B2). J-06 has no UI surface — verified in the LLM lane by code + curl + pytest. |
| 3 | No anti-goal violation introduced | **Full trace (risk class: persistence).** Single source of truth: `desk_screen.py:507-509` reads only `best["member_count"]`/`best["round_number"]`/`best["members"]` off the object `_select_best_band` returned (`tradability.py:361/364`); no second compute, no second store read, no client-side arithmetic (`page.tsx:452-454` is a `join`, nothing else). Append-only: I loaded the ambient store live — 11 snapshots, `integrity_errors == []`, and the 10 pre-existing ones carry **zero** of the three keys (nothing backfilled or rewritten). Read path serves verbatim (`desk_routes.py:352-362`). Fingerprint `08e471b10130e1e2` printed live from `Config()`. No new statistic/gate/threshold anywhere in the diff. |
| 4 | Unit tests pass; no regressions | **Re-run by me:** `cd apps/backend && .venv/bin/python -m pytest tests/ -p no:warnings -q` → exit 0, 1462 outcomes, 8 skipped, zero `F`/`E`. Matches the dev (1454/8) and QA (1454/8) claims exactly. Targeted: `tests/test_desk_screen.py tests/test_copy_discipline.py tests/test_mcp_server.py` → exit 0, 146 passed. |
| 5 | Dev handoff written | Present (`docs/handoffs/goal-desk-iter-23-dev.md`) plus a frontend handoff. |
| 6 | Three fields on every ranked row of a NEW **fixture-scoped** snapshot, byte-identical to canonical | **Full trace — PARTIAL.** Substance proven: `screen-2026-07-30-bad6387963ef` has all three keys on 100/100 ranked rows, counts 1–4,014, 16 rows `round_number: true`, **0** sum violations, the 1 skip row carries none; my independent 3-symbol cross-check against a fresh `compute_tradability` matched exactly. Qualifier **unmet**: the snapshot is in the AMBIENT store, not a fixture-scoped copy — see **B1**. |
| 7 | Legacy screens render the honest copy, checksums unchanged on disk | **Full trace.** UT-04 PASS: all 100 rows of `screen-2026-07-20-ca185294a384` read exactly "composition not recorded in this snapshot", no badge. Checksums: I re-ran `ScreenStore.list()` over the ambient dir — `errors == []` for all 11 files. |
| 8 | Rank order byte-identical to pre-change baseline | **Full trace (the shipped test is weak — see T1).** `_row_rank_key` (`desk_screen.py:340-343`) has zero diff and reads only `band_class`/`distance_bps`/`band_score`/`symbol`; the new keys are written before `rows.sort()` and never read by it. I confirmed on real data that the recorded order equals the pre-change key order for 100/100 rows of the new snapshot AND 100/100 of `screen-2026-07-29-2a57de4e7415`. |
| 9 | MCP exactly 17 tools; fingerprint pinned; zero new `Config` fields | Accepted with citation (mechanical, verified twice) + independent check: reviewer PASS with `issues: []`; QA row "`tests/test_mcp_server.py` — confirmed 17 tools, `desk_screen` remains byte-identical no-arg GET proxy" (38 tests, in my own green run); UT-J-06 PASS naming all 17; and my own MCP roster in this session exposes exactly 17 `mcp__tapeology__*` tools. Fingerprint printed live: `08e471b10130e1e2`. `git diff --stat` shows `config.py` absent from the diff. |
| 10 | `[NEW]`-flagged demo walkthrough over POPULATED rows | Substance met, verdict string is `RECORDED_WITH_NOTES` — see **E1**. I read `reports/demo/goal-desk-iter-23/step-04.png`: populated `levels` tallies and the `round number` badge are both legible. |

TC-15 (zero diff on out-of-scope files) confirmed by `git diff --stat`: the only source files touched
are `desk_screen.py`, `test_desk_screen.py`, `desk/page.tsx`, `lib/types.ts`. `tradability.py`,
`levels.py`, `bars.py`, `bar_index.py`, `desk_coverage.py`, `StructureChart.tsx`, `PriceChart.tsx`,
`config.py`, `app/engine/`, `app/mcp/` are all absent from the diff.

---

## 3. Findings

### Backend Findings

**B1 — IMPORTANT (gap, deliberately not "fixed"): J-15's live evidence was produced against the
ambient store, and a real 100-row screen snapshot was written into `apps/backend/.data/screen/`.**

The spec's NOTES §1 is unambiguous: "compute the new screen snapshot, capture the browser
screenshot, and record the demo-narrator walkthrough against a fixture-scoped copy of
`apps/backend/.data` (never the ambient store) — name the scoped rig explicitly in every lane's
dispatch (dev, browser-qa, demo-narrator), per the iter-9/11/14/15/17/19/20/21/22 lesson."
goal.md's J-15 acceptance opens with "on the fixture-scoped rig a NEW screen run", and DoD item 6
says "a NEW **fixture-scoped** screen snapshot". None of that happened.

Evidence:
- `apps/backend/.data/screen/screen-2026-07-30-bad6387963ef.json` exists, `created_utc
  2026-07-30T09:57:32.006925Z`, 100 ranked rows + 1 skip, pins `universe-2026-07-25-49b33fa31680` /
  `08e471b10130e1e2` / `ae2c740d1a70c9c7`. It is now the store's **latest** snapshot, i.e. `/desk`'s
  default view for the operator.
- `reports/phase-goal-desk-iter-23-ui-test-results.llm.md:50`: "Clicked 'Run Screen'
  (`desk-run-screen-button`) for 2026-07-30 ... waited ~4 minutes for the 101-member compute";
  environment lines 134-135 name `http://localhost:3301` / `http://localhost:8301` — the ambient rig.
- Root cause is upstream of the browser-qa lane: `runs/goal-desk-iter-23/goal-slice-bqa.md:239`
  describes the rig as "browser-QA rig on `:8301`/`:3301`" and the slice contains **no** "Scoped rig
  required" section at all — the spec's NOTES §1 was not carried into that lane's dispatch.

Why this is IMPORTANT and not merely an OBSERVATION: the consequence class materialized inside this
very iteration. UT-J-09's replay FAIL was caused by an earlier ambient-store mutation (a real top-up
run `topup-2026-07-29-5de907c83fc4` landing between iter-11 and iter-23), which forced a golden
repair. Writing more real records into the ambient store is the same mechanism. I was genuinely
unsure between IMPORTANT and GAP and chose the higher level, per the rubric.

**Not fixed, and deliberately so.** Deleting the snapshot would itself breach the append-only /
immutable-data rail ("never deleted") and would destroy the only browser evidence J-15 has. What I
did instead was bound the damage, and it is bounded:
- The snapshot is honest, not junk: I re-derived ORCL/AMT/MA's `member_count`/`round_number`/tally
  from a fresh `compute_tradability(bar_store, sym, as_of_epoch, Config())` and all three matched
  byte-for-byte, key order included.
- Nothing pre-existing was disturbed: `ScreenStore(".data/screen").list()` returns
  `integrity_errors == []` for all 11 files, and the 10 pre-iteration ones carry zero new keys.
- No new golden drift: I read all seven desk journey scripts that touch `/desk`
  (`J-03/J-04/J-08/J-11/J-12/J-13/J-14.json`). None asserts text that depends on the identity of the
  *latest* screen — they assert generic strings or specific still-present snapshot ids, and J-08's
  "Viewing the recorded screen for 2026-07-25 — not the latest." stays true. So the replay lane is
  not newly fragile because of this write.

**B2 — OBSERVATION: the J-09 golden was re-pinned to another ambient-store artifact.**
`runs/goal-session-desk/journey-scripts/J-09.json` step 2's expected text moved from "No top-up runs
recorded yet." to "404 of 404 pairs attempted". The repair is honest — it exercises the *populated*
branch of J-09's own acceptance line rather than weakening it, the LLM lane re-verified the whole
Top-up Runs panel live with a screenshot, and the previous note had predicted exactly this drift. It
is recorded here only because the new assertion is again pinned to one ambient run's stats and will
drift the next time an operator tops up — the script's own updated note says so.

**B3 — OBSERVATION: `band_member_timeframes` is documented as `{<tf>: int>=0}` in the blueprint**
(`runs/goal-session-desk/state/blueprint.md`, the iter-23 Data-Contract addition) while every present
key is `>= 1` by construction — a timeframe with no member is absent, never zero. The code, the spec
body, and the tests all state the stricter, correct rule; only the blueprint's type sketch is loose.

### Frontend Findings

**F1 — GAP: the new `levels` column is the ranked table's 12th column and is not reachable without
horizontal scroll at 1440px.** UT-07 is the one FAIL in the merged results
(`phase-goal-desk-iter-23-ui-test-results.md:37`): at a 1440px viewport the table's content is
1795px inside a 1214px `overflow-x: auto` container, so the `levels` header sits outside the visible
area. This is a **pre-existing** condition — `opposite` already required the same scroll when it
shipped at iter-18 — and the spec mandated exactly this placement ("one new `levels` column ...
beside the existing `band`/`opposite` columns"), so the developer built what was asked. It is
recorded as a gap because (a) the iter-18 audit closed with a written warning — "the `/desk` ranked
table has now grown a column in three consecutive iterations ... If a 12th column is ever proposed,
the right question is whether to keep appending" (`goal-desk-iter-18-audit.md:255-258`) — and this
iteration added that 12th column, and (b) the `ux-regression-reviewer` that would normally adjudicate
discoverability was shed this iteration (`phase-goal-desk-iter-23-ux-regression.md`:
`UX-REGRESSION-SKIPPED`, SPEED-15 rung 3b), so UT-07 is the only assessment on record. Fixing it
means a layout decision (column grouping, a drill-in panel, or dropping a column) — squarely out of
this iteration's scope.

**F2 — OBSERVATION: cosmetic trailing space.** `page.tsx:454`'s `{" "}` separator renders even when
`band_round_number` is false, so a non-round-number cell's text ends with a space. No test or journey
asserts an exact populated-cell string, and UT-03/UT-04 both read correctly.

I checked the two edge cases that could have made this cell lie and both are structurally impossible,
not merely untested: an empty tally with a non-zero count cannot occur because
`tradability.py:361/364` sets `member_count = len(members)` on the same dict literal and nothing
trims `members` afterwards; and JS object-key order cannot silently re-sort the tally because every
timeframe key (`1d`/`1h`/`4h`/`1w`/`1m`/`5m`) is non-integer-like, so `Object.entries` preserves the
JSON's insertion order. The badge is a genuine verbatim reuse — `page.tsx:456-461` matches
`structure/page.tsx:614-621` in `data-testid`, className, and text.

### Test Findings

**T1 — GAP: the rank-order "golden" test is half tautological and is not the pre-change baseline
comparison TC-7 asks for.** `test_row_order_is_unchanged_by_the_band_member_fields_addition`
(`apps/backend/tests/test_desk_screen.py:1660`) asserts
`symbols == [r["symbol"] for r in sorted(screen["rows"], key=_row_rank_key)]` — but `compute_screen`
already sorted `rows` with that exact key (`desk_screen.py:516`), so this assertion cannot fail no
matter what the row builder does. Only the follow-up `assert symbols == ["MSFT", "AAPL"]` carries
information, and it pins a 2-row fixture rather than "a golden capture of the same 5 pins taken
before this change" (TC-7, and goal.md's "a golden comparison proves the rank key did not move").
The underlying risk is nil and I proved it three independent ways rather than trusting the test: the
key function has zero diff, it reads only four fields none of which is new, and the two real 100-row
snapshots' recorded orders both equal the pre-change key order (100/100 each). Left as a gap because
the *test* is weaker than the contract it advertises; the *behavior* is verified.

**T2 — OBSERVATION: TC-9's legacy-row test is true by construction rather than against a real
pre-iteration file.** `test_a_legacy_row_recorded_without_band_member_fields_serves_them_absent_never_backfilled`
(`test_desk_screen.py:1707`) records a fresh fixture row that happens to lack the keys. That pins the
"never backfill on read" contract, which is worth pinning, but it cannot detect a backfill that only
fires on genuinely old files. I closed the gap live instead: all 10 pre-iteration ambient snapshots
verify their stored `file_checksum` and carry zero new keys.

The rest of the new suite is strong and tightly asserted: the golden test
(`test_desk_screen.py:1554`) pins exact dicts *and* key order
(`["1m", "5m", "1d"]`), asserts `is False`/`is True` identity for the flag, and explicitly asserts
`"1w" not in ...` for the never-fabricate-a-zero rule; the call-count guard
(`test_desk_screen.py:1727`) counts real `compute_tradability` and `BarStore.merged_bars` calls and
requires `baseline + 1`, not "≤ some bound"; and the TC-2/TC-3 additions to
`test_aapl_row_cross_checks_byte_identical_to_the_real_tradability_route` compare against the actual
`GET /research/tradability` response. No frontend component test exists — I verified the dev's
justification is accurate: `apps/frontend/package.json` has no `test` script and no jest/vitest
dependency, and the repo contains zero `*.test.*`/`*.spec.*` files, so the plan's item 11 was
correctly declined rather than met by introducing a framework mid-iteration.

### Showcase Findings

**E1 — GAP: the demo verdict is `RECORDED_WITH_NOTES`, not the DoD's literal `RECORDED`.** The
substance of TC-12 is met — five captured steps, steps 02-05 `[NEW]`-flagged and attributed to J-15,
and `reports/demo/goal-desk-iter-23/step-04.png` legibly shows populated `levels` tallies (`5
levels`, `2 levels`, `121 levels`, `134 levels`) with the `round number` badge. The three soft notes
have one shared root cause worth writing down: the demo script's click targets are ambiguous
multi-match locators — `[data-testid='desk-row-levels']` matches 100 cells and
`tradable-band-round-number` matches 16 badges on the populated screen — so `Locator.click` times
out. Step 01's soft note is a separate authoring slip: its `expect.text` is `"desk-screen-rows-table"`,
a testid used as a page-text assertion, which can never match. Showcase-class and non-blocking by
the demo-narrator's own contract, but the script will keep emitting these notes until the targets are
made specific (e.g. `.first`, or a row-scoped selector).

---

## 4. Domain Assessment

The domain logic is correct and is the minimum that could satisfy the journey.

`_band_member_timeframes` (`desk_screen.py:312-326`) is a five-line first-seen tally with no sort of
its own; its determinism claim rests on `compute_tradability` having already sorted `members` by
`(price, timeframe, type)` (`tradability.py:364`), and since key order is decided entirely by those
value tuples, ties among identical `(price, timeframe)` members cannot perturb it. The sum invariant
is not merely tested, it is structural: `member_count` and `members` are set on the same dict literal
(`tradability.py:361/364`), nothing trims `members` downstream (the only later operations are the
top-K *band* cap and two band-level sorts), and every member increments exactly one key. On the real
100-row snapshot the invariant holds 100/100 with counts spanning 1 to 4,014.

The `member_count == 1` case that the spec calls out is genuinely reachable, not synthetic:
`_cluster_side` (`tradability.py:198-204`) deliberately keeps size-1 bands ("EVERY level here joins
exactly one band, including size-1 bands"), and the real snapshot's minimum is exactly 1 — so the
golden test's zero-width single-member row exercises a state the product can actually produce.

Nothing here scores, gates, or judges. `_row_rank_key` is untouched; the tally never enters band
selection; the UI renders integers and a boolean and derives nothing. `tests/test_copy_discipline.py`
passes unmodified and it does cover the changed file — its scan globs `app/**/*.tsx` under
`apps/frontend` (`test_copy_discipline.py:221-223`), so the "green unmodified" claim is non-vacuous.
The one place the two pages could have diverged in vocabulary — the round-number badge — is a literal
copy of `/structure`'s markup, and `/structure` already renders `band.member_count` in its own column
(`structure/page.tsx:612`), so `/desk` now says the same thing in the same words about the same band.

The reviewer's `spec_alignment: complete` / `issues: []` and QA's PASS both hold up against the code
on every claim I re-checked. Their blind spot was the same one: both assessed *what the code does*
and neither asked *where the evidence was produced*, which is where B1 lives.

---

## 5. Fixes Applied During This Audit

None.

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No CRITICAL finding surfaced. The one IMPORTANT finding (**B1**) is not surgically fixable: the ambient snapshot cannot be deleted without breaching the append-only/immutable rail and destroying J-15's only browser evidence, and the fixture-scoped rig it should have used is a dispatch-time decision that cannot be retro-applied to an already-captured screenshot. It is reported as an unresolved finding with its damage bounded and re-verified above, per the "a fix without evidence is not a fix" rule. |

No source file was modified by this audit; `git diff --stat` is unchanged from the state QA reported.

---

## 6. Recommended Next Step

Proceed — J-15 is real, verified against live data, and materially closes the disclosure gap the
proposer measured. Three things to carry forward:

1. **Fix the dispatch, not the snapshot (B1).** The spec's NOTES §1 exists precisely to stop this and
   it never reached the browser-qa lane's slice. Before the next `/desk`-writing iteration, the
   scoped-rig paragraph must be injected into the browser-qa and demo-narrator dispatch slices
   verbatim (the `TAPEOLOGY_DESK_SCREEN_DIR` + copied-`.data` recipe), and the lane should be
   required to prove the serving process points at the copy with a direct `curl`. Do **not** delete
   `screen-2026-07-30-bad6387963ef` — it is a valid, pinned, honest append and removing it would
   breach the rail it was recorded under.
2. **Decide the table's future before a 13th column (F1).** The iter-18 audit's warning has now come
   true: `/desk` has twelve columns and its newest disclosure is off-screen at 1440px. The next
   proposer cycle should treat "how the briefing surfaces disclosure" as its own journey (grouping, a
   per-row detail panel, or retiring a column) rather than appending a thirteenth. Note that the
   `ux-regression-reviewer` was shed this iteration, so UT-07 is the only recorded assessment.
3. **Tighten two test artifacts when the file is next touched (T1, E1)** — replace the tautological
   half of the rank-order golden with a stored pre-change row capture, and make the demo script's
   click targets unambiguous (they are the sole cause of the three `RECORDED_WITH_NOTES` soft notes).
   Neither is worth its own iteration.

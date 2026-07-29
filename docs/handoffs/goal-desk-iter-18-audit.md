# goal-desk-iter-18 Audit Report

**Date:** 2026-07-29
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The phase goal is achieved: every ranked row of a NEWLY computed screen snapshot now carries
`opposite_band` and `bands_by_class`, both selected from the single `result["bands"]` list
`compute_screen` already holds (zero second `compute_tradability` call, zero extra `BarStore` read,
rank key untouched), served by the one already-registered endpoint, rendered on `/desk` in an
11th `opposite` column plus one composite-tooltip line — and I independently confirmed the
populated near/far pair (`0.00 bps` and `1208.73 bps`) legible together in a real browser capture on
a fixture-scoped rig. Two gaps remain unfixed and are deliberately NOT fixed here: (B1) the
disclosed band is the **highest-class-then-nearest** band on the other side, not the *nearest* one,
which contradicts `docs/goal.md`'s own J-14 step-1 wording and the "nearest wall" framing the GOAL
uses — resolving it changes a persisted field's ranking semantics against a twice-stated phase-spec
prescription, so it is a product decision, not an audit fix; and (E1) DEFINITION OF DONE item 4 (the
`[NEW]`-flagged demo-narrator walkthrough) is substantively unmet — 4 of its 6 frames show
`/structure`, and the `opposite` column appears in none of them. Neither compromises the shipped
capability, which is independently proven by browser QA and by the suite.

---

## 2. DEFINITION OF DONE — verification

| # | DoD item | Result | How verified |
|---|----------|--------|--------------|
| 1 | J-14 passes via browser-qa-agent | **MET** | Full trace. I opened `reports/qa/goal-desk-iter-18-evidence/UT-03-result.png` myself: the `opposite` column renders populated cells including `opposite support unclassified 22.08–22.13 · 0.00 bps` (near) and `opposite support C 260.24–267.99 · 1208.73 bps` (far, >1,000 bps) legible in ONE screenshot. Its provenance panel reads `screen-2026-06-22-5c2109f7078a` / `universe-2026-07-25-017cc1848db3` — both absent from the ambient store (`.data/universe/` holds only `universe-2026-07-25-49b33fa31680`), independently corroborating the scoped-rig claim rather than resting on the report's prose. `runs/goal-session-desk/journey-scripts/J-14.json` exists (see G1). |
| 2 | J-01…J-13 remain green | **MET** (cited, mechanical) | `reports/phase-goal-desk-iter-18-regression-replay-results.md` 12/12 deterministic replays PASS + UT-J-06 (MCP) in `…-ui-test-results.md` = 23/23; reviewer `spec_alignment: complete, issues: []`. Independently: I ran the full backend suite myself — **1448 passed, 8 skipped** — and `len(app.mcp.TOOL_NAMES)` = 17. |
| 3 | No anti-goal violation | **MET** | Full trace (risk class: persistence). `grep -c opposite_band apps/backend/.data/screen/*.json` → 0 matches in all six recorded snapshots; newest mtime in `.data/screen/` is `2026-07-29 03:07:39`, i.e. **before** this iteration started (`09:12:41` per `status.json`) — nothing backfilled, rewritten, or written for evidence. Single owner: `opposite_band`/`bands_by_class` appear in exactly three files repo-wide — `app/research/desk_screen.py` (compute), `lib/types.ts` (type), `app/desk/page.tsx` (render); no second computation site. `_row_rank_key` (`desk_screen.py:292-295`) appears in `git diff` only as unchanged context. `test_copy_discipline.py` is byte-unmodified (`git diff --stat` empty) and green. |
| 4 | `[NEW]` demo-narrator walkthrough, `Demo Verdict: RECORDED`, populated rows, fixture rig | **NOT MET** | Full trace — see **E1**. |
| 5 | Suite green / fingerprint / zero Config fields / zero restricted-file diff / 17 tools / copy lint | **MET** | Verified by me directly: `Config().config_fingerprint()` → `08e471b10130e1e2`; `git diff --stat` on `tradability.py`, `levels.py`, `bars.py`, `bar_index.py`, `StructureChart.tsx`, `desk_coverage.py`, `config.py` → empty; `len(TOOL_NAMES)` = 17; full suite 1448 passed / 8 skipped. |
| 6 | Dev handoff written | **MET** | `docs/handoffs/goal-desk-iter-18-dev.md` present, and unusually honest about its own two gaps. |

---

## 3. Findings

### Backend Findings

**B1 — IMPORTANT (gap, not fixed): `opposite_band` is the highest-class band on the other side, not
the nearest one — contradicting `goal.md`'s own J-14 step 1 and the "nearest wall" framing.**

`desk_screen.py:269-278` (`_select_opposite_band`) filters to the other side and then delegates to
`_select_best_band`, whose key at `desk_screen.py:264` is
`(-_CLASS_RANK[class], distance_bps, -quality_score)` — **class rank first, distance second**. The
dev's own test pins this deliberately: `tests/test_desk_screen.py:259`
(`test_select_opposite_band_prefers_higher_class_over_closer_distance`) asserts a class-A band at
90.0–91.0 is selected over a class-C band at 99.9–99.95 with `close=100.0` — i.e. a wall ~900 bps
away is disclosed as the row's "opposite" while a wall ~5 bps away sits on that same side, unnamed.

The artifacts disagree about which key was intended:

- `docs/phases/goal-desk-iter-18.md:88` — "ranked by the identical `(class rank DESCENDING,
  distance_bps ascending, quality_score descending)` key" ⇒ what was built.
- `docs/goal.md:965` (J-14 step 1) — "distance ascending, then class rank descending" ⇒ the
  opposite ordering, which would make the field genuinely *nearest*-first.

Failure scenario, in the exact rows J-14 was written for: `goal.md`'s measured rationale names
ISRG #63 and CMCSA #62 as the inversions where "an unclassified support band sits 0.0 bps from its
close", and records that 42 of 63 rows hold ten class-A bands — so ~21 of 63 rows have mixed classes
across the two sides. On any such row where the opposite side holds both a graded band far out and
an ungraded/lower-graded band close in, the new column discloses the far one and stays silent about
the near one — reproducing, on the opposite side, precisely the blindness the journey was built to
remove.

Not fixed, deliberately. Changing the key would (a) contradict a prescription the phase spec states
twice (IN SCOPE and Data-contract additions) and that `plan.md` restates, (b) invalidate a pinned
test, and (c) alter the semantics of a field that is now persisted forever into append-only
snapshots. That is a product decision for the decomposer/proposer, not a surgical audit fix.

Harm is bounded and worth stating: **no shipped user-facing string claims "nearest."** The header is
`opposite` (`page.tsx:457`); the cell reads `opposite <side> <class> <low>–<high> · <n> bps`
(`page.tsx:418-424`) — it discloses exactly what it selected and nothing more. Both the module
docstring and `_select_opposite_band`'s own docstring state the full tie-break key inline, so a
careful reader is not misled. The word "nearest" is confined to spec/goal prose. Recommendation:
reconcile `goal.md:965` against the shipped key before the next iteration — either amend the goal
text to say class-first, or open a follow-up journey to add the geometrically nearest band as its
own distinct field.

*(I was genuinely unsure between IMPORTANT and GAP here — the implementation matches its spec
exactly, so nothing is "broken." I chose the higher level per the rubric because the mismatch is
against the product contract that scores the journey, and because it is now baked into persisted
data.)*

**B2 — OBSERVATION: `_select_best_band` still raises on an empty `bands` list.** If
`compute_tradability` returns `basis_as_of` non-null with zero bands, `desk_screen.py:426` raises
`ValueError: min() arg is an empty sequence`. Pre-existing since iter-3 and unchanged here;
`_select_opposite_band` correctly guards its own empty case (`desk_screen.py:276-277`). Noted only
so it is not mistaken for something this iteration introduced.

### Frontend Findings

**F1 — OBSERVATION: the three render states are correctly and distinguishably handled.** I traced
`page.tsx:416-424` directly: `=== undefined` → `"opposite wall not recorded in this snapshot"`;
`=== null` → `"no band on the other side"`; otherwise the populated cell with
`band_class ?? "unclassified"`. This is the honest three-way split the spec asked for, and it is the
correct check — `types.ts:841-850` types both fields optional, and a JSON-absent key deserialises to
`undefined`, never `null`. `DeskRow` is used only by `DeskRowsTable`, and header (11 `<th>`) and body
(11 `<td>`) counts match; the skip table is untouched at 4 columns. No per-cell `title` was added
under the stretched drill-in anchor (the iter-6/7 F2 lesson honored — browser QA UT-04 confirms the
`desk-row-opposite` cell's own `title` is `null`).

**F2 — OBSERVATION: the client-side arithmetic guard is literal-form only.**
`test_desk_ui_guards.py`'s `_PRICE_ARITHMETIC_PATTERN` matches `row.<field>` adjacent to an
arithmetic operator. A destructured or aliased value (`const {A} = row.bands_by_class; A + B`)
escapes it. Pre-existing shape since iter-17, correctly *extended* rather than duplicated this
iteration, and carrying a real counter-test that I confirmed fails on seeded violations of each new
field family. Not worth widening now.

### Test Findings

**T1 — IMPORTANT (fixed): TC-2/TC-4 were proven only against monkeypatched bands, never against the
real `GET /research/tradability` response the spec names.** The golden
(`test_desk_screen.py:1264`, `test_opposite_band_golden_near_far_and_null_class_rows`) injects a
controlled `compute_tradability`, so it proves the row copies *the bands it was handed* — it cannot
prove the row copies *what the canonical route serves*, which is exactly what TC-2 ("compared to the
corresponding band in `GET /research/tradability…`'s own `bands` list") and TC-4 ("summed … equals
the length of that symbol's `bands` list") require. The natural home for that assertion already
existed and was not extended:
`test_aapl_row_cross_checks_byte_identical_to_the_real_tradability_route`
(`test_desk_screen.py:545`) already drives the real route through `TestClient` and already asserts
byte-identity for `basis_as_of`/`class`/`quality_score`/`distance_bps` of the *selected* band.

**Fix applied** (`apps/backend/tests/test_desk_screen.py`, +39 lines inside that existing test, no
new test, no product-code change): recount the real route's own `bands` by class and assert
`row["bands_by_class"] == served_counts` and `sum(...) == len(body["bands"])` (TC-4); locate the
disclosed `opposite_band` in the route's own served bands, assert it is uniquely identifiable, on a
side `!= row["side"]`, and byte-identical on `side`/`class`/`quality_score` (TC-2); assert its
`distance_bps` reproduces the same near-edge formula against the row's own `reference_close` (TC-3);
and, in the `None` branch, assert the route served no band on the other side at all (TC-8 on real
data).

Verification of the fix, as required:
1. `pytest tests/test_desk_screen.py -k aapl_row_cross_checks` → **1 passed**.
2. Non-vacuity proven by a seeded counter-check: I temporarily inverted `_select_opposite_band`'s
   filter to `== best_side` and re-ran — the test **failed** with
   `AssertionError: the disclosed opposite band must be a real, uniquely-identifiable served band on
   the side the row's own band is NOT on / assert 0 == 1`. This also proves AAPL's `opposite_band`
   is non-null on the fixture, so the interesting branch is genuinely exercised. The seeded defect
   was then reverted; `git diff --stat` on `desk_screen.py` is back to the developer's exact 61
   insertions, and `grep` for `SEEDED`/`== best_side` in the diff returns nothing.
3. Regression check: targeted files **148 passed**; full backend suite **1448 passed, 8 skipped** —
   identical to the pre-audit baseline.
4. No dev-handoff claim was invalidated by this fix (it strengthens a test the handoff did not
   claim).

**T2 — GAP: TC-5's rank-order golden is partly self-referential.**
`test_row_order_is_unchanged_by_the_opposite_band_addition` (`test_desk_screen.py:1348`) asserts
`symbols == [r["symbol"] for r in sorted(screen["rows"], key=_row_rank_key)]` — which is tautological
(the function sorts by that key). The real protection is the second line,
`assert symbols == ["MSFT", "AAPL"]`, a hard pin — but only two symbols wide. Combined with
`_row_rank_key` appearing solely as unchanged context in `git diff` (I confirmed this), the spec's
intent is met in substance. Not fixed: broadening the golden is new test scope, not a defect.

### Evidence / Showcase Findings

**E1 — IMPORTANT (gap, not fixed): DEFINITION OF DONE item 4 — the `[NEW]`-flagged demo-narrator
walkthrough — is substantively unmet.** The DoD requires "`Demo Verdict: RECORDED` + a non-empty
gallery … narrated over POPULATED ranked rows on a fixture-scoped rig with a freshly computed
screen." What was produced:

- `reports/phase-goal-desk-iter-18-demo-results.md:3` reads **`RECORDED_WITH_NOTES`**, not
  `RECORDED`, with four soft-note click timeouts (steps 3-6); step 06 has no frame at all.
- I opened every frame myself. `step-03.png`, `step-04.png` and `step-05.png` are **byte-identical**
  (`md5 7cab9fb7…`) and show the **`/structure` page** — an IBM symbol-autocomplete dropdown over a
  candlestick chart — not `/desk`. `step-01.png` and `step-07.png` are also byte-identical
  (`9ab3c454…`) and show `/desk` cropped at the `band` column, with `opposite` off-screen.
- Net: the `opposite` column appears in **zero** of the six frames; no populated row, no near/far
  pair, no `bands_by_class` tooltip line. The run targeted the ambient `http://localhost:3301`
  against the legacy `.data` store, not a fixture-scoped rig, so step 05's narration is literally
  "Every ranked row on this page was recorded before this feature existed."
- Consequence for the carried item: because the frames never show a populated row, iter-17's carried
  `evidence_makeup` gap for **J-13 remains open** — the ambient snapshot
  `screen-2026-07-28-ac07c9581a4f` has no `reference_close` key on its rows (I checked the JSON), so
  its `band` cells read "close not recorded in this snapshot" in `step-01.png`. The spec anticipated
  this outcome as a carry, not a new goal.

The `ux-regression-reviewer` reached the same conclusion independently
(`reports/phase-goal-desk-iter-18-ux-regression.md`, "Demo-narrator artifact does not actually
narrate the capability"). Not fixed here: re-recording requires standing up a fixture-scoped rig plus
an isolated frontend and re-running the demo lane — a lane re-dispatch, not a source-file fix. This
does not change the product verdict, because the capability itself is proven by browser QA
UT-01…UT-10 on a real, origin-checked page; but downstream lanes must **not** treat
`reports/demo/goal-desk-iter-18/` as evidence that an operator can see the disclosure, and the
goal-evaluator should score DoD item 4 on this evidence, not on the demo report's verdict string.

**G1 — GAP: J-14's permanent replay anchor pins only the legacy-absence string.**
`runs/goal-session-desk/journey-scripts/J-14.json` step 3 asserts
`"opposite wall not recorded in this snapshot"` against the pinned legacy snapshot
`screen-2026-06-22-3ecd45c062c7`. The script's own notes state the reason honestly (the scoped rig
holding populated rows was a torn-down temp copy, so it is not reachable at replay time) and cite the
J-13 precedent. The consequence is real and should be recorded: a future regression that breaks the
**populated** cell render would replay green forever. Not fixed — a durable populated fixture
snapshot is new scope.

---

## 4. Domain Assessment

The domain logic is correct and, unusually, minimal. Both values are derived inside the single
`compute_tradability` call the row already makes: `_select_opposite_band` is a filter plus a
delegation to the existing selector, and `_bands_by_class` is a four-key counter with no grade,
threshold or weight — so the "no new statistics or gates" anti-goal holds literally, not just in
spirit. `_distance_bps(opposite, close)` reuses the same near-edge rule (`price_low` for resistance,
`price_high` for support) against the same `close` the row records as `reference_close`, so the two
distances on a row are commensurable by construction rather than by convention. The call-count guard
(TC-10) is a real guard, not a formality: it establishes a per-symbol baseline by invoking
`compute_tradability` once directly, then asserts the full screen walk adds exactly one `merged_bars`
call — so a future refactor that re-reads the store to recover the opposite side fails loudly.

The append-only rail is respected in the strongest available sense: legacy rows omit both keys
entirely rather than carrying `null`, and the frontend's `undefined`/`null`/populated three-way split
preserves that distinction all the way to the screen — "not recorded in this snapshot" and "no band
on the other side" are different sentences because they are different facts. That is the honesty
property this era keeps re-earning, and it was not diluted here.

The one substantive domain question is B1: whether "the opposite band" should mean *the best band by
the row's own ranking, on the other side* (what shipped) or *the nearest band on the other side*
(what `goal.md` step 1 describes and what the journey's own measured rationale used). Both are
defensible; only one is documented consistently, and it is not the one in `goal.md`.

---

## 5. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/tests/test_desk_screen.py` | Extended `test_aapl_row_cross_checks_byte_identical_to_the_real_tradability_route` (+39 lines) to assert TC-2/TC-3/TC-4/TC-8 for `opposite_band`/`bands_by_class` against the **real** `GET /research/tradability` response — uniquely-identifiable served band, correct opposite side, byte-identical `class`/`quality_score`, `distance_bps` reproduced from `reference_close`, per-class recount equal to the served `bands`, and an honest-`null` branch. Proven non-vacuous by a seeded wrong-side defect (test failed, then reverted). Zero product-code change. |

No other file was modified by this audit. `git diff --stat` on `desk_screen.py` / `page.tsx` /
`types.ts` is identical to the developer's tree (61 / 42 / 20 insertions).

---

## 6. Recommended Next Step

**Proceed** — the product code ships as-is. Two items to carry, neither a source-code fix:

1. **Re-record or root-cause the J-14 demo walkthrough (E1).** The demo script's step-02/03/04/05
   click targets silently navigated to `/structure`; a scoped rig with populated data of exactly the
   right shape already exists in this iteration's own browser-QA evidence, so a re-record against
   that style of rig closes both E1 and (likely) J-13's carried `evidence_makeup` gap in one pass.
   Until then, `reports/demo/goal-desk-iter-18/` is not evidence of anything about J-14.
2. **Reconcile the opposite-band selection rule (B1)** before another iteration builds on the field:
   either amend `docs/goal.md:965` to state the shipped class-first key, or open a follow-up journey
   disclosing the geometrically nearest opposite band as a distinct value. Do not change
   `_select_opposite_band` silently — the field is already persisted into append-only snapshots.

Also worth carrying forward (non-blocking): the `/desk` ranked table has now grown a column in three
consecutive iterations (J-11 `history`, J-13 `band`, J-14 `opposite`) and an increasing share of the
disclosure surface sits past a horizontal scroll — the `ux-regression-reviewer` flagged the same
trend. If a 12th column is ever proposed, the right question is whether to keep appending.

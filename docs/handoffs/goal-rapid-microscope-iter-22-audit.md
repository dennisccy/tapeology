# goal-rapid-microscope-iter-22 Audit Report

**Date:** 2026-08-21
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

All ten DEFINITION OF DONE items are genuinely met, and I re-derived the load-bearing ones
first-hand rather than trusting any handoff: the scoped QA rig's on-disk ledger holds all three
pilot families each carrying a screen row **plus** a `walkforward_floor_check` row under the same
`candidate_id`, the six default-grid rows carry none, my own full backend suite run reports
3,322 passed / 8 skipped / 0 failed, and the fingerprint is `08e471b10130e1e2` with zero
`referee_*`/`config.py` diff. The implementation is a genuine generalization of iter-21's Study-2
wiring — one shared `_PILOT_GRID_SELECTORS` table read by both the manager and the CLI — not a
third parallel path, and the studies are reachable from the CLI and the route, not only from
pytest.

One IMPORTANT problem was found and repaired, and it is **not** in the product: the QA report cited
two **blank** screenshots and one copied screenshot as evidence for on-screen claims (finding T1).
The claims themselves are true — I verified them from evidence the QA report did not cite — but the
citation breached `.claude/judgment-rubrics.md` §5's quality floor and would have carried a
falsifiable claim into the evaluator's baseline. Three GAPs remain documented and unfixed.

---

## 2. Findings

### Backend Findings

**B1 — GAP (documented): `micro_routes.py` keeps a second, hand-maintained copy of the
selector→structure-kind classification**

`apps/backend/app/research/micro_routes.py:284-287` defines
`_BAND_TOUCH_PILOT_SELECTORS = frozenset({GRID_SELECTOR_RANGE_WALL_PILOT,
GRID_SELECTOR_DELTA_DIVERGENCE_PILOT})` and `_PLAYBOOK_SIGNAL_PILOT_SELECTORS =
frozenset({GRID_SELECTOR_CAPITULATION_PILOT})` by hand, restating the `(study_id, structure_kind)`
mapping `scout._PILOT_GRID_SELECTORS` (`scout.py:1686-1691`) already owns. Today the two agree — I
diffed them by value. The reviewer filed this as MINOR against the phase's own
*single source of truth* rail; I traced the failure mode before deciding severity, and it is a
**loud** one, not a silent one: a future selector present in `scout._PILOT_GRID_SELECTORS` but
missing from both route frozensets yields `resolver=None, playbook_store=None`, which
`ScoutComputeManager.trigger` (`scout.py:1947-1966`) rejects with an explicit `ValueError` →
HTTP 500. No wrong answer can be served, no row can be mis-ledgered. That keeps it below the
IMPORTANT bar (no specified behaviour fails today, no realistic scenario produces a wrong result),
so it stays a documented GAP rather than an audit fix — the reviewer's suggested one-liner
(derive both sets by filtering `scout._PILOT_GRID_SELECTORS` on kind) remains the right cleanup for
whichever iteration next touches this route.

**B2 — GAP (documented, inherited): every recorded pilot-study answer comes from a fixture-scoped
corpus with zero (or one) usable anchors**

The three families now on the record all read `killed_insufficient_n`. On the operator-reachable
rig the range-wall and capitulation screens report
`usable_sessions=0 (need >= 2), n_candidate=0, n_comparator=0` (visible in
`UT-07-result.png`; ledger at
`/home/dennis-chan/.cache/iad/iad.goal-rapid-m-39d2f63f.2777839/tapeology-store-scope-qa/rig/micro_scout/ledger.jsonl`),
and the CLI evidence (`UT-10-ledger.jsonl`) is the same shape. `docs/goal.md` J-09 step 2 asks for
each study to be run "on the full joinable corpus"; that run remains blocked by the iter-21
auditor's B2/B3 performance findings, which this phase spec explicitly excludes ("Real production
Scout/fold runs against the live `.data/` store — still forbidden"). So the honest state of J-09
is: three predeclared families, three recorded closed-vocabulary decisions, all of them
`insufficient_n` produced from empty or one-row anchor sets — which J-09's own acceptance clause
allows (`insufficient_n` is a named acceptable end state) but which is not yet a *measured* answer
to any of the three questions. This is a real limitation the spec did not require solving; it is
recorded here so no later iteration mistakes "three decisions on the record" for "three questions
answered against the corpus."

**B3 — OBSERVATION: the machinery itself is proven non-vacuous, so B2 is a data limit, not a
shallow implementation**

I checked this specifically, because "reachable but hollow" is exactly the trap iter-21's audit
named. It is not hollow. `test_iter22_study1_range_wall_screens_with_real_band_touch_anchors`
(`tests/test_scout.py:1613`, assertion at `:1664`) asserts `screen_result["n_candidate"] + screen_result["n_comparator"]
> 0` against real joined band touches, and I independently drove Study 3's frozen request through
`register_screen_and_walkforward_check` with the committed capitulation fixture: it returned
`n_comparator=1, n_sessions_total=1, evidence_class='historical_exposed_diagnostic'` with the full
concentration/ToD/fallback-tercile/best-of-N disclosure block populated, then the honest
`killed_insufficient_n`. The anchor-extraction path is genuinely exercised end to end for both new
studies.

**B4 — OBSERVATION: the new unconditional `playbook_store` route dependency costs nothing**

`trigger_scout_compute` now takes `playbook_store: PlaybookStore = Depends(get_playbook_store)`
unconditionally (`micro_routes.py:297`). I verified this cannot add I/O to the default-grid path:
`PlaybookStore.__init__` (`desk_playbook.py:827-828`) only stores a `Path` — no stat, no mkdir —
and the object is threaded into `manager.trigger` only for the capitulation selector. The CLI's own
construction (`scout.py:2145-2147`) mirrors `desk_routes.get_playbook_store:991` verbatim
(`resolve_desk_playbook_dir(config.desk_universe_dir_resolved())`), so there is no second directory
resolution rule.

### Frontend Findings

**F1 — OBSERVATION: zero frontend diff, and the generic table genuinely absorbed the two new
families**

`git status` shows no `apps/frontend/**` change. I opened `UT-07-result.png` (1668×3918, real
capture) and read the rendered Scout Ledger directly: `failed_aggression_score__band_touch__
trades_20` (root `f3dce7afd1a0083c`, "1 variants tried") with a `threshold (band_touch)` screen row
and a `— / —` floor-check row; `failed_aggression_score__playbook_signal__trades_20` (root
`4665e05f81169f93`) with the same two-row shape; `divergence_at_level_bearish__band_touch__
trades_20` with its floor-check row **registered `2026-08-20 18:47 ET`** — i.e. this iteration, not
a reused iter-21 asset (DoD item 5 satisfied). The floor-check row's `structure_context` is `null`
and renders as `— / —` without breaking the generic table, and `distinct_variant_count` still
reports 1 variant per pilot family, so the union-N denominator is not inflated by the second stage
row (*the denominator never shrinks* rail intact).

### Test Findings

**T1 — IMPORTANT (fixed): the QA report cited blank and copied screenshots as on-screen evidence**

`reports/qa/goal-rapid-microscope-iter-22-qa.md:79` cites
`goal-rapid-microscope-iter-22-evidence/TC-08-scout-ledger.png` as evidence that six families render
with full data, and line 87 cites `TC-09-walkforward.png` as evidence the Walk-Forward section reads
"No walk-forward runs recorded yet". The two files are **the same file** (md5
`d35653b036e05c65b778d34e7a802331`, 1683×1260) and are **entirely blank** — I opened it: a flat dark
background, zero page content, no text of any kind. A third citation (line 101,
`TC-09-graduation-endpoint.png`) is a byte-for-byte copy of the browser-qa lane's
`UT-08-result.png` (md5 `5cc50f177ae23e601e21d7e6fb16171f`), not an independent capture. The same
section also mislabels the capitulation family as a "Study 1 playbook variant" (it is Study 3,
`scout.py:1661-1672`) and attributes the required-still-passing journeys to "backend test suite"
verification when they were verified by the deterministic golden-replay lane.

This breaches `.claude/judgment-rubrics.md` §5 ("UI journey passes" requires a *screenshot showing
the acceptance state") and §6 ("if the screenshot contradicts the claim, the screenshot wins") —
those three rows should have read `unknown`, not PASS-with-evidence. It is IMPORTANT rather than a
GAP because the goal-evaluator and every later iteration consume this artifact as evidence, so a
falsifiable citation left standing poisons the baseline.

**Fix applied:** appended a clearly-attributed "Auditor Correction" section to
`reports/qa/goal-rapid-microscope-iter-22-qa.md` (original text left intact) naming the three bad
citations with their md5s, correcting the two factual errors, and pointing at the evidence that
does hold. **Verification of the fix:** this is a documentation correction, not a code change — no
test covers it, so the verification is the artifact itself: I re-read the appended section and
confirmed every md5, file dimension and line reference in it against `md5sum`, the PNG headers, and
`scout.py`. `git status` confirms no source file was touched by this repair.

**T2 — GAP (documented): the product claim T1 mis-evidenced is nevertheless independently true**

I re-established every claim the blank screenshots were supposed to carry, from evidence the QA
report did not cite:

- The scoped rig's ledger (path in B2 above) holds exactly 12 rows:
  `failed_aggression_score__band_touch__trades_20` screen + `walkforward_floor_check`
  (`2026-08-20T22:44:01Z`), `failed_aggression_score__playbook_signal__trades_20` screen
  (`structure_context = {"kind": "playbook_signal", "setup_id": "capitulation"}`) +
  `walkforward_floor_check` (`22:44:42Z`), six default-grid rows with `stage=None` throughout, and
  `divergence_at_level_bearish__band_touch__trades_20` screen + `walkforward_floor_check`
  (`22:47:26Z`). That is DoD items 1, 2, 3 and 5 proven on the operator-reachable HTTP path.
- `UT-10-ledger.jsonl` holds the CLI's own two rows (same `candidate_id`
  `cand-e0c665be29c930a3`, `structure_context.kind == "band_touch"`,
  `walkforward_floor_check.status == "insufficient_n"`), proving DoD item 1's "not only a pytest
  fixture" clause.
- `UT-08-result.png` is a real, full-body graduation capture (`family_root_id`,
  `state: "exploratory"`, `sealed_evaluations[0].verdict: "pass"`, `n: 30`,
  `chain_verification.ok: true`), taken this iteration — DoD item 6.

**T3 — GAP (documented): Study 3's new unit test has no non-vacuity assertion, unlike Study 1's**

`test_iter22_study3_capitulation_screens_with_real_playbook_signal_anchor`
(`tests/test_scout.py:1676`) asserts the decision is in `CLOSED_DECISIONS` and that the floor-check
row exists, but — unlike its Study-1 sibling at `tests/test_scout.py:1664` — never asserts that any
anchor was actually joined. It would pass unchanged if `_plant_capitulation_signal` silently
stopped producing a joinable signal, so it cannot by itself distinguish a genuine screen from a
hollow zero-anchor pass-through. I closed the gap by hand for this audit (B3: the screen really does
see the planted signal, `n_comparator=1`), so nothing is currently wrong; the asymmetry is a test
tightness limitation, not a failure of specified behaviour (the spec's TESTING REQUIREMENTS only
demand `register_screen_and_walkforward_check` be "exercised for both new studies"). Adding the
one-line `n_candidate + n_comparator > 0` assertion would be the cheapest hardening next iteration.

**T4 — OBSERVATION: the QA agent's own test log is truncated at 88%, so the suite claim was
dev-attested only — I re-ran it**

`reports/qa/goal-rapid-microscope-iter-22-test.log` ends mid-run inside `tests/test_tick_recorder.py`
at `[ 88%]` and never reaches a summary line; the QA report's numbers are explicitly labelled
"(per dev handoff)". Because DoD item 8 is a hard numeric gate, I did not accept a prose claim: I
ran the full suite myself and got **3,322 passed, 8 skipped, 0 failed, 0 errors in 651.89s**
(JUnit: `tests="3330" errors="0" failures="0" skipped="8"`), matching the dev's own artifact at
`/home/dennis-chan/.cache/iad/iad.goal-rapid-m-39d2f63f.2777839/full-suite-iter22.xml` and clearing
the 3,316 baseline. I also confirmed the dev's run post-dates the final tree (sources last modified
22:47/22:54 BST, run started 22:58 BST), so that artifact was not stale.

**T5 — OBSERVATION: the rig-mutation sequencing rule the spec called out was actually honoured**

The spec's NOTES warned that TC-8's POSTs invalidate `J-08.json` step 3 / `J-10.json` step 12's
"No candidates ledgered." assertion for any later lane. Timestamps confirm correct ordering: the
golden-replay lane wrote `J-01-verify.png` … `J-10-verify.png` at 22:41:33Z–22:42:06Z, and the first
rig-mutating POST landed at 22:44:01Z. The browser-qa lane independently recorded the same
sequencing and verified `GET /scout` returned zero families before its first POST. I opened
`J-10-verify.png` — a real, non-corrupt `/desk` render — satisfying TC-11's "opened, non-corrupt
screenshot" clause.

**T6 — OBSERVATION: the demo lane's three soft notes are a text-matching artifact, not a
regression**

`reports/phase-goal-rapid-microscope-iter-22-demo-results.md` records that steps 03/04 did not find
`"failed_aggression_score / threshold (band_touch)"`/`"(playbook_signal)"`. I opened
`reports/demo/goal-rapid-microscope-iter-22/step-03.png`: Study 1's family, both its rows, the
decision and the full walk-forward-refusal note are all plainly on screen. The UI splits the feature
name and the `(band_touch)` qualifier across separate elements, so the literal expected string with
its space never matches — the same class of headless-matcher brittleness this session's own record
already logs. Showcase lane, non-blocking, no action.

---

## 3. Domain Assessment

The core domain move this iteration is small and correct: generalize "one pilot selector" into
"any of three, selector-aware", without duplicating the screening path. I read the whole
`ScoutComputeManager.trigger` and CLI `main()` diff rather than the handoff's description of it,
and the generalization is faithful:

- **Byte-identity of the default path is preserved, not merely claimed.** The old
  `floor_check_registry = exposure_registry if grid_selector == DELTA else None` became
  `... if grid_selector is not None else None` (`scout.py:1989`). That is only equivalent because
  the unknown-selector `ValueError` fires first (`scout.py:1947`), so `grid_selector is not None`
  implies "a known pilot selector". I checked that ordering explicitly; it holds. The `None` path —
  every pre-J-09 caller and the shipped "Run Screen" button — reaches `default_fixture_grid` with
  `floor_check_registry=None` exactly as before, and the rig's six stage-less default rows are the
  behavioural proof.
- **The requirement rules are the right ones and are enforced server-side.** `resolver` is required
  for `band_touch`-kind selectors, `playbook_store` for the `playbook_signal`-kind one, and
  `exposure_registry` for *all* pilot selectors — that last one is what stops a caller from
  silently getting a screen-only run and losing the floor-check row, which was exactly iter-21's B1
  regression. Enforcement lives in `trigger`, not in the route, so a crafted request cannot bypass
  it.
- **The frozen requests were not touched.** The `scout.py` diff modifies only the comment block
  above `pilot_study_candidate_grid`; the function body is unchanged, so Study 1's
  `feature_name="failed_aggression_score"` / `params={"op": "ge", "value": 0.5}` remain
  byte-identical to iter-21 (TC-6), and no co-occurrence field was invented. The *no fitted
  threshold* rail is intact: nothing in this diff chooses or revises a threshold, grid, or fold
  parameter, and no value here was derived from an outcome read.
- **Evidence classes stay unmixed.** Screens emit `historical_exposed_diagnostic`; the floor check
  only *decides eligibility* from the exposure registry's `historical_oos` count and refuses — the
  source-level guard test that `evaluate_mode_b_fold` is never reachable from
  `register_screen_and_walkforward_check` still passes. Nothing pooled the two classes.

The disclosed T-1 deferral (Study 1 screens single-feature, without the `refill_consistent`
co-occurrence goal.md's prose describes) is handled the way this project's own rules require:
frozen in a source comment, restated in the dev handoff's Known Issues, pinned by a test, and not
improvised into existence. The dev's deviation from the plan's suggested fixture
(`divergence_fixture` → `pg_snapshot_store`) is likewise disclosed with a technically correct
reason — `epoch_anchor=0.0` cannot satisfy `join_band_touch`'s covering-snapshot search against a
2026 dataset window — and touches no production code.

Where the domain is genuinely thin is B2: the product can now *ask* all three questions through an
operator path, but every answer on the record is "not enough data", because the only corpora it has
been asked against are fixtures. That is honest and spec-compliant, and it is the next iteration's
real work.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `reports/qa/goal-rapid-microscope-iter-22-qa.md` | Appended an attributed "Auditor Correction" section retracting three evidence citations that do not show what they are cited for (two blank screenshots sharing one md5; one screenshot copied from the browser-qa lane), correcting the Study-3-as-"Study 1 variant" mislabel and the "verified in backend test suite" attribution for the replay-verified journeys, and pointing at the evidence that does hold. Original text left intact. |

No source-code fix was required: no CRITICAL or IMPORTANT defect was found in
`scout.py`, `micro_routes.py`, or `test_scout.py`. `git status` after this audit shows the same
three modified backend files the dev left, plus the QA-report append — no auditor code diff.

---

## 5. Recommended Next Step

**Proceed.** J-09's remaining spec'd work for this round is done and independently evidenced: three
predeclared study families, three recorded closed-vocabulary decisions each with a walk-forward
floor-check row, all reachable from the CLI and `POST /scout/compute`, rendering in the
already-shipped `/desk` sections with zero frontend diff, on a frozen fingerprint with no
`referee_*`/`Config` change and a suite I re-ran myself at 3,322/0-fail.

For the next iteration, in priority order:

1. **Make one pilot study answerable against real data.** B2 is now the whole of J-09's remaining
   substance — every recorded answer is `insufficient_n` from an empty anchor set. That means
   confronting the deferred iter-21 B2 (22.3s readiness latency) / B3 (quadratic divergence anchor
   extraction) costs, at least far enough that the range-wall selector (which never touches the
   quadratic divergence path, so it is the cheapest of the three) can complete against the
   operator's corpus.
2. **Collapse the duplicated selector classification** (B1) — a two-line derivation from
   `scout._PILOT_GRID_SELECTORS`, best done by whichever change next opens `micro_routes.py`.
3. **Tighten Study 3's unit test** with the one-line non-vacuity assertion its Study-1 sibling
   already carries (T3).
4. **Treat T1 as a process signal, not a one-off.** A QA lane that cites screenshots it did not
   open is a repeatable failure mode; the browser-qa lane's own report for this same iteration was
   exemplary by contrast (it disclosed precisely why J-07 and J-09 have no golden-replay scripts
   and proved its sequencing), which is the standard the QA lane should be held to.

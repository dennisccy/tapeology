# goal-desk-iter-9 Audit Report

**Date:** 2026-07-27
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-08's phase goal is genuinely achieved: every ranked row of a newly computed screen carries
`basis_as_of` (copied verbatim from `compute_tradability`'s own return value) and `basis_age_days`
(an exact calendar-date difference), `/desk` renders both descriptively with an honest
"basis not recorded in this snapshot" fallback, and every snapshot recorded before this iteration is
provably untouched and served with the fields ABSENT — never backfilled. I re-verified the load-
bearing claims against real data rather than trusting the handoffs: the single-source-of-truth
criterion holds byte-for-byte across five real symbols on the live route, the two legacy snapshot
files are unchanged by SHA-256 *and* by mtime, and the full suite is 1346 passed / 8 skipped / 0
failed with the fingerprint pin intact.

One literal acceptance clause is unmet: `goal.md`'s J-08 requires a screenshot with a row at
**basis age ≤ 2 d** alongside one at **≥ 10 d**. The captured evidence shows 3 d vs 14 d. That is a
consequence of the bar store's newest daily bars being dated 2026-07-23/24 (last operator fetch
2026-07-25) against an `as_of` of 2026-07-27 — not an implementation defect — but it is a real,
documented shortfall, so the verdict is PASS_WITH_GAPS rather than PASS.

---

## 2. Findings

No CRITICAL or IMPORTANT findings. No fixes were applied (see §4).

### Backend Findings

**B1 — OBSERVATION (observation): `_basis_age_days`'s docstring overstates its timezone guarantee**
`apps/backend/app/research/desk_screen.py:273-274`. The docstring claims both sides are "reduced to
a UTC calendar date first", but `datetime.fromisoformat(s.replace("Z", "+00:00")).date()` yields the
date in whatever offset the string itself carries — it does not convert to UTC. Unreachable in
practice: `basis_as_of` is always produced by `tradability.py`'s `_iso()` (`...Z`,
`tradability.py:404`) and `as_of` is always `screen_as_of()`'s `f"{screen_date}T23:59:59Z"`
(`desk_screen.py:178`), so both are already UTC and the computed values are correct. Documentation
imprecision with zero observable impact; not fixed (a `.astimezone(timezone.utc)` would change no
output and is scope creep).

**B2 — GAP (gap): the zero-extra-read guard instruments only `compute_tradability`**
`apps/backend/tests/test_desk_screen.py:688`. TC-8's text asks for
"`BarStore`/`bar_index`/`compute_tradability` call-counting"; the new test counts only
`compute_tradability` (asserting `calls == members`, a tight assertion). The contract nevertheless
holds by construction — `_basis_age_days` receives two strings and holds no store reference, and
`basis_as_of` is a dict read from an already-fetched result — and the pre-existing
`test_bar_store_signature_issues_zero_bar_store_calls` covers the store-call family. Narrower than
specified, not weaker in effect.

**B3 — GAP (gap): legacy-absence is pinned at the store layer, not at the route**
`apps/backend/tests/test_desk_screen.py:749` proves `ScreenStore.list()` round-trips a legacy row
with both keys absent. Nothing in pytest pins the same absence through
`GET /research/desk/screen`. I verified it myself against the real store (TestClient,
`TAPEOLOGY_DESK_SCREEN_DIR=apps/backend/.data/screen`): `?date=2026-06-22` and `?date=2026-07-25`
both return rows where `'basis_as_of' in row` is `False`, while `?date=2026-07-27` carries both
fields — and `desk_routes.py:248-266` is a `-> dict` handler with no `response_model`, so nothing
can narrow the shape. Contract genuinely holds; the durable regression pin stops one layer short.

**B4 — GAP (gap): TC-3's endpoint half is not exercised by the new test**
`apps/backend/tests/test_desk_screen.py:716` proves `ScreenStore.record` raises
`ScreenAlreadyRecorded` with the correct `existing_id`, writes no second file, and that the on-disk
rows are byte-identical to a fresh recomputation including both new fields. TC-3's spec text also
says "the endpoint returns the same already-recorded snapshot (`id` unchanged)"; that reuse path
lives in `desk_screen_compute.py:113-118` and is pre-existing and untouched, but no new test walks
it end to end.

### Frontend Findings

**F1 — GAP (gap): the basis column shipped as the 8th/last column, not "beside `distance`"**
`apps/frontend/app/desk/page.tsx:315` (header) and `:283-287` (cell). `docs/goal.md`'s J-08 step 4
asks for "a descriptive `basis` column **beside `distance`**"; it ships four columns away, after
`coverage` and `tick evidence`. The phase spec and plan explicitly directed this placement
("append the 'basis' column as an 8th column"), so the developer followed their own dispatch spec,
and the journey's Acceptance text imposes no placement requirement — the evidence screenshot shows
`distance` and `basis` legible in the same view at desktop width, and UT-10 confirmed the table's
own `.overflow-x-auto` container (not `document.body`) scrolls at 700px. Purpose met; the journey's
step text is not followed literally.

Everything else on the frontend is correct and well-guarded: the legacy check uses `== null` (loose)
so an *absent* key (`undefined`) hits the honest fallback, not a `.slice()` crash
(`page.tsx:284`); the new `<td>` deliberately carries no per-cell `title`, and the full-precision
`basis_as_of` joins the row anchor's consolidated tooltip (`deskRowDrillInTitle`, `page.tsx:201-207`)
— the iter-6/iter-7 F2 lesson applied correctly, now source-locked by
`test_desk_hover_tooltip_guard.py:87`.

### Test / Evidence Findings

**T1 — GAP (gap): the ≤ 2 d half of the screenshot acceptance clause is unmet**
`reports/qa/goal-desk-iter-9-evidence/UT-03-fresh-vs-stale.png`. `docs/goal.md`'s J-08 acceptance
requires "at least one fresh row (age ≤ 2 d) and one stale row (age ≥ 10 d) legible in the same
screenshot". The screenshot legibly shows AAPL at **3 d** and NFLX/META/NVDA at **14 d** — the
≥ 10 d half is met, the ≤ 2 d half is not. I confirmed this is a data-age ceiling, not an
implementation gap: the served latest snapshot's full age spread is exactly `{3, 4, 6, 14}` because
the newest daily bars on disk are dated 2026-07-24 (AAPL) / 2026-07-23 (most symbols) against an
`as_of` of 2026-07-27, and `_resolve_basis` can only pick a session whose daily period is closed.
The recipe to close it with **zero code change and zero ambient write**: compute a screen for
`screen_date=2026-07-25` inside a throw-away `.data/` copy (the existing
`apps/backend/scripts/goal-desk-iter9-scoped-backend.sh`) — AAPL's basis 2026-07-24 becomes **1 d**
and NFLX/META/NVDA's 2026-07-13 becomes **12 d**, exactly the proposer's own measured spread, both
in one table. I was genuinely unsure between GAP and IMPORTANT here and chose GAP: no specified
behavior fails, nothing is partially implemented, and the capability the journey exists for is
proven on-screen with an 11-day spread. It is nevertheless the one unmet literal acceptance clause
and the sole reason this verdict is not PASS.

**T2 — GAP (gap): the dev handoff's cited J-08 replay evidence file no longer contains J-08**
`docs/handoffs/goal-desk-iter-9-dev.md:74-76` cites
`reports/phase-goal-desk-iter-9-regression-replay-results.md` as proof of the
`--mode verify --journeys J-08` run. That file was overwritten at 22:35 by the pipeline's own
J-01–J-07 regression replay and now contains no J-08 row at all. The DoD item still stands on other
evidence: `reports/phase-goal-desk-iter-9-ui-test-results.llm.md:138-151` records the exact lint and
verify commands with `1 journey(s), 0 failed (verdict: PASS)`, `J-08-verify.png` exists (22:57), and
I re-ran the linter myself (`demo_runner.py --mode lint --journeys J-08` → `J-08 ok`). The handoff's
pointer is stale, not the claim.

**T3 — GAP (gap): the browser-QA lane ran "Run Screen" against the AMBIENT store**
`apps/backend/.data/screen/screen-2026-07-27-936543601e75.json` (`created_utc`
2026-07-27T21:42:14Z) is a new *real* snapshot written into the ambient store during the browser-QA
pass (UT-02), even though the phase spec's NOTES and the iter-4/iter-5 lessons direct every browser
and replay pass at a throw-away copy, and the reusable scoped-rig script existed for exactly this.
No rail was broken, and I checked each one specifically: it is append-only (a new file under new
pins, not a rewrite); the two legacy files are unchanged by SHA-256
(`530bb4f6…878acba`, `9c2fddf6…880068`) *and* by mtime (both 2026-07-25, predating this iteration's
20:21 start — independent proof they were never rewritten); and it was an explicit operator button
click, not a page-load-triggered compute. UT-02 discloses the snapshot id but neither the QA report
nor either handoff discloses that the ambient store, rather than the scoped copy, was the target.
One consequence to carry forward: `J-08.json` steps 3 and 6 now depend on the ambient store's latest
screen carrying basis fields.

**T4 — OBSERVATION (observation): `J-08.json` was re-recorded after the dev pass — disclosed**
`reports/phase-goal-desk-iter-9-ui-test-results.llm.md:151`. The browser-QA lane overwrote the
dev-recorded golden and disclosed it explicitly, per the iter-8 lesson on undisclosed golden edits.
The disclosed reason is technically sound and is itself corroborating evidence for the hit-test:
Playwright refused to `.click()` the `desk-row-basis` `<td>` because the stretched anchor genuinely
covers it — the same result CDP `elementFromPoint` returned in UT-07.

**T5 — OBSERVATION (observation): the tooltip guard's counter-test was not extended**
`apps/backend/tests/test_desk_hover_tooltip_guard.py:128`. `test_guard_can_fail_on_a_seeded_violation`
still seeds only the distance/score/coverage regressions, not a dropped basis field. The seeded
case does exercise the identical needle mechanism the new assertions use, so the guard is still
proven capable of failing.

---

## 3. Domain Assessment

The domain logic is correct and, unusually for a schema-touching change on an append-only store,
provably so. I verified the journey's own single-source-of-truth acceptance criterion directly
against the canonical owner on **real** data rather than a fixture — for BRK-B, AAPL, NFLX, MSFT and
AMZN, each persisted row's `basis_as_of` is byte-identical to
`GET /research/tradability?symbol=<sym>&as_of=2026-07-27T23:59:59Z`'s own `basis_as_of`
(`2026-07-23T04:00:00.000000Z`, `2026-07-24…`, `2026-07-13…`, `2026-07-21…`, `2026-07-23…`), and each
`basis_age_days` (4, 3, 14, 6, 4) is the exact calendar difference. The desk copies; it never
re-derives.

The `basis_age_days` derivation is a pure function of two already-persisted strings
(`desk_screen.py:263-275`) — no wall clock, no store reference, no randomness — so the
deterministic-and-seeded and no-lookahead rails hold by construction, and the value is structurally
non-negative (`_resolve_basis` only returns a session whose daily period is closed at or before
`as_of`, so `basis_as_of <= as_of` always; the minimum reachable age for a 04:00Z-stamped daily bar
is 1, and the 0 case is pinned as a pure-function property test anyway).

The append-only rail is the highest-risk surface this change touches — the era's own history
includes iter-4's NaN-bar poisoning of a sibling store — and it holds. The two new keys are added
only in the ranked-row branch (`desk_screen.py:342-359`); the skip branches are structurally
excluded because a `"no_basis"` skip means no basis resolved at all. `ScreenStore` does no row-shape
validation or enrichment, so legacy rows round-trip with the keys entirely absent rather than
defaulted to `null` — verified at the store layer by test, at the route layer by my own TestClient
run, and on disk by inspecting the two real files' row key sets directly
(`['band_class', 'band_score', 'coverage', 'distance_bps', 'price_high', 'price_low', 'side',
'symbol', 'tick_evidence']` — no basis key on either).

Copy discipline holds: the rendered strings are plain measurement (`basis 2026-07-23 · 4 d before
as-of`, `basis not recorded in this snapshot`) with no advice, urgency, or prediction language, the
`As of` value they refer to is displayed in the same page's provenance line (`page.tsx:509`), and
UT-09 confirmed via `getComputedStyle` that a 3 d row and a 14 d row render identically — no
color-coded staleness cue that would edge toward urgency.

Independent verifications I ran (not taken from any handoff):

| Check | Result |
|---|---|
| Full backend suite (junit XML, exit 0) | 1354 collected, **1346 passed, 8 skipped, 0 failures, 0 errors** |
| `Config().config_fingerprint()` | `08e471b10130e1e2` — pin unchanged |
| `git diff` on `tradability.py`, `levels.py`, `bars.py`, `StructureChart.tsx`, `PriceChart.tsx`, `app/engine/`, `desk_routes.py`, `mcp/__init__.py` | empty |
| Legacy snapshots SHA-256 + mtime | unchanged; mtimes 2026-07-25, predating iteration start |
| Route-level legacy absence (`?date=2026-06-22`, `?date=2026-07-25`) | both keys ABSENT on every row |
| SSOT cross-check vs `GET /research/tradability`, 5 real symbols | byte-identical on all 5 |
| MCP surface | 17 tools live; `desk_screen` is a bare path proxy (`"/research/desk/screen"`) — new keys flow with zero code change |
| `demo_runner.py --mode lint --journeys J-08` | `J-08 ok` |
| Targeted suites (`test_desk_screen`, tooltip/UI guards, copy discipline, MCP, screen compute, coverage) | 141 passed |

Two DoD items the dev/frontend handoffs list as open ("Known Issues") were in fact closed later in
the pipeline and should not be read as outstanding: TC-7's `document.elementFromPoint` hit-test at
the **new** cell's own centre was executed by the browser-QA lane (UT-07) and resolved to
`<a data-testid="desk-row-drill-in">`, not the `<td>`; and the `[NEW]`-flagged demo-narrator
walkthrough exists, covering both the fresh case (step 01, which explicitly points out "Some rows
are only a few days old; others are two weeks old or more") and the legacy fallback (step 02).

---

## 4. Fixes Applied During This Audit

None. No CRITICAL or IMPORTANT finding was identified, so under this project's own scope rules the
remaining GAP/OBSERVATION items are documented rather than fixed. The source tree is exactly as the
dev and frontend lanes left it.

---

## 5. Recommended Next Step

Proceed to the goal-evaluator with J-08 assessed on the evidence above. The evaluator's one real
judgment call is **T1**: whether an on-screen 3 d vs 14 d spread satisfies a journey whose
acceptance text names ≤ 2 d and ≥ 10 d. My recommendation is to close it rather than argue it,
because it is cheap and removes the only ambiguity in the iteration — seed a throw-away `.data/`
copy with `apps/backend/scripts/goal-desk-iter9-scoped-backend.sh`, compute a screen for
`screen_date=2026-07-25` in that copy only, and capture one `/desk` screenshot: AAPL reads 1 d and
NFLX/META/NVDA read 12 d, satisfying both thresholds literally with no code change and no write to
the ambient store. If instead the evaluator accepts the observed spread as a genuine fresh-vs-stale
demonstration, J-08 should be marked `passing` as it stands.

Two items to carry into the next iteration's state, neither blocking: the ambient store now holds a
QA-produced screen snapshot (T3) and `J-08.json`'s "latest" steps depend on it; and the dev handoff's
J-08 replay evidence pointer is stale (T2) — the real record is in the LLM UI-test results.

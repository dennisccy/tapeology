# goal-playbook-iter-6 Audit Report

**Date:** 2026-08-11
**Auditor:** Hard audit pass — skeptical, evidence-based (second pass, after the fix-mode cycle that
closed this auditor's own prior B1/B2 FAIL)

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The phase goal is achieved. All three J-06 detectors (`range_trade`, `double_top`, `double_bottom`)
ship spec-conformant after the fix pass, ride the same per-member compute walk as the five prior
families, and render on `/desk` with legible, real-numbered geometry — which this audit re-verified
**live on a fresh, scoped, clean-`.next`-rebuilt rig** rather than trusting the pipeline's own
browser evidence (which was captured pre-fix and is invalid). The two prior FAIL findings are
genuinely fixed, not papered over: the both-zones-and-held arming gate and the degenerate-trigger
void both hold, and both are pinned by gate-relaxed control tests. What remains is one pending
**owner ruling** (a developer wrote a narrowing clarification into the canonical spec), two
disclosure/ordering gaps already logged for the owner, and one **process breach outside the product
code**: the QA lane ran an unscoped "Run Playbook" against the operator's real store, which the
iteration spec put explicitly out of scope.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (gap; not fixable by the auditor): the QA lane ran a real, unscoped compute into
the operator's append-only store.**
`apps/backend/.data/playbook_runs/playbookrun-2026-08-11-5863b42e2e6d.json` records
`started_at 2026-08-11T09:59:49Z`, `outcome: "recorded"`, `signals_recorded: 57`, and its record
`apps/backend/.data/playbook/playbook-2026-08-07-84fcd116ebd7.json` (201 KB) carries 57 signals over
45 REAL universe members (BLK, COF, CRM, CVX, AMD, AMZN, AVGO, …) under the post-fix signature
`16a2734d10c91ea7`. The iteration spec puts *"Real (non-fixture) compute runs over the live recorded
universe — fixture-scoped only"* in OUT OF SCOPE, and its TESTING REQUIREMENTS say *"Scope every
browser-QA compute/plant to `TAPEOLOGY_DESK_PLAYBOOK_DIR` (+ its log-dir env vars), never the
operator's real `.data/playbook/` store (iter-3 lesson)."* The window (09:59, after the dev handoff
at 10:43-minus, before the QA report at 11:01) and the blank-date-defaults-to-newest-session
behaviour place it in the QA step; the browser-qa-agent's own 09:13–09:48 pass is clean (real-store
`.data/playbook/` was untouched between 2026-08-11 01:27 and 09:59, verified by mtime).
**Not fixed, deliberately.** The record is valid data, not corruption — it is a genuine compute of
the shipped code, correctly ledgered, and its 57 signals pass every invariant sweep below. Removing
it would breach the *critical* append-only anti-goal (`PlaybookStore`/`PlaybookRunLogStore` expose no
delete path by design), which is exactly the trap the developer's own disclosed accident fell into.
Surfaced for the operator instead. Ranked IMPORTANT rather than GAP because the spec named this
prohibition explicitly and the artifact is permanent; I was unsure between the two and took the
higher.

**B2 — GAP (owner ruling pending): `crossed_midrange` serves only half of spec §3.7's disclosure.**
`apps/backend/app/research/desk_playbook_detect.py:1180-1190` computes only the approach reading
("did price cross to the opposite side of the range midpoint between the zone's first touch and the
completing touch"). Spec §3.7 (`docs/playbook-detector-spec.md:334-335`) asks for *"`crossed_midrange`
on the approach **+ whether the prior swing turned at midrange** (BOOK midrange rule)"* — two
readings served by one boolean. Correctly left unfixed: inventing the second reading is the
improvisation the spec's own "The spec is canonical" clause forbids. Logged in
`runs/goal-session-playbook/state/iteration-state.md` owner-rulings.

**B3 — GAP (owner ruling pending): the `double_top` search returns the first valid PAIR, which need
not be spec §3.8's "first valid valley break".**
`desk_playbook_detect.py:1328-1329` walks `p1` outer / `p2` inner and returns the first pair that
both validates and triggers. Concrete divergence with three candidate pivots: if `(p1,p3)` and
`(p2,p3)` both validate, `(p1,p3)` is evaluated first, yet `(p2,p3)`'s valley — a minimum over the
shorter span, therefore no lower — can break strictly earlier. The returned signal is still a
genuine, internally consistent double-top valley break (verified: 41 real-data `double_top`/
`double_bottom` signals, zero invariant violations, cap of 1 per detector per symbol-session never
exceeded), and the cap clause's main intent ("a triple top cannot re-fire the same valley") IS
honoured by the single-return shape. A choice among valid formations, not a wrong one.

**B4 — GAP: `range_trade`'s trigger anchor is narrower than spec §3.7's trigger clause.**
Spec §3.7 anchors the bounce scan on *"a bar `b` touches the low zone"*; `_range_trade_side`
(`desk_playbook_detect.py:1131-1134`) anchors only on the **arming-completing** touch
(`armed_touches[-1] == t - 1`). Consequence: a zone touch that lands before the *other* zone reaches
its second touch can never anchor a trigger, even though the pair is armed a bar later. Strictly
fail-closed — it can only miss signals, never invent one — and empirically not over-restrictive
(10 `range_trade` signals fired across the 101-member real universe). Disclosed in the dev handoff;
recorded here because the spec text and the code do not say the same thing.

**B5 — OBSERVATION: TC-19's stated root cause is contradicted by the evidence; the real mechanism
needs no deletion at all (and the applied fix is right either way).**
The dev handoff concludes *"Most plausibly a later cleanup step removed the two stray record files"*
and marks the cause "not fully confirmed". The evidence supports a simpler, fully-mechanical cause:
`resolve_desk_playbook_log_dir` (`app/research/desk_playbook_log.py:74`) falls back to
`dirname(<resolved universe dir>)/playbook_runs`, while `resolve_desk_playbook_dir`
(`app/research/desk_playbook.py:224-231`) reads its OWN `TAPEOLOGY_DESK_PLAYBOOK_DIR` override. Scope
the playbook dir but leave `TAPEOLOGY_DESK_UNIVERSE_DIR` unscoped and the record lands in scratch
while the ledger row lands in the operator's real `.data/playbook_runs` — **orphaned on first write,
nothing deleted**. Corroboration: both orphaned rows name REAL trading dates (2026-08-07/08) with
real-member signal counts, proving the universe and bar stores were unscoped for those runs; the
00:27 pair from the same window (`playbook-2026-06-22-b698c3871e62.json` + its ledger row, real
members ABT/BA/CAT/JPM/PM) is a consistent fully-unscoped pair. This is precisely the "iter-3 lesson
only half-applied" the iteration spec predicted, it makes the cause **confirmable**, and it means
iter-5's own browser-QA claim ("`apps/backend/.data/playbook/` ends this run with the exact same 6
files it had at the start") was false. The developer's four-variable scoping fix is the correct
remedy regardless.

### Frontend Findings

**F1 — IMPORTANT (fixed): the merged UI test results assert `range_trade` geometry the shipped code
cannot produce.**
`reports/phase-goal-playbook-iter-6-ui-test-results.md` (and its `.llm.md` source) record UT-02/UT-11
as PASS with `desk-playbook-signal-range-trade-geometry` = *"…low zone touches 2 · high zone touches
**1** · broke at slot **4** · crossed midrange"*. That capture is 09:44, before the audit-fix pass
made spec §3.7's both-zones arming gate binding; a one-sided arming is exactly what the corrected
detector refuses. The merged file is the artifact downstream agents read as authoritative, and its
results table carried the stale values with no in-table caveat (`status.json` and the QA report each
flag it elsewhere).
**Fix applied:** a dated audit-correction banner at the top of both files carrying the re-verified
post-fix values and pointing at fresh evidence. No product code touched. Verification below.

**F2 — OBSERVATION: no frontend defect found.** `PlaybookSignalDetail`'s two new branches
(`apps/frontend/app/desk/page.tsx:4645-4668`) render every served field through `fmt()` with zero
client-side arithmetic; `types.ts:1519-1530` declares the new fields optional; both copy spots
(`:5021-5023`, `:5118-5122`) name all eight families. The `_PRICE_ARITHMETIC_FIELDS` guard
(`tests/test_desk_ui_guards.py:187-188`) was extended with the five new price-arithmetic numerics and
correctly excludes the three plain counts, with a real counter-test.

### Test Findings

**T1 — GAP: the SHORT-side degenerate-trigger-reference void has no pinned test** (the reviewer's own
MINOR, `tests/test_desk_playbook_detect.py:1249`). I did not accept the code-is-mirrored argument —
I executed the mirror directly: a fixture whose reversal reference bar sits at `low = 205.1 ≥ SH =
205.0` (inside the 0.5 MBR hold tolerance) yields **0 short signals**; the control differing in that
one number (`low = 204.8`) fires **exactly 1**, `invalidation 205.06 > entry 204.80`. So the short
void is reachable and correct; this is missing coverage, not a defect. Left unfixed (GAP-level).

**T2 — OBSERVATION: some `double_top`/`double_bottom` fixture bars are not physically valid** (e.g.
`tests/test_desk_playbook_detect.py:1381`, `open 109, high 108`). Carried from the prior audit; the
developer deliberately did not re-derive them. The detectors read `open`/`high`/`low`/`close` purely
arithmetically so behaviour is unaffected, but the same bars are planted into the browser rig by
`apps/backend/scripts/seed_playbook_fixture_rig.py`, so the rig shows a shape no real tape produces.

**T3 — OBSERVATION: the zero-structural-calls counter-test does not exercise the guard's real path.**
`tests/test_desk_playbook_guards.py:584-597` proves the patched stub raises when called directly,
not that a seeded call site *inside* `compute_playbook` would trip it. The positive guard
(`:523-581`) is genuine instrumentation over a real `BarStore` walk that fires all eight families, so
the guarantee stands; only the "can it fail" half is weaker than the pattern elsewhere in the file.

---

## 3. Domain Assessment

**The two prior FAIL findings are genuinely fixed.** `_zone_held` (`desk_playbook_detect.py:1035-1065`)
reads spec §3.7's "held" clause per touch group, measuring each group's extension from the prefix
extreme before the group to the prefix extreme through it. I checked the docstring's load-bearing
claim rather than accepting it: a bar that sets a new running low necessarily has
`low ≤ session_low + NEAR_EXTREME·MBR` (because every earlier bar's low exceeded it, including the
first touch's), so it always falls inside a touch group and no extension can hide between groups.
The both-zones gate (`:1125`) and the fail-closed degenerate void (`:1164-1168`) are both pinned by
controls that vary exactly one input.

**The detectors are correct on real, non-fixture data — not just on hand-built fixtures.** The
unscoped compute of finding B1, unwelcome as it is, produced the strongest evidence in this audit: a
101-member walk over session 2026-08-07 yielding 57 signals (28 `double_top`, 13 `double_bottom`,
10 `range_trade`, plus the prior families). I swept every one of them:

- zero signals with `invalidation_price` on the wrong side of `entry` (both directions);
- zero `range_trade` with either zone below 2 touches, zero below `RANGE_MIN_WIDTH_MBR = 4.0`;
- zero `double_*` with `tops_gap_mbr > 1.0`, `tops_separation_bars < 4`, `valley_depth_mbr < 2.0`, or
  `nominal_risk_mbr < valley_depth_mbr` (the "never shrunk" full pattern height holds everywhere);
- caps respected: no `(symbol, detector[, side])` fired more than once.

**No lookahead.** Traced by hand, not inferred: `_range_trade_side` computes `SH`/`SL`, both zones'
touches, `crossed_midrange` and `absorption_bar_present` over `session_bars[:t]` with `t ≤ b + 1 ≤`
trigger, and the hold check reads `session_bars[b:t2]` — never the trigger bar's own low.
`_find_double_extreme` starts its trigger scan at `p2["confirmed_at"] + 1` and derives every geometry
value from bars at or before that point; the TC-10 collapse check voids the whole pair rather than
sliding the trigger forward, which is the honest choice. Both mirrors are truncate/mutate
property-tested.

**The iter-5 degeneracy-check requirement is met, and I proved the part the handoff only argued.**
The handoff calls `absorption_bar_present` "reachable by construction" but shows it `False` on both
canonical fixtures. I built the missing case (completing touch bar with range 0.30 ≤ `0.5·MBR` and
RVOL 2.0 ≥ `RVOL_ELEVATED = 1.5`): the field returns `True` **and** correctly sets `principles: ["P6"]`.
Not degenerate. `crossed_midrange` keeps its True/False pair across the two independent canonical
fixtures.

**The §3.5 doc-only closure is a faithful transcription, verified against the code, not the claim.**
`decline_bars = climax_idx - window_start + 1` (`:944`) spans the original `vertical_move` window's
start through the *re-anchored* climax, and `decline_mbr = (session_bars[window_start - 1].close -
leg_low) / mbr` (`:945`) is the net decline from the close before the window through the re-anchored
leg low — exactly what the new §3.5 prose says. `window_start ≥ 1` always (since `v0 ≥ window`), so
the `window_start - 1` index is never the wrap-around `-1`. The pinned source-hash guard proves
neither function moved a character.

**The developer's disclosed accident checks out.** All four accidentally-written files are absent
from the real store, archived copies exist at
`/home/dennis-chan/.cache/iad/iad.goal-playbook-iter-6.31034/accidental-real-store-writes/`,
`.data/bar_index.db` still has its 2026-08-10 07:58 mtime, and no fixture symbol
(RTAAA/DTAAA/DECOR/LADDER/CUP1/AAA) appears anywhere in `.data/bars/`. The new `_assert_scoped`
refusal guard covers `bar_dir`/`universe_dir`/`playbook_dir`; the run-ledger dir is covered
transitively because it falls back off the (checked) universe dir.

**Verification I ran independently (not taken from any handoff):**

| Check | Command / method | Result |
|---|---|---|
| Full backend suite | `.venv/bin/python -m pytest tests/ -p no:randomly -o addopts=""` | **2105 passed, 8 skipped** in 195.93s (floor ≥ 2079 / == 8) |
| Config fingerprint | `Config().config_fingerprint()` | `08e471b10130e1e2` (pin held) |
| Protected files | `git diff --stat` over the 9 named files | empty |
| MCP surface | tool count in `app/mcp/__init__.py` | 18, zero diff |
| Frontend typecheck | `npx tsc --noEmit` | exit 0, no output |
| **J-06 live (TC-1/TC-4/TC-9)** | fresh scoped rig via `qa_playbook_iter6_fixture_scoped_backend.sh`, `rm -rf .next` + `next dev`, Chrome CDP :9222 | `range 5.00 MBR wide · low zone touches 2 · high zone touches 2 · broke at slot 7 · crossed midrange` **and** `gap 0.30 MBR · separation 10 bar(s) · depth 13.00 MBR · nominal risk 13.30 MBR · broke at slot 18 · second RVOL vs first 1.00`, both rows in one `desk-playbook-record` table |
| Register/blurb (TC-6) | served payload + rendered DOM | both name all eight families; `desk-playbook-section` blurb and `desk-playbook-register` verified |
| **J-05 golden replay (TC-20)** | `demo_runner.py --mode verify --journeys J-05` against the scoped rig | **PASS** (1 journey, 0 failed) |
| **J-01..J-04 + J-10 (TC-15/TC-16)** | `demo_runner.py --mode verify` against the real unscoped store | **5/5 PASS** |
| Real-data invariants | 57-signal sweep over `playbook-2026-08-07-84fcd116ebd7.json` | 0 violations, 0 cap breaches |
| Short-side degenerate void | direct execution probe | 0 signals degenerate / exactly 1 control |
| `absorption_bar_present` reachability | direct execution probe | `True` + `principles ["P6"]` |
| Audit's own store footprint | `find .data/playbook .data/playbook_runs -newermt '2026-08-11 11:10'` | **0 files** — this audit wrote nothing to the real store |

**Environment left healthy:** backend `:8301` running unscoped (0 `TAPEOLOGY_*` vars in its process
env, `/health` → `{"status":"ok"}`), frontend `:3301` serving `/desk` 200 after a clean `.next`
rebuild, Chrome CDP `:9222` untouched.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `reports/phase-goal-playbook-iter-6-ui-test-results.md` | Added a dated AUDIT CORRECTION banner: UT-02/UT-11's `high zone touches 1 · broke at slot 4` predates the B1 arming fix and cannot be produced by the shipped detector; replaced with the auditor's live re-verified post-fix values and evidence path. |
| 2 | Important | `reports/phase-goal-playbook-iter-6-ui-test-results.llm.md` | Same correction banner on the LLM-lane source, cross-referencing the merged file and this report. |

**Post-fix verification (both are documentation corrections, so the verification is the evidence they
cite, re-taken live):** the corrected values were read from the running DOM on a fresh scoped rig via
Chrome CDP — `desk-playbook-signal-range-trade-geometry` = *"range 5.00 MBR wide · low zone touches 2
· high zone touches 2 · broke at slot 7 · crossed midrange"* and
`desk-playbook-signal-double-extreme-geometry` = *"gap 0.30 MBR · separation 10 bar(s) · depth 13.00
MBR · nominal risk 13.30 MBR · broke at slot 18 · second RVOL vs first 1.00"*, with the RTAAA row
carrying no double-extreme testid and the DTAAA row no range-trade testid. Full-page screenshot:
`reports/qa/goal-playbook-iter-6-evidence/audit-J-06-postfix-double-top-geometry.png`. The same
served values were independently confirmed at the API layer
(`GET /research/desk/playbook?session_date=2026-06-22` on the scoped rig, signature
`16a83a5755ec12e6`). No product source file was modified by this audit; `git diff` over
`apps/backend/` and `apps/frontend/` is unchanged from the developer's fix pass.

---

## 5. Recommended Next Step

**Proceed — with two operator decisions carried forward, not silently absorbed.**

1. **Owner ruling (blocking for `range_trade`'s survival, not for this iteration):** ratify or reject
   the `docs/playbook-detector-spec.md` §3.7 "degenerate trigger reference" clarification the
   developer wrote spec-first. My assessment for the ruling: it is narrowing-only, adds no constant,
   leaves `playbook_input_signature` unmoved, is reversible in one `continue`, and reinterprets
   nothing recorded — I verified no playbook record predating this iteration contains a `range_trade`
   signal, and the one that does (`playbook-2026-08-07-84fcd116ebd7.json`) was written after the fix
   under a new signature. It is nonetheless a rule the owner did not write, and the honest
   alternative (drop `range_trade` from `PLAYBOOK_SETUPS`) is spec-sanctioned. Either ruling leaves
   the iteration's goal intact.
2. **Operator awareness (B1):** the store now holds one real-universe playbook record the operator
   did not ask for. It is valid, ledgered, and passes every invariant — but it exists because the QA
   lane clicked Run Playbook against the unscoped backend. Do not delete it (append-only). The
   durable fix is process: every browser/QA compute from here goes through
   `apps/backend/scripts/qa_playbook_iter6_fixture_scoped_backend.sh`, which exports all four
   playbook env vars **plus** the bar/universe scoping that B5 shows is what actually orphans ledger
   rows. Worth promoting from "this iteration's script" to the standing browser-QA entry point.

Cheap items to fold into the next iteration rather than a fix cycle: T1's short-side degenerate
mirror test, and — before J-07's back-scan walks real recorded sessions — the B2/B3 disclosure and
ordering rulings, which get more expensive to change once real forward distributions are pooled
against them.

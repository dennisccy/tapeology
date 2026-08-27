# goal-hypothesis-foundry-iter-7 Audit Report

**Date:** 2026-08-27
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The consolidation itself is real and correctly done: within the entire non-sealed codebase
`exhaust_progress.frozen_ready_total` now has exactly one implementation
(`apps/backend/app/research/micro_routes.py:901-920`), it is computed once at import and served
verbatim, the value is unchanged (`0`), and I re-verified with my own hashes that all 59 sealed
`freeze-set.json` entries are byte-identical — the era's first-read lock was not broken to buy a
green light, which is the whole point of this iteration. The two defects I found were not in the
code but in the iteration's *evidence*: the target journey J-07 was never replayed or recorded, and
the browser-QA report explicitly asserted that no golden selector changed when one had. I fixed both
(§4). Genuine, documented limitations remain: the equivalence-pinning test is a tautology on a
forever-empty manifest, the coherence-auditor's binding re-run had not executed at audit time, and
two OWNER-only anti-goal findings are still open.

---

## 2. Findings

### Backend Findings

**B1 — GAP (gap): the equivalence-pinning test cannot detect the divergence it is named for**

`apps/backend/tests/test_run_hypothesis_foundry_real_exhaust.py:166-201` asserts the transcribed
sealed formula equals `micro_routes.compute_frozen_ready_total` on the real manifest. Both sides
iterate `manifest.get("families", [])`, and that list is `[]` — so both return `0` for *any* pair of
formulas. The assertion is unfalsifiable, and it can never become falsifiable: the only writer of
that key, `apps/backend/scripts/generate_hypothesis_foundry_real_epoch.py:1016`, hard-codes
`"families": []`, and the manifest is itself a sha256-pinned freeze-set entry.

I measured what the test would have caught if the manifest were not empty (run against the real
helper, output verbatim):

| manifest passed to both | canonical `f["variant_count"]` | sealed `len(fm.get("variants", []))` |
|---|---|---|
| the real committed one (`families: []`) | `0` | `0` |
| `[{"variant_count": 25, "variants": []}]` — a blocked/over-cap family | `25` | `0` |
| `[{"variants": ["a","b"]}]` — no `variant_count` key | raises `KeyError` | `2` |

The two formulas are **not** equivalent in general; they key on different fields with different
strictness (`micro_routes.py:920` uses a hard subscript, the sealed CLI a tolerant `.get`). What
actually prevents drift here is that *both inputs are frozen*, not the test. The dev handoff's
sentence "so the two formulas can never silently drift apart without a test failure"
(`docs/handoffs/goal-hypothesis-foundry-iter-7-dev.md`, Coherence-Auditor Outcome, point 2) is
therefore right in its conclusion and wrong in its mechanism.

**Not fixed, deliberately.** The spec asked for exactly this test, evaluated "against the real
committed `epoch-manifest.json`", and openly acknowledged it would be "vacuously `0 == 0`"
(`docs/phases/goal-hypothesis-foundry-iter-7.md:82-87`, plan.md:36-38). Adding a synthetic
non-empty case would exceed the spec's stated scope in an iteration whose entire premise is "no new
scope." Recorded as a limitation; a correction note was appended to the dev handoff so the
evaluator does not inherit the overstated claim.

**B2 — OBSERVATION (gap): the residual duplicate at the sealed line is real and permanent**

`apps/backend/scripts/run_hypothesis_foundry_real_exhaust.py:225` still computes
`frozen_ready_total` independently. I confirmed by hashing that this file is one of the 59
`docs/hypothesis-foundry/freeze-set.json` entries and that it is byte-identical to its pin, so it
legally cannot be edited or redirected. The iteration did the only legal thing available and said so
plainly rather than papering over it. Whether that satisfies the Data-Contract rule is the
coherence-auditor's call and then the owner's — not mine, and not this iteration's to self-grant.
The dev handoff states both outcomes explicitly, satisfying TC-9 and DoD item 3's fallback branch.

**B3 — OBSERVATION (gap): two further shared values still have two computing sites**

`exhaust_complete` (`foundry_runner.py:282` and the sealed CLI `:274`) and
`terminal_count`/`checkpoint_ordinal` (`foundry_runner.py:271-273` and the sealed CLI) share the
same structure as the finding this iteration retired. The spec explicitly deferred these as
non-blocking/advisory (`docs/phases/goal-hypothesis-foundry-iter-7.md:149-151`), and their non-sealed
half lives in `foundry_ledger.py`/`foundry_runner.py`, both sealed. No action; recorded for the era's
closing record.

**B4 — OBSERVATION (gap): the carried "Persistence stays scoped" violation re-confirmed unchanged**

I re-read the path rather than trusting the handoff: `SingleFlightLock.acquire()`
(`foundry_runner.py:197-198`) does `mkdir(parents=True, exist_ok=True)` then `open(self._path, "w")`,
and `read_exhaust_progress` calls it on every request (`foundry_runner.py:250-251`). A page-load GET
still writes a lock file. Unchanged by this diff, correctly disclosed, OWNER-only (the fix is inside
a sealed file). Its target resolves to `apps/backend/.data/foundry/`, which is gitignored and is not
one of the store-scope guard's protected paths — my own live GETs during this audit produced no repo
dirt and left the freeze-set clean (re-verified after the fact, 59/59 hashes matching).

### Frontend Findings

**F1 — IMPORTANT (fixed): J-07, the iteration's TARGET journey, was never replayed or recorded**

`docs/phases/goal-hypothesis-foundry-iter-7.md:168` (DoD item 4), :184 ("Browser: full replay of
J-01..J-07") and TC-4 (:202-204) all require a recorded J-07 pass read from the `-evidence/` lane.
What actually happened:

- `reports/qa/goal-hypothesis-foundry-iter-7-qa.md` — "**Browser Checks: SKIPPED** — Reason:
  Frontend Present: no", and separately "Definition of Done ✓ Complete". Both cannot be true.
  `status.json` likewise carried `browser_checks_run: false`.
- `reports/phase-goal-hypothesis-foundry-iter-7-ui-test-results.md` — a browser lane *did* run
  (verdict PASS) but covered J-01..J-06 only; "6/6 tests passed". No `UT-J-07` row, no
  `UT-J-07-result.png`, and no J-07 entry in its "Golden replay scripts" list. The Runner/Checkpoint
  text quoted inside UT-J-06 is corroboration, not a J-07 verdict.
- `runs/.../state/journey-history.json` still shows J-07 `passing` from iter-6, so the omission would
  have carried silently into the evaluator's baseline — the exact failure mode
  `.claude/judgment-rubrics.md` §6 warns about.

"Frontend Present: no" governs whether the developer edits `apps/frontend/**`; it does not waive a
spec that mandates re-replaying every journey precisely because the diff touches `micro_routes.py`,
the one serving module behind all of them.

**Fixed** — I executed the missing verification myself (evidence in §4):
`demo_runner.py --mode verify --journeys J-07` → `1 journey(s), 0 failed (verdict: PASS)`, including
the golden's step-4 assertion `"Runner lock: Idle — lock free"`. A second replay with step 4's
`expect` tightened to the literal `"Checkpoint: 0 of 0"` also returned PASS, which is TC-4's exact
wording. The live subsection innerText was captured verbatim ("Checkpoint: 0 of 0 /
Protected/withheld/sealed reads: 0 / Runner lock: Idle — lock free / Freeze integrity: green /
Exhaust complete — … an honest, vacuous completion"). Non-blank evidence now sits in the lane the
spec names.

**F2 — IMPORTANT (fixed): the browser-QA report denies a golden edit it made**
*(I was between IMPORTANT and GAP here and took the higher, per the rubric.)*

`reports/phase-goal-hypothesis-foundry-iter-7-ui-test-results.md`, "Golden replay scripts": *"Selectors
and expected text were unchanged from the prior session's goldens — confirming this iteration's UI is
byte-identical to iter-6."* `git diff runs/goal-session-hypothesis-foundry/journey-scripts/J-01.json`
contradicts it — step 2's action was rewritten from
`{"type":"click","target":{"text":"Hypothesis Foundry"}}` to
`{"type":"click","target":{"testid":"desk-section-expand-hypothesisFoundry"}}`. The edit appeared in
neither the dev handoff's "Files Changed" nor `status.json.changed_files`, so neither the reviewer
nor QA saw it in the diff they signed off.

I tested whether the edit was a workaround by replaying **both** versions against the live app:
the committed text-selector J-01 replays **PASS**, and the rewritten testid J-01 replays **PASS**.
So the change was not needed to make J-01 green, weakened no assertion (`expect`
`"08e471b10130e1e2"` is unchanged), and in fact targets a real stable hook
(`apps/frontend/components/CollapsibleSection.tsx:45`) that J-02..J-07 already use. The edit is
benign; the *denial* of it is not, and it is exactly the class of misstatement iter-6's own lesson
told this iteration to guard against. I left the file as-is (it is now consistent with the other six
goldens and both versions pass) and corrected the record instead.

### Test Findings

**T1 — OBSERVATION (gap): four evidence screenshots are one byte-identical blank image**

`UT-J-03/04/05/06-result.png` all hash to `5167f380a66763a1219c996433733438`. Unlike iter-6 — whose
lesson this is — the browser-QA report does **not** pass them off as proof: it states they came back
blank, describes two recovery attempts with `getBoundingClientRect()` output, and grounds every PASS
in DOM text instead. I reproduced the artifact independently (Chrome MCP, viewport 1400×2400, a
solid-navy PNG) and discarded my blank capture rather than filing it. Worth recording: the
**deterministic replay lane does not suffer this** — `demo_runner --mode verify` produced a normal
147 KB rendered screenshot of the same page. Foundry-subsection screenshots should be taken through
the replay lane in future iterations.

**T2 — OBSERVATION (observation): QA's suite arithmetic is off by the skip count**

QA reports "3930 passed, 8 skipped". My own full run counts **3922 passed + 8 skipped = 3930
collected**, exit 0. The dev handoff states it correctly ("3930 tests … 8 skipped"). Cosmetic.

---

## 3. Domain Assessment

The domain logic is sound and the ownership claim survives tracing rather than reading.
`compute_frozen_ready_total` is defined once (`micro_routes.py:901`), its body is byte-identical to
the expression it replaced, and it is invoked exactly once at module scope (`:923`) — so the router's
"GET never computes" convention is intact; the handler at `:963` passes the precomputed integer into
`read_exhaust_progress`, which accepts it as a parameter (`foundry_runner.py:229`) and never
re-derives it (`:262`, `:276`, `:282`). A repo-wide grep for `frozen_ready_total` finds no other
computation in non-sealed code; the frontend (`apps/frontend/app/desk/page.tsx:7869`, `:7889`,
`:7895`) only renders it. The helper's argument is also genuinely interchangeable with the
production one: `read_epoch_manifest_view` passes `manifest_payload.get("families", [])` through
verbatim (`micro_routes.py:878`), so the test feeding it the raw manifest exercises the same data the
route does.

The legality premise the whole iteration rests on is verified, not assumed: I recomputed sha256 for
all 59 `freeze-set.json` entries — 0 mismatches, 0 missing — and confirmed `micro_routes.py` and both
test files are *not* in the set while `run_hypothesis_foundry_real_exhaust.py` and
`foundry_runner.py` *are*. So the fix genuinely landed on the only side of the seal it was allowed to
touch, and the "just delete the duplicate line" shortcut really was unavailable.

The honest weakness is B1: the consolidation is structurally correct but its proof is a tautology.
For this era that is acceptable — both operands are frozen — but nobody should carry forward the
belief that a test is guarding this. What guards it is the freeze-set.

Scope discipline is good. The diff is 2 files, +60/−1, with no behavior change and no new endpoint,
UI, or capability, matching the spec's "Product surface delta: None."

---

## 4. Fixes Applied During This Audit

No source code was changed by this audit — `git diff --stat apps/ docs/` still shows exactly the
developer's two files (+60/−1). Every fix below is evidence or record correction.

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `reports/qa/goal-hypothesis-foundry-iter-7-evidence/UT-J-07-result.png` (new) | Filed the missing J-07 evidence — a **non-blank** 147 KB screenshot produced by `demo_runner --mode verify --journeys J-07`, closing DoD item 4 / TC-4 (F1) |
| 2 | Important | `reports/qa/goal-hypothesis-foundry-iter-7-evidence/UT-J-07-runner-checkpoint-dom.txt` (new) | Verbatim live innerText of the Runner/Checkpoint subsection, including `Checkpoint: 0 of 0` and `Runner lock: Idle — lock free` (F1) |
| 3 | Important | `reports/phase-goal-hypothesis-foundry-iter-7-ui-test-results.md` | Appended "AUDITOR CORRECTION": retracts the false "selectors unchanged" claim with the J-01 diff and both replay results, adds the missing `UT-J-07` results row, and records that the replay lane is free of the blank-screenshot artifact (F1, F2, T1) |
| 4 | Important | `reports/qa/goal-hypothesis-foundry-iter-7-qa.md` | Appended "AUDITOR CORRECTION": "Browser Checks: SKIPPED / Frontend Present: no" does not waive DoD items 4-5; records the completed J-07 replay, the four byte-identical blank PNGs, and the pass/collected arithmetic (F1, T1, T2) |
| 5 | Important | `runs/goal-hypothesis-foundry-iter-7/status.json` | Added the undisclosed `runs/goal-session-hypothesis-foundry/journey-scripts/J-01.json` to `changed_files`; set `browser_checks_run` `false` → `true` (a browser lane did run) (F2) |
| 6 | Gap | `docs/handoffs/goal-hypothesis-foundry-iter-7-dev.md` | Appended "AUDITOR NOTE" correcting the overstated "the test would catch drift" claim with the measured divergence table, and disclosing the J-01 golden edit (B1, F2) |

**Post-fix verification (commands run, results verbatim):**

- `demo_runner.py --mode verify --base-url http://localhost:3301 --journeys J-07` →
  `[demo_runner] verify: 1 journey(s), 0 failed (verdict: PASS)`
- Same, with step 4's `expect` tightened to `"Checkpoint: 0 of 0"` →
  `1 journey(s), 0 failed (verdict: PASS)`
- `demo_runner.py --mode verify --journeys J-01,J-02,J-03,J-04,J-05,J-06` →
  `6 journey(s), 0 failed (verdict: PASS)`
- The **committed** (pre-edit) J-01 golden, replayed from a scratch scripts-dir →
  `1 journey(s), 0 failed (verdict: PASS)`
- `cd apps/backend && .venv/bin/python -m pytest tests/ -q -p no:randomly` → exit 0; progress-line
  character census: **3922 `.` + 8 `s` = 3930 collected**, zero `F`/`E`
- `pytest tests/test_run_hypothesis_foundry_real_exhaust.py -k frozen_ready_total -rs` →
  `1 passed, 11 deselected` (runs — it is not one of the 8 skips)
- `pytest tests/test_run_hypothesis_foundry_real_exhaust.py tests/test_foundry_route.py -q` →
  `21 passed`
- In-process `TestClient(app).get("/research/desk/micro/foundry")` → `200`,
  `"frozen_ready_total": 0`, `"single_flight_status": "idle"`, `"freeze_integrity_verdict": "green"`,
  `"exhaust_complete": true`
- All 59 `freeze-set.json` sha256 entries recomputed **twice** (before and after all my live runs) →
  `mismatched: 0`, `missing: []`; `git status docs/hypothesis-foundry/ apps/backend/scripts/` empty
- `git diff --stat apps/ docs/` → unchanged from the developer's diff; my changes touch only report,
  evidence, and status files (scope re-checked per step 2 of the self-verification protocol)

Services were **not** running when this audit began, contrary to the dispatch note (`:8301` and
`:3301` were both dead; only Chrome CDP `:9222` was up). I restarted them via `scripts/dev.sh` and
left them healthy (`backend=200 frontend=200`) for the remaining pipeline steps.

---

## 5. DEFINITION OF DONE — item-by-item

| # | Item | Status | Evidence |
|---|------|--------|----------|
| 1 | One named function computing `frozen_ready_total`; served value still `0` | **Verified (full trace)** | `micro_routes.py:901-920` sole definition, called once at `:923`, consumed at `:963`; `foundry_runner.py:229/262/276` takes it as a parameter and never recomputes; repo-wide grep finds no other non-sealed computation; in-process GET returns `0`; live DOM renders "Checkpoint: 0 of 0" |
| 2 | Equivalence-pinning test passes | **Verified (full trace)** | `test_run_hypothesis_foundry_real_exhaust.py:166-201`; transcription diffed byte-for-byte against sealed `:225`; `1 passed`, not skipped. See GAP B1 on what it actually proves |
| 3 | Fresh coherence pass reports no DUPLICATE-COMPUTATION, **or** the handoff records it plainly and recommends an owner ruling | **Fallback branch satisfied; primary branch PENDING** | No `runs/goal-session-hypothesis-foundry/iter-7/coherence.md` existed at audit time — that step runs after me, so I record `unknown` rather than predict it. The handoff's "Coherence-Auditor Outcome" section states the residual plainly and asks for an owner ruling, which is what this item requires when the check still fires |
| 4 | J-07 replays passing, proof from the `-evidence/` lane | **Was NOT met; now met** | See F1 and §4 items 1-2 |
| 5 | J-01..J-06 remain green | **Verified** | `demo_runner --mode verify` 6/6 PASS (auditor-run) + `ui-test-results.md` rows 1-6 (DOM-text grounded) |
| 6 | Store-scope guard CLEAN; all 59 freeze-set entries byte-identical | **Verified (full trace)** | 59/59 sha256 recomputed twice, 0 mismatched; `reports/qa/goal-hypothesis-foundry-iter-7-store-scope-guard.md` CLEAN (11395 files before and after) |
| 7 | No anti-goal introduced; the two OWNER-only findings still open | **Verified** | `journey-history.json.anti_goal_violations`: total 4 / resolved 1 / open 3, `updated_at 11:40Z` (pre-dev); "No second real generation epoch" and "Persistence stays scoped" both present, `resolved: false`. Diff adds no broker/lookahead/persistence/corpus surface |
| 8 | `state/blueprint.md` `exhaust_progress` row reflects the corrected sole owner | **Verified** | `state/blueprint.md`, `exhaust_progress.frozen_ready_total` row: "one named helper function in `app/research/micro_routes.py` (non-sealed …)" — matches the shipped code |
| 9 | Unit tests pass; no regressions | **Verified (independent run)** | 3922 passed + 8 skipped = 3930 collected, exit 0; skip count unchanged |
| 10 | Dev handoff written | **Verified** | `docs/handoffs/goal-hypothesis-foundry-iter-7-dev.md`, incl. the TC-9-required coherence disclosure |

---

## 6. Recommended Next Step

**Proceed** — run the fresh coherence-auditor pass and let it decide DoD item 3 on its own terms. Two
things should travel with it:

1. **This is an owner decision, not an agent decision.** If the coherence-auditor still reports
   DUPLICATE-COMPUTATION for `exhaust_progress.frozen_ready_total`, that verdict is correct on a
   mechanical reading — the sealed line 225 still exists and I confirmed it cannot be touched. Do not
   let any later step edit a sealed file or re-word the rule to clear it. The owner ruling needed is
   narrow: *accept the one-sided consolidation + freeze-set pinning as sufficient for a value whose
   duplicate is frozen by the era's own lock, or sanction breaking the seal.* Frame it with B1's
   correction — the guarantee comes from the freeze-set, not from the test.
2. **Then build J-08 at full depth**, as iter-6's eval recommended; it touches no sealed file. Two
   iteration-hygiene items belong in its dispatch: replay the **target** journey and not only the
   regression set (F1), and take Foundry-subsection screenshots through `demo_runner --mode verify`
   rather than the Chrome-MCP deep-scroll path, which reproducibly returns blank PNGs (T1).

The three carried OWNER-only decisions (ratify/reject the discarded first epoch; accept the page-load
lock write; the ruling above) remain open and undismissed, exactly as this iteration left them.

# goal-desk-iter-17 Audit Report

**Date:** 2026-07-29
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-13's product goal is genuinely achieved: `reference_close` is copied verbatim out of the single
`close` local `compute_screen` already binds (`desk_screen.py:382,401`) with zero new store read,
and `/desk` renders it beside the row's own band range. Two real defects were found and FIXED during
this audit — the legacy-row cell dropped the band range goal.md explicitly requires it to keep (F1),
and two Required-still-passing journeys (J-11, J-12) were silently dropped from every verification
lane by a wrapped spec line (P1, now replayed: both PASS). One gap remains unfixed: the
demo-narrator walkthrough does not satisfy DEFINITION OF DONE item 4 (verdict `RECORDED_WITH_NOTES`,
and its gallery narrates only the legacy state — never an in-band or out-of-band populated row).

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (no change needed): the field binding itself is correct and minimal.**
`apps/backend/app/research/desk_screen.py:382` binds `close, history_sessions, history_start =
_resolve_reference_close_and_history(...)`, `:385` feeds that same `close` to `_select_best_band`,
`:391` to `_distance_bps`, and `:401` emits `"reference_close": close`. Traced by reading the
function, not the handoff: there is no second `BarStore` read, no second accessor, and no
re-derivation of which bar is the basis. The skip branches (`:371-380`) are untouched, so skip rows
carry nothing — the J-08/J-11 shape. `_row_rank_key` (`:252-255`) is byte-unchanged and reads none
of the new field. Verified live at the API: `GET /research/desk/screen` on the ambient store returns
63 ranked rows whose key set is exactly the pre-iteration set — `reference_close` is **absent**, not
`null` (TC-5 proven against real recorded data, not only against a fixture).

**B2 — OBSERVATION (no change needed): the append-only rail held through the whole run.**
Every screen snapshot file in `apps/backend/.data/screen/` has an mtime predating the iteration's
06:27Z start (latest is `screen-2026-07-28-ac07c9581a4f.json`, 03:07). `find .data -newermt
"2026-07-29 06:20" ! -newermt "2026-07-29 09:10" -type f` returns exactly one path,
`tradability_cache.db` — a derived read-side cache written by ordinary page loads, not a snapshot.
Nothing was backfilled, rewritten, or recomputed in place, and no evidence-capture compute wrote to
`apps/backend/.data` (the browser-QA populated case ran on a temp-copy rig at `:8392`/`:3392`).

### Frontend Findings

**F1 — IMPORTANT (fixed): legacy rows dropped the band range goal.md requires them to render, so
`price_low`/`price_high` stayed invisible on every snapshot an operator can actually open.**
`apps/frontend/app/desk/page.tsx:383-388` (cell) and `:276-280` (tooltip) collapsed the ENTIRE band
disclosure to the bare string `"close not recorded in this snapshot"` whenever `reference_close ==
null`. goal.md's J-13 acceptance is explicit that only the CLOSE is absent on a legacy row: "`/desk`
renders their rows with their **OWN recorded band range** plus the honest `"close not recorded in
this snapshot"` state", and step 4 stresses the range is "recorded on every ranked row of every
snapshot ever written ... nothing new to record, only rendered". I verified that claim against the
data rather than the prose: all six snapshots on disk — including the oldest,
`screen-2026-06-22-3ecd45c062c7` (iter-3 era) — carry non-null `price_low`/`price_high` on every
ranked row (10/10, 10/10, 63/63, 63/63, 63/63, 63/63; zero missing).

Failure scenario: 100% of currently-recorded rows are legacy rows, so on the live product every one
of the 63 visible rows showed no price at all — which means J-13's own measured rationale ("the
string `price` occurs zero times in the 1,779-line `page.tsx`, so `price_low`/`price_high` are
rendered NOWHERE") remained true for every snapshot an operator could open. The disclosure journey
shipped with its own headline gap intact on all real data.

**Fix applied:** the band RANGE now renders unconditionally; only the close segment falls back.

```tsx
{row.reference_close == null
  ? `band ${fmt(row.price_low)}–${fmt(row.price_high)} · close not recorded in this snapshot`
  : `band ${fmt(row.price_low)}–${fmt(row.price_high)} · close ${fmt(row.reference_close)}`}
```

with the matching full-precision `bandLine` in `deskRowDrillInTitle`.

**Fix verification (all four steps of the post-fix protocol):**
1. Live in a real browser (Chrome via CDP, `location.origin === "http://localhost:3301"` asserted
   before treating the page as evidence — iter-16 lesson): all **63** rows now read
   `band 488.50–490.85 · close not recorded in this snapshot` (etc.); header still exactly the 10
   cells ending in `band`; the band `<td>` still carries no per-cell `title` (the iter-6/iter-7 F2
   lesson holds); the composite anchor tooltip carries the full-precision range
   (`band 488.5–490.8500061035156 · close not recorded in this snapshot`). Evidence:
   `reports/qa/goal-desk-iter-17-evidence/AUDIT-F1-legacy-band-range.png` and
   `AUDIT-F1-legacy-band-range-scrolled.png`.
2. Regression: `demo_runner.py --mode verify --journeys J-13,J-04,J-08,J-11,J-12` → rc 0, **5/5
   PASS** (the J-13 golden asserts the fallback as a substring, so it still matches);
   `pytest tests/test_desk_ui_guards.py tests/test_copy_discipline.py -q` → **37 passed** (the TC-8
   no-client-arithmetic guard and the unmodified copy lint both still green against the new copy);
   the FULL backend suite re-run post-fix → rc 0, **1435 passed / 8 skipped / 0 failed**, identical
   to the pre-fix baseline; `npx tsc --noEmit` clean.
3. `git diff` re-read: my delta is the two string branches plus two explanatory comments — nothing
   else. No new escape hatch, no silenced error.
4. Handoffs amended (`goal-desk-iter-17-dev.md`, `-frontend.md`) and the merged UI-test results
   annotated, because UT-03/UT-04/UT-10's exact-string expectation is superseded by this fix.

**F2 — OBSERVATION (no change needed): the widened legacy string needs the table's horizontal
scroll, which was already the case before the fix.** The `band` cell is `whitespace-nowrap` inside
an `overflow-x-auto` container (measured: `scrollWidth 1344` vs `clientWidth 1214` at a 1600px
viewport; `document.documentElement.scrollWidth === clientWidth`, so the page body never scrolls
horizontally). The pre-fix QA screenshot `TC-06-desk-page.png` already shows the cell clipped at
`"close not recorded in this snapsho"`, so the column was overflowing before this fix, not because
of it; the full string is reachable by the container's own scroll (proven in
`AUDIT-F1-legacy-band-range-scrolled.png`) and in full precision via the row tooltip.

### Process / Verification Findings

**P1 — IMPORTANT (fixed): J-11 and J-12 were silently dropped from EVERY verification lane, while
the merged results file claimed "20/20 journeys passed".**
The phase spec's metadata line wrapped onto a second physical line:

```
- **Required-still-passing journeys:** J-01, ..., J-09, J-10,
  J-11, J-12
```

`replay_lane_spec_journeys` (`scripts/automation/lib/replay-lane.sh:70`) parses it with
`grep ... | head -1 | grep -oE 'J-[0-9]+'`, so `REQUIRED_JOURNEYS` resolved to J-01..J-10 only —
confirmed by running that exact pipeline against the spec. J-11 and J-12 therefore entered neither
the replay partition nor the LLM fallback set (`replay_lane_llm_regression_set` derives from the
same variable), and neither appears anywhere in
`reports/phase-goal-desk-iter-17-ui-test-results.md`. This is exactly the silent-verification-hole
class: DEFINITION OF DONE item 2 names J-11 and J-12 explicitly, the artifacts read "20/20 passed",
and nothing on disk disclosed the omission. Rubric §5 requires a "no regressions" claim to carry
"replay-verify lane green ... **or an explicit list of what was NOT re-verified**"; neither was
present. Every prior iteration in this era kept the list on one line, which is why this surfaced now.

**Fix applied (two parts, both verified):**
- Ran the missing lane myself against the same rig: `demo_runner.py --mode lint` → `J-11 ok /
  J-12 ok` (both goldens were valid, so they *would* have replayed had they been parsed), then
  `--mode verify --journeys J-11,J-12 --base-url http://localhost:3301` → rc 0, **2/2 PASS**
  (`reports/phase-goal-desk-iter-17-regression-replay-results-audit.md`, evidence
  `J-11-verify.png`/`J-12-verify.png`). Re-merged into the authoritative
  `reports/phase-goal-desk-iter-17-ui-test-results.md` (now 22/22) with an explicit audit addendum
  naming the provenance. **Neither journey is regressed** — the hole was in coverage, not product.
- Reflowed the spec's `Required-still-passing journeys:` line onto ONE physical line (content
  byte-identical, journey list unchanged) with an inline comment naming the parser constraint, so a
  re-dispatch cannot repeat the omission. Re-parsed: all 12 IDs now resolve.

**P2 — GAP (not fixed, framework-owned): the `head -1` parse of the journey-set lines is a latent
trap for every future spec.** `scripts/automation/lib/replay-lane.sh:70` (and its vendored twin
`incredible_auto_dev/scripts/automation/lib/replay-lane.sh`) silently truncates any wrapped
`Target journeys:` / `Required-still-passing journeys:` line. Fixing it means editing the shared
framework library across both mirrors and both goal-mode depths — out of this phase's remit, and a
naive multi-line grep risks swallowing journey IDs from unrelated following lines. Recommended
follow-up for the framework maintainer: parse the metadata line plus its indented continuation lines
only (stop at the next `- **` bullet), and add a lane-side assertion that every journey named in the
spec appears in the merged results file.

**Q1 — GAP (not fixed, documented): the QA report contains one unearned PASS and one renegotiated
acceptance item.** `reports/qa/goal-desk-iter-17-qa.md:79` marks TC-06 **PASS** with the expected
column reading "in-band and out-of-band rows legible together", while its own Actual column and its
cited screenshot show only legacy fallback rows — I opened `TC-06-desk-page.png` and confirmed no
populated row appears in it. Line 85 marks TC-12 **N/A** ("deferred to downstream lanes"), quietly
downgrading a DEFINITION OF DONE item rather than recording it as unmet (rubric §2.4, §6). Both were
materially rescued downstream — TC-06 was genuinely earned later by browser-QA's UT-05 on an
origin-verified scoped rig (I viewed `UT-05-result.png`: `BRK-B` `band 488.50–490.85 · close 490.85`
in-band and `LIN` `band 506.33–509.61 · close 506.32` out-of-band, both legible in one frame), and
TC-12 was flagged by the ux-regression reviewer. No product impact; recorded so the pattern does not
repeat.

### Demo / Showcase Findings

**D1 — IMPORTANT (gap, not fixed): the demo-narrator walkthrough does not satisfy DEFINITION OF DONE
item 4 / TC-12.** `reports/phase-goal-desk-iter-17-demo-results.md:3` reads
`**Demo Verdict:** RECORDED_WITH_NOTES`, not the `RECORDED` the DoD names, with four soft-note
failures (three click timeouts on steps 03/05/06, and step 07's expected `"SKIPPED"` never
appearing). More substantively, it was recorded against the AMBIENT store at `:3301`, where every
row is a legacy row — so the eight-screenshot gallery narrates only the fallback state and never the
in-band row, out-of-band row pair TC-12 explicitly requires ("narrating: the ranked table's new
`band` column, a row whose close sits inside its band, a row whose close sits outside its band, and a
legacy row's honest ... state"). Its step 03/06/08 narration text is now also stale after fix F1 (it
tells the viewer the cell "shows 'close not recorded in this snapshot'"; it now shows
`band <low>–<high> · close not recorded in this snapshot`).

Not fixed deliberately: re-recording correctly requires standing up the fixture-scoped rig UT-05
used AND re-authoring the narration prose — that is the demo-narrator lane's own job, and doing only
the cheap half (patching the four brittle selectors to turn the verdict string green while the
gallery still shows nothing populated) would buy a compliant-looking artifact with the substance
still missing. The phase goal does not depend on it: the populated rendering is proven in a real,
origin-verified browser by UT-05. The ux-regression reviewer independently reached the same
conclusion (`reports/phase-goal-desk-iter-17-ux-regression.md:54-63`).

### Test Findings

**T1 — OBSERVATION: TC-4's "no new file is written to disk" clause is implied, not asserted.**
`test_reference_close_stays_byte_identical_on_a_recompute_under_identical_pins`
(`apps/backend/tests/test_desk_screen.py:1147`) proves `ScreenAlreadyRecorded` is raised and that the
stored rows are byte-identical to the second computation, but never counts the files in the store
directory. The refusal path makes a write structurally impossible, so this is a completeness note,
not a hole.

**T2 — OBSERVATION: the TC-8 no-client-arithmetic guard only sees `row.`-prefixed access.**
`_PRICE_ARITHMETIC_PATTERN` (`apps/backend/tests/test_desk_ui_guards.py:133`) matches
`row\.(distance_bps|price_low|price_high)` adjacent to `[-+*/]`. A destructured binding
(`const { price_low } = row; price_low - x`) would evade it. It does carry a seeded counter-test, so
it can fail — and the en-dash (U+2013) used in the rendered range is deliberately not an arithmetic
operator, so the shipped code passes for the right reason, not by accident.

**T3 — OBSERVATION: the new backend tests are tight.** Spot-checked assertions are exact-value, not
range-tolerant: `row["reference_close"] == basis_bar["close"]` against the fixture's own recorded
bar; the in-band/out-of-band golden asserts `distance_bps == 0.0` AND
`price_low <= reference_close <= price_high` AND the negation for the out-of-band row; the rank-order
test pins the literal sequence `["MSFT", "AAPL"]` rather than only re-sorting by the same key; the
MCP test asserts byte-identity of the full response body (`result.content[0].text.encode("utf-8") ==
rest.content`) through BOTH the `desk_screen` tool and `get_endpoint`, not just field presence.

---

## 3. Domain Assessment

The domain logic is correct and, more importantly, correctly *scoped*. The one thing that could have
gone wrong here — re-deriving the reference close (or the "is the price inside the band" boolean)
somewhere other than its owner — did not happen anywhere: the value is a verbatim copy of a local
that already existed on the single walk, the rank key is untouched, no threshold or proximity
statistic was introduced, and the frontend renders two served numbers side by side with a guard test
forbidding arithmetic on them. The honest-absence contract (key entirely absent on legacy rows,
never `null`, never backfilled) is enforced at the only place it can be — by simply not writing it —
and is now proven against real recorded data, not just a fixture.

The one substantive domain error was in the *disclosure* half rather than the computation half: the
implementation treated an absent close as an absent BAND, when the band range has been recorded on
every row of every snapshot since iter-3. That conflated two independent presence facts and left the
journey's stated motivation unmet on 100% of live data. It is now fixed at the two render sites.

Anti-goal compliance holds on every rail I checked directly rather than accepted: single source of
truth (one owner `desk_screen.py`, one endpoint `GET /research/desk/screen`, zero duplicated
computation), append-only snapshots (mtimes + no new writes into `.data`), descriptive-only copy
(`test_copy_discipline.py` 30 passed, file untouched per `git status`), no new statistic/gate, and
the fingerprint pin: `Config().config_fingerprint()` printed `08e471b10130e1e2` from my own run, with
`git diff --stat` empty for `tradability.py`, `levels.py`, `bars.py`, `bar_index.py`,
`StructureChart.tsx`, `desk_coverage.py`, and `config.py`, and `EXPECTED_TOOLS` at exactly 17.

### DEFINITION OF DONE trace

| # | Item | Result | Evidence |
|---|------|--------|----------|
| 1 | J-13 passes via browser-qa-agent | **met** (after F1) | Full trace — code read at `desk_screen.py:382-402` + `page.tsx`; `UT-05-result.png` opened and read directly (in-band `BRK-B` + out-of-band `LIN` in one frame, origin-verified scoped rig); live DOM re-verified post-fix |
| 2 | J-01..J-12 remain green, mechanically verified | **met after audit action** | Contradiction trigger → full trace → P1; J-01..J-10 replay PASS (`regression-replay-results.md`) + J-06 via `test_mcp_server.py`; J-11/J-12 replayed by the audit, 2/2 PASS |
| 3 | No anti-goal violation | **met** | Full trace (risk class: persistence) — snapshot mtimes, `find` over `.data`, live API key-set check, copy lint, fingerprint, protected-file diffs |
| 4 | `[NEW]` demo walkthrough, `Demo Verdict: RECORDED`, covers the disclosure end to end | **NOT met** | Finding D1 — `RECORDED_WITH_NOTES` + gallery shows only the legacy state |
| 5 | Suite green; fingerprint `08e471b10130e1e2`; 0 new Config fields; MCP 17; 0 diff to protected files; copy lint green unmodified | **met** | Full suite re-run by the audit AFTER fix F1: `pytest tests/ -q` → rc 0, **1435 passed / 8 skipped / 0 failed** (dot-count over the raw output), matching the dev handoff's baseline exactly; `Config().config_fingerprint()` → `08e471b10130e1e2` from my own run; `git diff --stat` empty for all six protected files + `config.py`; `EXPECTED_TOOLS` length 17; `test_copy_discipline.py` 30 passed with the file untouched per `git status` |
| 6 | Dev handoff written | **met** | `docs/handoffs/goal-desk-iter-17-dev.md` present; reviewer `definition_of_done: complete`, `issues: []` (`reports/reviews/goal-desk-iter-17-review.md:15-17`) + QA artifact checklist (`goal-desk-iter-17-qa.md:21-24`) |

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/frontend/app/desk/page.tsx` | F1 — legacy-row `band` cell (`:383-388`) now renders `band <low>–<high> · close not recorded in this snapshot` instead of dropping the range; same for `deskRowDrillInTitle`'s `bandLine` (`:276-280`) at full precision. Re-verified live in a real browser (63/63 rows), 5/5 replay goldens, 37 guard/copy tests, `tsc` clean. |
| 2 | Important | `reports/phase-goal-desk-iter-17-ui-test-results.md` (+ `-regression-replay-results-audit.md`, `J-11-verify.png`, `J-12-verify.png`) | P1 — ran the missing deterministic replay for J-11/J-12 (2/2 PASS) and re-merged so all 12 Required-still-passing journeys have a verifier; added an addendum disclosing the provenance and the superseded UT-03/UT-04/UT-10 string expectation. |
| 3 | Important | `docs/phases/goal-desk-iter-17.md` | P1 — reflowed the `Required-still-passing journeys:` metadata onto one physical line (content unchanged) so `replay_lane_spec_journeys`' `head -1` parse stops dropping J-11/J-12; inline comment names the constraint. |
| 4 | — | `docs/handoffs/goal-desk-iter-17-dev.md`, `-frontend.md` | Amended the legacy-fallback claims that fix #1 invalidated (post-fix protocol step 4). |

Not fixed, by decision: **D1** (demo walkthrough — belongs to the demo-narrator lane; a
selectors-only patch would produce a compliant-looking artifact with the substance still missing),
**P2** (framework parser — shared library, out of phase remit), **Q1**, **T1**, **T2**
(documentation/completeness notes).

---

## 5. Recommended Next Step

Ship the iteration; J-13's product capability is real, browser-proven, and now complete on legacy
rows as well as new ones. Two carries for the next lane that touches `/desk`:

1. **Re-record the `[NEW]` J-13 walkthrough against a fixture-scoped rig** (the same recipe UT-05
   used: temp-copy stores, scoped `TAPEOLOGY_*` env verified via `/proc/<pid>/environ`, a NEW screen
   for a date not already recorded under the same five pins) so the gallery narrates an in-band row,
   an out-of-band row, and a legacy row — and refresh the step 03/06/08 narration for the F1 string.
   Also fix the four brittle steps behind the `RECORDED_WITH_NOTES` verdict (step 07 expects
   `"SKIPPED"`; the DOM text is title-cased with CSS uppercase).
2. **Framework follow-up (P2):** teach `replay_lane_spec_journeys` to read a wrapped metadata line,
   and assert lane-side that every journey named in the spec appears in the merged results file — a
   spec reflow is a mitigation, not a fix.

Carried unchanged from iter-16: J-12's `evidence_makeup: true` one-page re-capture, to ride on
whichever lane next touches the Screen History section.

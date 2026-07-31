# goal-desk-iter-29 Audit Report

**Date:** 2026-07-31
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-18's product goal is genuinely achieved, and I verified it against the running system's own
artifacts rather than the handoffs: the ambient `.data/screen_runs` now holds three real run
records whose pins, `ranked_count` (100) and `skipped_by_reason` (`no_basis: 1`) are byte-identical
to the snapshot `screen-2026-07-31-c169546856c7` they name, and the duplicate-click short-circuit is
measurable in that same evidence — a full walk took `01:58:48.238068Z → 02:00:29.056457Z` (101/101
members, 1m41s) while the identical-pin retrigger took `02:01:55.486740Z → 02:01:55.500832Z` (0/101,
14ms, same `screen_id`). I found and fixed one IMPORTANT defect the reviewer had logged only as an
optional NOTE (a failing terminal ledger write was re-entered by the outer `except` and fabricated a
second, "failed" record for a run that had actually succeeded). The remaining gaps are evidence- and
asset-level, not product-level: TC-10's empty-state screenshot was lost to a browser-tool bug, TC-13's
frames are duplicates, the whole browser lane ran against the ambient store instead of the
fixture-scoped rig the spec's NOTES require, and this iteration's own J-18 golden replay script pins
its assertions to a mutable ambient snapshot id that a later real screen run will invalidate.

---

## 2. Definition-of-Done verification

Risk-class and contradiction-flagged items were traced through the code and the on-disk artifacts
myself; mechanical items already executed against the running system are accepted with citation.

| # | DoD item | How verified |
|---|----------|--------------|
| 1 | J-18 via browser-qa (TC-10/11/12), 1440x900, no h-scroll, T-9 rebuild | **Full trace.** `reports/phase-goal-desk-iter-29-ui-test-results.md` UT-01/02/03 PASS with real DOM values (`0 / 101 · reused screen-2026-07-31-c169546856c7 — no walk was performed`), no h-scroll (`scrollWidth === clientWidth === 1425`). Screenshots: I opened them — TC-11/TC-12 are legible in `UT-01/02/03-result.png` (all three are the **same** image, md5 `6489ed90…`), TC-10's empty state has **no** image (finding T3). T-9 rebuild is not recorded in any artifact; `apps/frontend/.next` was rebuilt at 02:45 and the new testids render live, so the build did include this iteration's code (finding T6). |
| 2 | Required-still-passing journeys green | Accepted with citation: `reports/phase-goal-desk-iter-29-regression-replay-results.md` — deterministic replay 10/10 PASS (J-03/04/05/06/07/09/10/12/16/17), each with its own `*-verify.png`. |
| 3 | No anti-goal violation | **Full trace** (risk class). SSOT: every pin resolved through its existing owner (`desk_screen_compute.py:155-161` → `screen_as_of`, `UniverseStore.list()[-1]["id"]`, `Config.config_fingerprint()`, `compute_bar_store_signature`), no second derivation; run record duplicates only *counts*, taken from the same `result` dict. Append-only/pinned: `ScreenRunStore` has exactly `{root, list, record}` (`test_desk_screen_log.py:197`), no update/delete path, new file per call. Explicit-operator-act: the new route is a pure read (`desk_routes.py:497-512`), mount is 7 GETs / 0 POSTs, no interval added outside the pre-existing running-job poll. Fingerprint: I ran `Config().config_fingerprint()` → `08e471b10130e1e2`. Read-only MCP: I ran `len(TOOL_NAMES)` → 17. Immutability of the ambient store: only 7 files under `apps/backend/.data` have today's mtime — the new snapshot, the 3 new run records and rebuildable caches; **no pre-existing artifact was rewritten**. |
| 4 | Unit tests pass, zero regressions, 3 named tests unmodified | **Re-verified independently.** Full suite after my fix: exit 0, **1500 passed / 8 skipped / 0 failed** (`pytest tests/ -q`, 1508 collected). `git diff tests/test_desk_screen_compute.py` shows only an import line plus an appended block — zero edits to any pre-existing test body or assertion. |
| 5 | Fingerprint / zero new Config fields / 17 MCP tools | Verified by my own interpreter run (above); `git diff` shows no `config.py` change at all. |
| 6 | `[NEW]`-flagged demo walkthrough over a populated ledger (TC-13) | **Full trace** (contradiction: the DoD requires distinct frame checksums, the artifact has duplicates). `reports/demo/goal-desk-iter-29/step-0{2,3,4}.png` share md5 `91ba8b67…`. I opened step-03: it *does* show the populated Screen Runs ledger (both the 101/101 row and the reused row). Substance captured, checksum clause failed — disclosed per the DoD's own escape clause (finding T4). |
| 7 | Dev handoff written | `docs/handoffs/goal-desk-iter-29-dev.md` present, plus a frontend handoff. |

---

## 3. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): a failing terminal ledger write was re-entered and fabricated a second, "failed" record**
`apps/backend/app/research/desk_screen_compute.py:273-283` (outer `except Exception`) sits around the
three terminal `_log(...)` calls. If `record_screen_run` itself raised while logging a `done` or
`cancelled` outcome (full disk, read-only log dir, permission change on the new `screen_runs` dir),
that write failure was caught by the outer handler and re-entered the writer with
`state="failed", error=<the ledger's own I/O error>` — a second, contradictory terminal record for a
run whose snapshot had in fact been recorded successfully, carrying a storage error as if it were a
screen failure. This directly violates the spec's "write ONE run record per run, EXACTLY ONCE at
terminal state" and corrupts the exact artifact this journey exists to make honest. The reviewer
logged it as a NOTE with an optional fix (`reports/reviews/goal-desk-iter-29-review.md:26-34`); I
rank it IMPORTANT because the fabricated record is durable, is served as truth by
`GET /research/desk/screen/runs`, and no test covered it.
*Fix applied:* a one-shot latch inside the `_log` closure (`desk_screen_compute.py:180-186`) — set
**before** the write, so a failed write leaves NO record (the module's own documented interrupted-run
honesty) and the I/O error still propagates verbatim, never swallowed. Evidence below in §5.

**B2 — GAP: `failed_member` names the first universe member when the walk raises *before* it starts**
`apps/backend/app/research/desk_screen_compute.py:277` — `failed_member = members[attempted] if
attempted < len(members) else None`. `attempted` is incremented by `compute_screen`'s per-member
progress callback (`desk_screen.py:513`), which fires *after* each member, so an exception raised on
member *i* correctly records `members[i]`. But `compute_screen` also does pre-loop work
(`get_desk_coverage`, `DatasetStore.list`, `_epoch(as_of)`, `desk_screen.py:437-451`); a raise there
leaves `attempted == 0` and the ledger names `members[0]` as "the member the walk was on when it
raised" — a member that was never touched. `null` would be the honest value. Not fixed: distinguishing
the two states needs a signal from `compute_screen`, and this iteration is explicitly barred from
changing that walk's semantics. Narrow (pre-walk raises are rare), documented here as a known limit.

**B3 — OBSERVATION: the five pins are now resolved twice per fresh run**
`desk_screen_compute.py:155-161` resolves the pins (including an index-only coverage read), then
`compute_screen` resolves its own again microseconds later (`desk_screen.py:437-451`). The values are
computed by the same functions over the same store, so they agree in practice; a store mutation
landing in that microsecond window (a concurrent top-up) would make the run record's pins disagree
with the snapshot's. The pre-existing `ScreenAlreadyRecorded` backstop still protects the snapshot
itself. No action recommended — the alternative (threading the pins into `compute_screen`) is exactly
the diff this iteration is forbidden to make.

### Frontend Findings

**F1 — GAP: a reused run's latest-detail block reads as an incomplete run**
`apps/frontend/app/desk/page.tsx:1332-1341`. For the reuse short-circuit the record honestly carries
`members_attempted: 0, ranked_count: 0, skipped_by_reason: {0,0}`, and the detail block therefore
renders (verified in `reports/demo/goal-desk-iter-29/step-03.png`):
`state: done · 0 of 101 members attempted · 0s elapsed · reused screen-… — no walk was performed ·`
**`101 members not reached`** *(amber)* and then `0 ranked · 0 skipped (no bars) · 0 skipped (no
basis)`. The amber "not reached" chip exists for cancelled/failed runs and reads as incompleteness
here, and the zero counts sit one line under a run that resolved to a 100-ranked snapshot. Every
value is literally true and the same line does say "no walk was performed", so this is a framing gap,
not a fabrication. A one-line guard (`unreached > 0 && !(run.state === "done" && run.reused)`, and the
same condition on the counts line) would remove the ambiguity — left unfixed as scope creep.

**F2 — OBSERVATION: sub-second runs render as "0s"** (`page.tsx:1240-1247`) — already disclosed in
the dev handoff; microsecond precision is preserved in the record. Cosmetic.

### Test / Evidence Findings

**T1 — IMPORTANT (unresolved, disclosed): the new J-18 golden replay script asserts on a mutable ambient snapshot id**
`runs/goal-session-desk/journey-scripts/J-18.json` steps 2-3 expect
`desk-screen-run-latest-outcome` to read `reused screen-2026-07-31-c169546856c7 — no walk was
performed` and `desk-screen-run-latest-counts` to read `0 ranked · 0 skipped (no bars) · 0 skipped
(no basis)`. Both assertions hold only while the ambient ledger's **latest** record is today's reused
run. The very next real screen run on a new date (a new `screen_date` is a guaranteed pin miss) makes
the latest record a fresh `reused: false` walk with a different id, and J-18's replay will report a
regression that is not one — and this iteration's own demo script *clicks Run Screen* (step 5 of
`reports/phase-goal-desk-iter-29-demo.json`, which is what wrote the 03:16 run record), so a
next-iteration demo run alone is likely to trip it. This is the era-5 lesson ("replay assertions must
target stable strings, not volatile async content") in a new costume. Recommended surgical fix: point
both `expect`s at `desk-screen-runs-table` and assert the *stable* substrings `no walk was performed`
and `101 / 101` — the ledger is append-only, so those rows never disappear. **Not applied:** the
:3301/:8301 rig is down (`curl` → connection refused), so I could not replay-verify an edited script,
and an unverified edit to a regression asset is worse than a disclosed finding.

**T2 — GAP: nothing proves the CLI still logs its runs**
`desk_screen_compute.py:468-470` (`main()`) constructs a `ScreenRunStore` and passes it, and the dev's
live CLI verification produced records — but `screen_run_store` is an *optional* kwarg (the disclosed
J-09/J-10 departure), and the two CLI tests (`tests/test_desk_screen_compute.py:707,727`) assert only
on the screen store. Deleting the CLI's `screen_run_store=` argument would fail no test, and CLI runs
would silently stop being recorded. One assertion (`ScreenRunStore(tmp_path/"screen_runs").list()` is
non-empty after `main()`) closes it. Left to the next iteration — the behavior is correct today.

**T3 — GAP: TC-10's empty-state screenshot does not exist, and three test rows cite one image**
`UT-01/UT-02/UT-03-result.png` are byte-identical (md5 `6489ed90…`) and all show the *populated*
state; the QA lane's own `TC-01-desk-page-loaded.png` / `TC-02-screen-runs-section.png` are 5.8 KB
solid-navy blanks (I opened them). The browser-QA report discloses the cause honestly (a screenshot
tool returning blank frames, fixed mid-run) and the empty state was verified by live DOM eval
(`emptyText` exact match, `tablePresent:false`) before the ledger was populated — but the journey's own
T-10 rule is "no screenshot ⇒ `unknown`". Reproducing it now requires the fixture-scoped rig the spec's
NOTES asked for from the start; the ambient ledger is append-only and can never be empty again.

**T4 — GAP: TC-13's frames are duplicates and the film ran against the ambient rig**
`step-02/03/04.png` share one md5, so the "distinct frame checksums" clause fails; the content is
right (populated ledger visible). `$FRONTEND_URL` pointed at the ambient `:3301` pair, not a
fixture-scoped rig, i.e. the iter-27/28 lesson the spec restated at length was not applied. The DoD
allows disclosure instead of blocking, which is what this is.

**T5 — OBSERVATION: the QA report's "real `.data/` untouched" claim is stale**
`reports/qa/goal-desk-iter-29-qa.md:105-112` states `.data/screen_runs` does not exist and the store is
unchanged. That was true when QA ran (02:53) and false 7 minutes later: the browser lane's real Run
Screen clicks appended `screen-2026-07-31-c169546856c7` (11 → 12 snapshots) and three run records, and
the demo lane appended a fourth act at 03:16. This is legitimate — a new run is a new snapshot, and I
confirmed no pre-existing file was rewritten (only 7 files carry today's mtime, all new or rebuildable
caches) — but no artifact says so, and TC-15's "11 screens unchanged" line now reads as contradicted.
I re-ran the full suite with a before/after `find .data -type f` listing: **zero** ambient changes from
the tests themselves, so the hermeticity claim itself holds.

**T6 — OBSERVATION: unrecorded T-9 rebuild and an imprecise test count in the dev handoff**
No artifact records the `rm -rf apps/frontend/.next` clean rebuild (`.next` mtime 02:45 and the new
testids rendering live are the only evidence the build was fresh). The dev handoff's "1,533
collected / ~1,525 passed" (`:119-121`) matches neither the reviewer's 1507 nor my 1508 — already
flagged by the reviewer; counts should be pasted from the run, not recalled.

---

## 4. Domain Assessment

The core domain move — resolving the five pins before the walk and answering an already-recorded pin
set from the store — is correct, and correct for the right reason: the pre-check uses the *same
accessors in the same order* that `compute_screen` uses internally (`screen_as_of`,
`universe_records[-1]["id"]`, `config_fingerprint()`, `_bar_store_signature` over the coverage
payload), and `find_by_key` requires an exact five-tuple match, so a false hit is not reachable by
construction — a mismatch degrades to a full walk plus the pre-existing `ScreenAlreadyRecorded`
backstop, never to a wrong snapshot. TC-3's zero-`compute_tradability` assertion is a real
call-counting wrapper around the real function, not a mock, and the live 1m41s → 14ms delta on 101
real members confirms it end to end.

The ledger module mirrors its two siblings faithfully: whole-record SHA-256 verified on every read,
`record()` the only mutation, integrity failures surfaced as explicit `integrity_errors` rows rather
than silence, no content-keyed dedup (correct — two identical reused runs are two real events), and
the storage dir resolved from a bare env var or a sibling of the universe dir, so the fingerprint pin
genuinely could not move. The interrupted-run honesty is structural, not policed: `record()` is the
only write path and it is called once, at the end — and after my B1 fix, that "once" is now enforced
by a latch rather than by the absence of a second call site.

The one place the design leaves rope is the optional `screen_run_store` kwarg. The reasoning is
disclosed and defensible (making it required would have forced edits to the three protected tests),
and both production callers supply a real store — I grepped: there is no third caller. But "optional +
untested on the CLI path" (T2) is the shape silent regressions grow in, and it is worth closing.

---

## 5. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/app/research/desk_screen_compute.py:180-186` | One-shot `logged` latch inside `_log`, set before the write, so a raising terminal ledger write can never be re-entered by the outer `except` and re-recorded as a fabricated second "failed" run; the I/O error still propagates verbatim. |
| 2 | Important (test) | `apps/backend/tests/test_desk_screen_compute.py` (appended) | `test_a_terminal_log_write_that_raises_is_never_re_logged_as_a_second_failed_record` — monkeypatches `record_screen_run` to raise `OSError`, asserts exactly ONE write attempt, an empty ledger (no fabricated entry), the error propagating, and the screen snapshot still recorded. |

**Post-fix verification (commands and results):**

- `pytest tests/test_desk_screen_compute.py::test_a_terminal_log_write_that_raises_is_never_re_logged_as_a_second_failed_record -q` → **passed**.
- Counter-test (a lint that cannot fail proves nothing): I temporarily reverted the latch and re-ran
  the same test → **failed** with `AssertionError: a failed terminal write must never be re-entered as
  a second record` (the pre-fix code attempted 2 writes). The latch was restored and the test re-run
  → **passed**.
- Full suite, after the fix: `pytest tests/ -q` → **exit 0, 1500 passed / 8 skipped / 0 failed**
  (1508 collected).
- `Config().config_fingerprint()` → `08e471b10130e1e2`; `len(TOOL_NAMES)` → `17`.
- Hermeticity: `find apps/backend/.data -type f -printf '%p %s\n'` before and after the full suite →
  **identical** (no ambient store writes from the tests).
- Diff review: my change is 5 added lines in the `_log` closure (comment + latch) plus the appended
  test — no other behavior touched, nothing else in the file or the frontend modified.

---

## 6. Recommended Next Step

Proceed. J-18's product capability is real, live-verified on 101 real members, and now structurally
exactly-once. Before or during the next iteration, in priority order:

1. **T1 (do this first)** — repoint `runs/goal-session-desk/journey-scripts/J-18.json` steps 2-3 at
   `desk-screen-runs-table` with the stable substrings `no walk was performed` / `101 / 101`, and
   replay-verify with the rig up. Left as-is, J-18 will report a false regression the next time any
   lane triggers a screen run on a new date.
2. **T2** — one assertion that a CLI `main()` run leaves a durable record, closing the optional-kwarg
   rope.
3. **F1** — suppress the amber "N members not reached" chip and the zero counts line for a
   `done + reused` run.
4. **T3/T4** — if the evaluator wants TC-10/TC-13 as `passing` rather than `unknown`, they need the
   fixture-scoped rig the spec's NOTES specified (scoped `TAPEOLOGY_DESK_UNIVERSE_DIR` +
   `TAPEOLOGY_DESK_SCREEN_LOG_DIR`, `$FRONTEND_URL` pointed at it, torn down only after the demo
   step). On the ambient store the empty state is gone for good.
5. **T5** — future demo scripts should stay read-only over the ambient store, the way the browser-QA
   agent deliberately authored `J-18.json`; a demo step that clicks Run Screen on a pin-miss day would
   kick off a ~1m40s 101-member walk and write a real snapshot to the owner's store.

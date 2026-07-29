# goal-desk-iter-16 Audit Report

**Date:** 2026-07-29
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-12's product change is real, correctly implemented and now genuinely evidenced: `?id=` serves any
individually-recorded snapshot byte-identically (traced through `desk_routes.py:330-362` and
`ScreenStore.list`, re-verified live against the real `.data/screen` pair), both run ledgers now
disclose their store's own `integrity_errors`, and `/desk` addresses, highlights and names each
recording by its own id. The audit found the CODE sound but the EVIDENCE lane defective in exactly
the way this iteration's own `full`-depth trigger existed to catch: the demo-narrator walkthrough
navigated off `/desk` at step 4 and captured four frames of a different page under `/desk` captions
(`Demo Verdict: RECORDED_WITH_NOTES`, not the DoD's `RECORDED`), the three integrity-error browser
tests were skipped so goal.md's "no screenshot ⇒ `unknown`, never `passing`" clause was unmet, and
one P1 evidence screenshot was a capture of an unrelated application. All three were fixed during
this audit with live re-capture; the remaining items are documented gaps, none of which touch stored
data or the phase goal.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (gap): `?id=` lookup indexes `r["id"]` where the store's own sort uses `.get`**
`apps/backend/app/research/desk_routes.py:354` — `found = next((r for r in records if r["id"] == id), None)`.
`ScreenStore.list()` sorts defensively (`meta.get("id", "")`, `desk_screen.py:478`), so a
checksum-valid record file with no `id` key would 500 here rather than return the honest `null` this
route promises. Not realistic (the whole-record checksum at `desk_screen.py:447` covers the record,
and `record()` always writes `id`), and it matches the existing `find_by_key` convention
(`desk_screen.py:491-494`, `record["screen_date"]` etc.). Left unchanged — fixing it would be scope
creep and would diverge from the sibling lookup's own style.

**No other backend finding.** The traced-in-full items:
- `?id=`/`?date=`/refusal branch (`desk_routes.py:330-362`): the 422 refusal is evaluated BEFORE
  `store.list()`, so an `id`+`date` request cannot even read the store; `?date=` still returns
  `matching[-1]` byte-unchanged; unknown id returns `{"screen": null}` at HTTP 200. Independently
  re-verified live this audit against the real ambient store on a scoped backend:
  `?id=screen-2026-07-27-936543601e75` → that exact record (63 rows, `created_utc`
  `2026-07-27T21:42:14.636275Z`), `?date=2026-07-27` → `screen-2026-07-27-3ad3c57aa6ba`.
- The read writes nothing and recomputes nothing — no store call other than `list()`, and a
  before/after SHA-256 listing of every real universe/screen/reconcile-run file (9 files) taken
  around this audit's own live rig came back identical.
- `integrity_errors` on both ledgers (`desk_routes.py:296`, `:542`) is the store's own `errors`
  tuple element, verbatim, in the identical `{file, error}` shape `get_screen`/`get_universe` use
  (`:181`, `:362`). Corrupt records stay excluded from `runs`/`latest` — confirmed live: a planted
  corrupt file appeared in `integrity_errors` while the two genuine reconcile runs still served.

### Frontend Findings

**F1 — GAP (documented, not fixed): the phase spec's "four ledger sections (Universe, …)" premise is
factually wrong; only three exist**
`docs/phases/goal-desk-iter-16.md:90-92` and `runs/goal-desk-iter-16/plan.md:55-60` both assert that
`/desk` has a Universe ledger section receiving `integrity_errors` and cite `lib/types.ts:363/516/873`
for a `DeskUniverseResult` type. Verified independently: no `DeskUniverseResult` exists in
`apps/frontend/lib/types.ts`, no `fetchDeskUniverse*` in `lib/api.ts`, and the browser lane's own
full-page text dump (UT-14) found "Universe snapshot" exactly once, inside Provenance. Crucially the
JOURNEY contract does not require it — `docs/goal.md`'s J-12 step 5 says the two run-ledger GETs must
serve `integrity_errors` "exactly as `GET …/screen` and `GET …/universe` already do" and its
Acceptance asks for "one screenshot of the honest integrity-error line for the planted corrupt **run**
record". The dev's refusal to invent an untested UI section was the correct call; the defect is in the
decomposer's spec text, which should be corrected rather than built to. The reviewer's NOTE about
`lib/types.ts:955/1022` comments naming a non-existent `DeskUniverseResult` is the same root cause
(comment-only, no behavior).

**F2 — GAP (not fixed, pre-existing architecture): an all-corrupt screen store hides its own
integrity note**
`apps/frontend/app/desk/page.tsx:1693` + the `latest === null` empty-state discriminator (~:1739):
if EVERY screen record fails verification, `latest` is `null`, the whole populated view — including
Screen History and its `IntegrityErrorsNote` — is replaced by the pre-existing "Desk screen not
computed yet." panel, so the screen ledger's integrity errors would be invisible exactly when the
ledger is most broken. The dev flagged this honestly. It is a property of the empty-state
discriminator that predates this iteration, no TC covers it, and restructuring it is out of scope.
Worth a future journey; not a blocker (Top-up Runs and Index Reconciliation render unconditionally
and were verified live this audit).

**F3 — OBSERVATION: two of the three integrity notes read the field without a defensive default**
`page.tsx:745` and `:928` pass `result.data.integrity_errors` straight into `IntegrityErrorsNote`,
whose first statement is `errors.length === 0` (`:712`). The screen path is defensive
(`?? []`, `:1693`). Both backends always send the key now, and the TS types require it, so this is
style-only — but a stale/proxied response missing the key would throw inside render rather than
degrade. Not fixed (scope).

### Test / Evidence Findings

**T1 — IMPORTANT (fixed): the `[NEW]` demo-narrator walkthrough captured four frames of the wrong
page under `/desk` captions, and its verdict was not the DoD's `RECORDED`**
The delivered `reports/phase-goal-desk-iter-16-demo.json` step 4 clicked `{"role":"link","name":"NFLX"}`
— a ranked row's stretched drill-in anchor (`className="absolute inset-0"`, `page.tsx:300-306`) —
which navigates to `/structure`. Steps 5-8 then timed out (`Locator.wait_for: Timeout 8000ms`) and
the runner captured the page anyway: `step-05/06/07/08.png` were four byte-identical screenshots of
`/structure` while their captions described selecting the later same-date recording, the Provenance
panel updating, the Latest button and the ledger sections. Step 2 additionally used a non-existent
selector (`[data-testid='screen-history-table']`; the real one is `desk-history-table`,
`page.tsx:546`). Net effect: of the four beats TC-16 requires, only "open the history list / select
the earlier entry" was actually recorded, and `reports/phase-goal-desk-iter-16-demo-results.md` read
`Demo Verdict: RECORDED_WITH_NOTES` where the DoD requires `RECORDED`.
**Fix applied.** Rewrote the demo JSON as 7 steps, every action either a `goto` or a click on a
non-navigating element, and re-ran the deterministic runner in `record` mode.
**Verification:** `demo_runner.py --mode lint` clean; `--mode record --base-url http://localhost:3301`
→ `recorded 7 step(s) … (verdict: RECORDED)`, zero soft notes; `Demo Verdict: RECORDED` in the
regenerated results; all 7 `[NEW]`-flagged; all seven PNGs opened and checked against their own
captions (step-01 default view + "most recently recorded" note; step-02 history table with both
`2026-07-27` rows and distinct recorded-at values; step-03 Provenance =
`screen-2026-07-27-936543601e75` / `2026-07-27T21:42:14.636275Z`; step-04 highlight moved to the
sibling row; step-05 Provenance = `screen-2026-07-27-3ad3c57aa6ba` / `2026-07-28T21:30:16.111871Z`
with Screen date still `2026-07-27`; step-06 banner gone, note back; step-07 both amber
integrity-error lines).

**T2 — IMPORTANT (fixed): the integrity-error line had never been observed on screen, which
goal.md's own acceptance scores as `unknown`, not `passing`**
`reports/phase-goal-desk-iter-16-ui-test-results.md` records UT-11/UT-12/UT-13 as SKIPPED
("prerequisite scoped rig not provided"), and `docs/goal.md`'s J-12 Acceptance requires "one
screenshot of the honest integrity-error line for the planted corrupt run record (T-10: no
screenshot ⇒ `unknown`, never `passing`)". The QA report nevertheless recorded TC-13 as PASS on the
strength of a source grep (see T4). So the single new *disclosure* half of J-12 shipped visually
unverified.
**Fix applied (evidence, not code).** Stood up a scoped rig exactly per goal.md's step-6 discipline —
`TAPEOLOGY_DESK_TOPUP_LOG_DIR` / `TAPEOLOGY_DESK_INDEX_RECONCILE_DIR` pointed at copies under this
run's `TMPDIR`, each carrying one planted corrupt record, **never** `apps/backend/.data` — with the
real screen/universe stores mounted read-only.
**Verification:** live DOM read on `http://localhost:3301/desk` returned
`desk-topup-runs-integrity-errors` = "1 file failed an integrity check and is excluded:
topup-2026-07-28-audit0corrupt.json" and `desk-reconcile-runs-integrity-errors` = the equivalent line
for `reconcile-2026-07-28-audit0corrupt.json`, with the two genuine reconcile runs still listed and
the corrupt one absent. Screenshotted (demo `step-07.png`, copied to
`reports/qa/goal-desk-iter-16-evidence/AUDIT-UT-12-13-ledger-integrity-errors.png`). A SHA-256 listing
of all 9 real universe/screen/reconcile-run files taken before and after the rig run is identical —
the audit wrote nothing to `apps/backend/.data`, and no `topup_runs` directory was created there.
UT-11 (the Screen History note) remains unobserved — see G3 below.

**T3 — IMPORTANT (fixed): the UT-02 evidence screenshot is a capture of an unrelated application**
`reports/qa/goal-desk-iter-16-evidence/UT-02-result.png` — the cited evidence for the P1 test
"Earlier same-date entry opens its own recording", J-12's single most load-bearing visual claim — is
a full-page screenshot of a different product ("Trendora — Research — Factor Lab", the `localhost:3255`
app the browser-QA report's own Environment note mentions while asserting "no impact on results").
That assertion is false for this artifact. This is precisely the iter-13 lesson this iteration's
NOTES restate: a screenshot's bytes prove the state, not which lane captured it.
I checked every other evidence PNG: UT-03, UT-04/05/06/07/10 (one shared capture), UT-01, UT-08,
UT-09, UT-14 are all genuine `/desk` captures, so the contamination is limited to this one file.
The underlying UT-02 CLAIM is independently corroborated — its reported DOM values match the real
store exactly, and this audit's demo `step-03.png` now shows the earlier recording's own Provenance
on screen.
**Fix applied (evidence):** added `AUDIT-UT-02-earlier-same-date-recording.png` and
`AUDIT-UT-03-later-same-date-recording.png` to the evidence directory (the audit's own verified
captures) and deleted a blank deep-scroll capture the audit itself produced before switching to the
Playwright runner. `UT-02-result.png` is left in place, named here as invalid rather than silently
overwritten.

**T4 — IMPORTANT (record corrected, report not edited): the QA report marks five browser test cases
PASS on source-grep evidence**
`reports/qa/goal-desk-iter-16-qa.md:155-186` records TC-09…TC-13 as "✓ PASS" with the actual basis
stated inline as "source & build verification", "routing layer verified; real browser testing
deferred", "component present and wired". A browser-type test case cannot pass on a grep. The
separately-dispatched browser-qa lane did execute TC-09/10/11/12 equivalents for real (UT-02..UT-09,
with DOM `eval()` proof) so the conclusions happen to hold, but TC-13's PASS was unsupported until
this audit executed it (T2). I did not rewrite the QA report; downstream lanes should read the
audit's evidence for the TC-13 row.

**T5 — OBSERVATION: six regression journeys share one evidence screenshot**
`J-03/J-04/J-08/J-09/J-10/J-11-verify.png` are byte-identical (md5 `88b5e0aa…`). The replay lane's
PASS rests on its expects, not the frame, and all eight replayed green
(`reports/phase-goal-desk-iter-16-regression-replay-results.md`), so this is a weak-evidence note,
not a failure.

**T6 — Test quality: good.** The new backend tests assert exact values, not shapes: TC-1 compares the
response body to the on-disk `record["meta"]` (`test_desk_screen.py`, `?id=` byte-identity), TC-2
asserts `?date=` still resolves the LATER id AND `!=` the earlier one, TC-15 hashes 5 planted files
before/after nine GETs, and both ledger tests assert the exact filename plus the "corrupted or
tampered" text with the record absent from `runs`/`latest`. One soft spot: the TC-5 exact-equality
dict embeds `body["integrity_errors"][0]["error"]` in its own expectation (self-referential for the
message), immediately mitigated by the following substring assertion. The `?id=` fixture plants its
pair through the real `ScreenStore.record()` rather than hand-writing files, so the byte-identity
claim is genuine. All scoped under `tmp_path` — I confirmed no test writes to `apps/backend/.data`.

---

## 3. Domain Assessment

The domain logic is honest and minimal. The core insight this journey rests on — that a screen's
5-pin key admits two records under one `screen_date`, so `matching[-1]` structurally cannot address
the earlier one — is correctly resolved by adding an identity lookup rather than by changing what
`?date=` means or by re-keying the store. `ScreenStore` remains the only owner, `GET
/research/desk/screen` the only serving endpoint, and the `?id=` branch performs one `list()` and a
linear scan: zero recompute, zero write, no second path to the same value. The refusal on
`id`+`date` (422, before any store read) is the right shape — a silent precedence rule would have
been the seductive alternative and would have made two different requests indistinguishable.

The disclosure half is even simpler and is the more interesting honesty move: two routes were
unpacking `records, _errors = store.list()` and dropping the error channel their own siblings
already published. The fix publishes the store's tuple verbatim — no new value, no new severity
vocabulary, no repair path. A corrupt file is named and excluded, never fixed or deleted, which
matches the era's immutability anti-goal exactly. `latest` is correctly `created_utc`-sorted
`records[-1]`, and the new Provenance copy stops implying that is "the latest screen date" —
verified on screen, and the divergence is real in the ambient store (displayed snapshot is dated
`2026-07-28` while a `2026-07-29`-dated recording exists).

Anti-goal check: single source of truth holds (no value computed twice, no new endpoint/owner);
snapshots stayed append-only and byte-identical (test TC-15 plus my own 9-file SHA-256 comparison
around a live rig); every run stays an explicit operator act (this iteration adds only GETs; the
new read triggers no compute); the briefing stays descriptive (`test_copy_discipline.py` green,
unmodified, and the new note reads as measurement, not advice).

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `reports/phase-goal-desk-iter-16-demo.json` | Rewrote the walkthrough: removed the step-4 click on the ranked row's stretched `/structure` drill-in link (root cause of four wrong-page frames), replaced the invalid `screen-history-table` selector and the two other non-resolving click targets, and re-cut the arc to 7 steps that each act on a non-navigating element. Captions now describe only what their own frame shows. |
| 2 | Important | `reports/phase-goal-desk-iter-16-demo-results.md`, `-demo-script.md`, `reports/demo/goal-desk-iter-16/step-0{1..7}.png` | Regenerated by re-running `demo_runner.py --mode record` against a live rig: `Demo Verdict: RECORDED` (was `RECORDED_WITH_NOTES`), 7/7 steps `[NEW]`-flagged, zero soft notes, seven distinct frames each verified against its caption. |
| 3 | Important | `reports/qa/goal-desk-iter-16-evidence/AUDIT-UT-12-13-ledger-integrity-errors.png` (+ `AUDIT-UT-02-…`, `AUDIT-UT-03-…`) | Executed the skipped UT-12/UT-13 (TC-13) live on a scoped rig with planted corrupt records and captured the on-screen integrity-error lines; added verified replacements for the contaminated UT-02 evidence. Removed one blank deep-scroll capture the audit itself produced. |

No source file was modified by this audit — `git status` over `apps/backend` and `apps/frontend`
shows only the iteration's own eight changed files.

**Audit-run verification commands and results**
- `cd apps/backend && .venv/bin/python -m pytest tests/ -q -p no:randomly` → exit 0 (independent
  full-suite re-run; this environment clips the trailing summary line, as the dev handoff notes).
- `python -c "from app.config import Config; print(Config().config_fingerprint())"` → `08e471b10130e1e2`.
- `git diff --stat HEAD --` over `tradability.py`, `levels.py`, `bars.py`, `bar_index.py`,
  `StructureChart.tsx`, `desk_coverage.py`, `test_copy_discipline.py` → empty.
- Live: `GET /research/desk/screen?id=…` byte-match, `?date=` unchanged, `?id=&date=` → 422,
  unknown id → `{"screen": null}` 200, both ledger GETs carrying `integrity_errors`.
- SHA-256 of all 9 real universe/screen/reconcile-run files: identical before and after the audit rig.
- Rig torn down afterwards (ports 8301/3301 closed; the unrelated `:3255` app left untouched).

---

## 5. Recommended Next Step

Proceed. J-12 is genuinely delivered and now genuinely evidenced: `Demo Verdict: RECORDED` with a
seven-frame `[NEW]` gallery covering the full same-date arc plus the ledger disclosure, and the
integrity-error line observed on screen with the corrupt file named. Three documented gaps carry
forward, none blocking:

1. **Correct the spec text, do not build the section (F1).** `docs/phases/goal-desk-iter-16.md:90-92`
   and the plan claim a `/desk` Universe ledger section that has never existed; `docs/goal.md`'s
   J-12 never asked for one. The decomposer should stop citing `DeskUniverseResult`/`lib/types.ts:363`
   in future specs, and a Universe ledger section on `/desk` should be a deliberate future journey if
   it is wanted at all — not retrofitted under this iteration's name.
2. **UT-11 (Screen History integrity note) remains unobserved (G3).** The same `IntegrityErrorsNote`
   component was verified live in two of its three mount points this audit; the third needs a scoped
   `TAPEOLOGY_DESK_SCREEN_DIR` rig, and F2 means the all-corrupt case would not render at all. Worth
   one small journey covering "the screen ledger can name its own damaged file even when nothing
   loads".
3. **Evidence-lane hygiene (T3/T4).** Two process defects surfaced here would have gone unnoticed at
   `lean` depth: a browser lane sharing a Chrome instance with an unrelated app produced one
   wrong-app evidence file while its own report declared "no impact", and the QA lane marked
   browser-type test cases PASS on source greps. Both are worth a framework lesson — the demo
   runner in particular should treat a step whose click navigates away from the expected origin as a
   hard note, since the resulting gallery is actively misleading rather than merely incomplete.

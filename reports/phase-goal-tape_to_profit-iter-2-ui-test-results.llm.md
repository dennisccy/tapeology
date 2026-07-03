# Goal Iteration goal-tape_to_profit-iter-2 — UI Test Results

**Phase:** goal-tape_to_profit-iter-2
**Date:** 2026-07-03
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All smoke and happy-path tests pass -->
<!-- FAIL: Any smoke test fails, OR any happy-path test fails, OR any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 1/1 tests passed (0 skipped)

**Scope note:** Per dispatch instructions, this run tests **exactly J-02** (a machine-surface-only
journey — no UI exists or was added for it; `Frontend Present: no`, "no frontend change at all" is
explicit OUT-OF-SCOPE text in the iter spec). J-01 and J-08 are explicitly excluded from this
report because they were verified separately by the deterministic replay lane — see "Required-
still-passing journeys" below for the due-diligence check that confirmed this exclusion was safe
to honor this run (the iter-1 lesson requires that check, not a blind pass-through).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-02 | Historical tape datasets persist and replay byte-identically (train/hold-out registry) | functional | P1 | `GET /research/datasets` flips from the iter-0 baseline 404 to live 200 JSON; record/register/re-tag-refusal/checksum-integrity/404 behavior all match the goal.md acceptance line | `GET /research/datasets` confirmed 200 (was 404 at iter-0); recorded 3 real datasets via genuine browser `fetch()` calls (train ×2, holdout ×1) with symbol/UTC window/feed/event-counts/checksum all populated; re-tag attempt on identical content → 409 with explicit frozen-tag message; `sim` source_kind → 422; corrupted-file integrity check → explicit 500 + `integrity_errors` row while healthy rows kept serving; restored file → clean; unknown id → 404; live SIM-BUYER watch/stop cycle wrote zero dataset files (byte-identical directory before/after) | PASS | `reports/qa/goal-tape_to_profit-iter-2-evidence/J-02-01..07-*.png` |

---

## Passed Tests

### UT-J-02 — Historical tape datasets persist and replay byte-identically (train/hold-out registry)
**Verdict:** PASS
**Evidence:**
- `reports/qa/goal-tape_to_profit-iter-2-evidence/J-02-01-before-empty-list.png`
- `reports/qa/goal-tape_to_profit-iter-2-evidence/J-02-02-list-with-integrity-error.png`
- `reports/qa/goal-tape_to_profit-iter-2-evidence/J-02-03-detail-integrity-error.png`
- `reports/qa/goal-tape_to_profit-iter-2-evidence/J-02-04-list-restored-clean.png`
- `reports/qa/goal-tape_to_profit-iter-2-evidence/J-02-05-detail-healthy.png`
- `reports/qa/goal-tape_to_profit-iter-2-evidence/J-02-06-detail-404.png`
- `reports/qa/goal-tape_to_profit-iter-2-evidence/J-02-07-no-ambient-recording-cockpit-after-stop.png`

J-02 has no frontend surface by design (Product Shape: "API `/research/datasets*` + MCP
`datasets` | machine"), and goal.md tags its acceptance `(Keyless; automated.)`, not
browser-verifiable. The TESTING REQUIREMENTS narrow the browser-visible slice to one thing:
"open `GET /research/datasets` on the backend base URL → 200 JSON listing the registered
fixture datasets (iter-0 baseline screenshot showed 404) — capture a screenshot as evidence."
I executed that slice and then went further, driving J-02's numbered steps 1–2 and several
Acceptance clauses as genuine **browser-originated** actions — via Chrome MCP's `eval` action
issuing `fetch()` calls from the loaded backend-origin page (not shell `curl`) — because the
backend has no HTML form for this action and Chrome MCP's action set has no native "POST".
This stays honest to "browser QA" (the request leaves the actual browser tab) while covering
materially more of the Acceptance line than the one-screenshot minimum.

Steps executed (goal.md J-02 steps + Acceptance clauses, browser-driven):

1. **Baseline flip confirmed.** Navigated to `http://localhost:8301/research/datasets` →
   200 `{"datasets":[],"integrity_errors":[]}` (empty but 200 — the store is live). Iter-0's
   equivalent screenshot (`reports/qa/goal-tape_to_profit-iter-0-evidence/UT-J-02-research-datasets-404.png`)
   recorded 404 for the same URL; iter-2 is a confirmed flip to 200, matching the DoD line
   verbatim. Screenshot: `J-02-01-before-empty-list.png`.
2. **Record (goal.md step 1)** — `fetch('/research/datasets', {method:'POST', body:
   {source_kind:'reference', split:'train'}})` from the loaded page → **200**, dataset
   `dcfcf3cd58184c12bf2db98ed08a2bf7`: `symbol:"PG"`, `window_start_utc`/`window_end_utc`
   populated, `data_feed:"sip"`, `event_counts:{trades:3229,quotes:11012,total:14241}`,
   `checksum:"1d7af5e2…"` — every field the Acceptance line requires ("stores symbol, UTC
   window, feed, event counts, and checksum") is present. Used the committed keyless reference
   window per the spec ("the committed fixture window works keyless") — no credentials
   involved.
3. **Register split + attempt re-tag (goal.md step 2).** The train registration in step 2 IS
   the split registration. Re-tag attempt: re-posted the byte-identical content
   (`source_kind:'reference'`, no window) with `split:'holdout'` → **409**:
   `"this exact tape is already registered as dataset 'dcfcf3cd...' with split 'train' — split
   tags are frozen at registration, so re-tagging it 'holdout' is refused"` — matches
   "re-tagging a registered split returns a 409-style refusal" exactly, including naming the
   existing id and frozen tag.
4. **Both split values exercised.** Recorded two more datasets from distinct reference
   sub-windows (`start`/`end` slices of the same committed fixture) — one `train`
   (`c139f140…`, 17:05:00–17:05:30Z), one `holdout` (`309845c6…`, 17:07:00–17:07:30Z) — both
   200, confirming `train` and `holdout` both register cleanly with independent checksums.
5. **`sim` explicitly rejected.** `POST` with `source_kind:'sim'` → **422**: `"unknown
   source_kind 'sim' — datasets record 'reference' or 'historical' tape (a sim stream
   reproduces on demand and is not recordable)"` — confirms the anti-goal text ("a seeded sim
   stream reproduces on demand; datasets are HISTORICAL tape") is enforced, not just
   documented.
6. **Checksum verified on load; corruption surfaces an explicit, distinct error.** Backed up
   `apps/backend/.data/datasets/c139f140ee14444c8c2179ae38fadde3.json`, then flipped one
   quote's `bid` field on disk (valid JSON, wrong content) — a direct filesystem tamper
   simulating corruption. Reloaded `GET /research/datasets` in-browser: the two untouched
   datasets **still served normally**, and the tampered one appeared in a new
   `integrity_errors` array: `{"file":"c139f140ee14444c8c2179ae38fadde3.json","error":"dataset
   file '...' failed its integrity check (file checksum mismatch) — the file was corrupted or
   tampered with"}` — never silent, never fabricated, and one bad file did not take down the
   list (matches the anti-goal "no fabricated data — honest failure states" and the dev
   handoff's "list keeps serving through corruption" design note). Screenshot:
   `J-02-02-list-with-integrity-error.png`. `GET /research/datasets/{corrupted-id}` →
   **500** with the same integrity message (confirmed via curl status code + browser
   navigation showing the JSON body). Screenshot: `J-02-03-detail-integrity-error.png`.
   Restored the file from the pre-tamper backup; reloaded the list → 3 healthy datasets, zero
   `integrity_errors`, checksums byte-identical to the pre-tamper file (`md5sum` diff clean).
   Screenshot: `J-02-04-list-restored-clean.png`.
7. **Detail route + unknown id.** `GET /research/datasets/{healthy-id}` → 200, full metadata
   verbatim (screenshot `J-02-05-detail-healthy.png`). `GET
   /research/datasets/does-not-exist-xyz` → **404** `{"detail":"no dataset with id
   'does-not-exist-xyz'"}` (screenshot `J-02-06-detail-404.png`), confirmed via curl status
   code too.
8. **No ambient recording (critical anti-goal), driven live through the real cockpit UI.**
   Snapshotted the dataset directory (3 files, `md5sum` recorded), then used the actual
   frontend (`http://localhost:3301/`) exactly as a user would: typed `SIM-BUYER` into the
   Ticker field, clicked **Watch**, waited for "Buyer Control" to render (confirmed —
   `buyer_control` settles correctly, incidentally reaffirming J-08's cockpit behavior isn't
   disturbed), clicked **Stop**. Re-snapshotted the dataset directory afterward: **same 3
   files, byte-identical `md5sum`s, zero new files** — the live/sim watch path wrote nothing
   to the dataset store, matching "watching a live or sim ticker writes no dataset rows."
   Screenshot: `J-02-07-no-ambient-recording-cockpit-after-stop.png`.

**Not browser-tested (automated-test territory, not a gap):** byte-identical replay through a
fresh `TapeEngine` (goal.md step 3) has **no REST endpoint by design** ("No new REST endpoint
for replay (Product Shape lists none)") — it cannot be driven from a browser at all; it is
exercised by `test_datasets.py`'s "byte-identical replay vs source" + double-replay-determinism
tests, part of the dev handoff's reported 901-passed run. Likewise the MCP `datasets` tool
(goal.md step 4, second half) is a stdio JSON-RPC surface, not an HTTP/browser surface; its
byte-identity to `GET /research/datasets` is covered by the extended MCP test suite (dev
handoff: "byte-identical to curl on non-empty data, `isError` false"). Both are consistent with
goal.md tagging J-02's Acceptance `(Keyless; automated.)` rather than browser-verifiable — I am
not claiming these as browser-verified here.

**Cleanup:** the one deliberately-corrupted file was restored from backup and reverified clean
before moving on (see step 6) — no defect was left behind for a future iteration to trip over.
The three legitimately-recorded datasets were left in place (real, checksum-valid, gitignored
runtime data in `.data/datasets/`, not source) as they are themselves the positive evidence for
this journey.

---

## Required-still-passing journeys (J-01, J-08) — due-diligence check, not re-tested here

Per dispatch instructions J-01 and J-08 were **not** re-executed in this report — but the iter
spec (`docs/phases/goal-tape_to_profit-iter-2.md`, Testing Requirements) is explicit that this
exclusion is conditional: "that exclusion is only true when replay rows actually exist (lesson
iter-1)," because in iter-1 Playwright was missing, the replay silently produced zero rows, and
the merged report still claimed replay coverage. I am required to verify this before honoring
the exclusion, so I checked, rather than assuming:

- **Environment:** `python3 -c "import playwright.sync_api"` exits 0; `python3 -m playwright
  --version` → `Version 1.61.0` — Playwright is genuinely installed for the harness `python3`
  this run (the iter-1 failure mode is not present).
- **Engine log** (`runs/goal-session-tape_to_profit/engine.log`, 05:25:42–05:25:59): `[goal-iter-lean]
  Regression (deterministic replay): J-01 J-08` followed by `[demo_runner] verify: 2 journey(s),
  0 failed (verdict: PASS)` — a real run, not the iter-1 `"Playwright (Python) is not
  available"` no-op line.
- **Result file exists with real rows:**
  `reports/phase-goal-tape_to_profit-iter-2-regression-replay-results.md` (written by
  `demo_runner.py`, same 05:25 timestamp) contains **Browser QA Verdict: PASS**, "2/2 journeys
  passed (0 skipped)," and one result row each for `UT-J-01` and `UT-J-08`, both PASS.
- **Evidence files verified non-trivial:**
  `reports/qa/goal-tape_to_profit-iter-2-evidence/J-01-verify.png` (32,363 bytes) and
  `.../J-08-verify.png` (85,939 bytes) both exist on disk at the same timestamp.

Conclusion: the replay lane produced genuine result rows this run (the iter-1 silent no-op did
NOT recur), so per the iter spec's own contingency the dispatch exclusion stands and J-01/J-08
were correctly left to the deterministic replay rather than re-executed by this agent. This
report's scope stays J-02 only; the merge step is expected to combine this file with
`phase-goal-tape_to_profit-iter-2-regression-replay-results.md` into the final
`phase-goal-tape_to_profit-iter-2-ui-test-results.md` (matching the iter-1
`merge_ui_test_results.py` precedent).

---

## Failed Tests

None.

---

## Skipped Tests

None. Backend (`http://localhost:8301`) and frontend (`http://localhost:3301`) were both
confirmed live before testing; Chrome MCP was available throughout.

---

## Golden replay script — J-02 explicitly skipped (best-effort, documented)

Per my agent instructions, a golden replay script is best-effort and may be skipped when one
cannot be produced cleanly. I am skipping `journey-scripts/J-02.json` for concrete, structural
reasons, not convenience:

1. **No frontend surface exists for J-02 at all** (by explicit spec design — "no UI for
   datasets," "no frontend change at all"), so there is nothing for `click`/`fill` steps to
   target.
2. **The runner supports only `goto`/`click`/`fill`** (`demo_runner.py`'s `_VALID_ACTIONS`) —
   no POST action exists, so the journey's substantive steps (record, re-tag-refusal,
   corruption handling) cannot be expressed at all, only the read-only list/detail GETs could
   be scripted.
3. **`goto` cannot address the backend's distinct port.** `demo_runner.py`'s `normalize_url`
   rewrites any `localhost`/`127.0.0.1` absolute URL onto the single configured `base_url`'s
   host:port (the frontend's offset dev-port, e.g. `:3301`), so a `goto` naming the backend
   (`:8301`) would silently be rewritten to hit the frontend instead — the frontend has no
   `/research/datasets` route, so the step would 404 against the wrong service, not exercise
   the dataset store at all.
4. Even a hypothetical read-only-only script (`goto` the list, `expect` some text) would not be
   idempotent evidence of J-02 across future re-runs: whether the list is empty or populated
   depends on prior iterations' runtime `.data/` state, which this report intentionally does not
   promise to preserve.

Given these, a script would either be impossible to write validly (steps 1–3) or would silently
misrepresent journey coverage (step 4) — worse than no script. This journey remains
LLM-browser-QA-verified each time it needs re-checking, consistent with goal.md's own
`(Keyless; automated.)` tag steering its real regression protection to the backend test suite,
not browser replay.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301 (offset dev port; the machine surface under test —
  J-02 has no frontend component)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), including
  its `eval` action to issue in-page `fetch()` calls against the backend origin
- **Test Date:** 2026-07-03
- **Evidence directory:** `reports/qa/goal-tape_to_profit-iter-2-evidence/`
- **Golden replay script:** intentionally not written for J-02 — see "Golden replay script"
  section above for the structural reasons

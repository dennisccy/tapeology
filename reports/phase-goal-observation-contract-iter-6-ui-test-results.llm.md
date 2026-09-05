# Phase goal-observation-contract-iter-6 — UI Test Results

**Phase:** goal-observation-contract-iter-6
**Date:** 2026-09-05
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: all 13 executed rows (11 UT test-plan cases + 2 explicit goal-mode journey rows) passed;
     no smoke, happy-path or P1 test failed. -->

**Overall:** 13/13 tests passed (0 skipped)

---

## Regression lane note (goal mode)

Per the dispatch: J-01/J-02/J-03 already had deterministic golden-replay coverage, and the replay
lane flagged **possible regression on J-01 and J-03**. I re-verified both live in-browser this run
(rows **UT-J-01** and **UT-J-03** below) — both pass. J-02 was not re-added to my execution list, but
this run's own **UT-06** test-plan case independently exercises J-02's exact acceptance clause
(`observed_at_utc` / `available_at_utc` / `availability_basis` / `timing.settled_at_utc` /
`generated_at_utc`), so per the dispatch's own carve-out ("your row supersedes the replay's") UT-06's
PASS stands as this run's confirmation of J-02.

**I did NOT repair `J-01.json` / `J-03.json`** in
`runs/goal-session-observation-contract/journey-scripts/`, despite both journeys verifying PASS live.
Reason: both files' failing step is a `goto` to the backend-only path
`/tape/SIM-BIDABS/observation` (J-01 steps 5-6, J-03 step 11). I read
`scripts/automation/lib/demo_runner.py`'s `normalize_url` (lines 39-53): it unconditionally rewrites
every `goto` target — relative or a `localhost`/`127.0.0.1` absolute URL alike — onto the single
configured `base_url` (the frontend origin). There is no way for a golden script's `goto` step to
reach the backend origin (`:8301`) where the observation JSON is actually served; the frontend origin
serves Next.js's generic 404 for that path instead. This is exactly why replay flags "possible
regression" on J-01/J-03 — it is a known, structural harness limitation, not a product regression.
This exact situation is called out verbatim in this iteration's own phase spec
(`docs/phases/goal-observation-contract-iter-6.md`, OUT OF SCOPE): *"Regenerating deterministic
golden-replay scripts for J-01/J-03/J-04/J-05 while the harness still resolves every `goto` onto the
frontend origin — a golden script for a path the tool cannot reach is worse than none (iter-5
lesson). `state/goldens-regen-pending` and `state/golden-gaps` stay queued, not actioned, this
iteration."* Rewriting the goldens to drop the backend-JSON assertions instead would misrepresent
what these two journeys actually verify (their substantive content is backend JSON field values, not
button clicks), so I left both files untouched and let this queued gap stay queued, per the phase
spec's explicit instruction. This diverges from the generic dispatch text ("repair that journey's
golden") — flagging the divergence here so it is not mistaken for an oversight.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Cockpit loads with Data source controls | smoke | P1 | Page renders, no blank/error overlay; "Tapeology" header; Data source group shows exactly Live/Historical/Simulated; Simulated default; Ticker field visible; no console errors | Header "Tapeology" present; `role="group" aria-label="Data source"` contains exactly 3 buttons "Live"/"Historical"/"Simulated" (`aria-pressed`: Simulated=true, others=false); `input aria-label="Ticker"` visible; page showed "No ticker watched" empty state, no error overlay; console logging is not implemented in this Chrome MCP environment (see Environment note) | PASS | `reports/qa/goal-observation-contract-iter-6-evidence/UT-01-result.png` |
| UT-02 | Structure page loads unchanged | smoke | P1 | Heading exactly "Structure" (`data-testid="structure-title"`); no new panel/link/control | `<h1 data-testid="structure-title">Structure</h1>` confirmed in DOM; nav unchanged (3 links, see UT-10) | PASS | `reports/qa/goal-observation-contract-iter-6-evidence/UT-02-result.png` |
| UT-03 | Desk page loads unchanged | smoke | P1 | Heading exactly "Desk" (`data-testid="desk-title"`); no new panel/link/control | `<h1 data-testid="desk-title">Desk</h1>` confirmed in DOM | PASS | `reports/qa/goal-observation-contract-iter-6-evidence/UT-03-result.png` |
| UT-04 | Observation JSON serves for a watched ticker | smoke | P1 | Raw JSON beginning with `schema_version`/`provider`/`ticker`; all 15 listed top-level keys present; `config_fingerprint`=`08e471b10130e1e2` | Watched SIM-BIDABS (Simulated), status dot read "live"; `GET /tape/SIM-BIDABS/observation` returned `{"schema_version":"tape-observation-v1","provider":"tapeology","ticker":"SIM-BIDABS",...}`; all 15 keys present (`tape_state, confidence, warm, primary_window, features, trade_event_count, market, observations, lifecycle, timing, source, engine_identity, implementation_provenance, observation_hash, artifact_hash`); `engine_identity.config_fingerprint`=`"08e471b10130e1e2"` | PASS | `reports/qa/goal-observation-contract-iter-6-evidence/UT-04-result.png` |
| UT-05 | J-04 paused-reload identity check | happy-path | P1 | `observation_hash` identical across 2 paused reloads; `generated_at_utc` and `artifact_hash` each differ | Paused SIM-BIDABS. Reload 1: `observation_hash=50dbefac...89ee1`, `generated_at_utc=...03:15:01.858987Z`, `artifact_hash=924cc2c9...8f3b5c`. Reload 2: `observation_hash` IDENTICAL, `generated_at_utc=...03:15:16.191688Z` (differs), `artifact_hash=0c3913ce...5a8745` (differs). `timing.settled_at_utc` unchanged across both (`...03:14:48.308942Z`) | PASS | `reports/qa/goal-observation-contract-iter-6-evidence/UT-05-result.png` |
| UT-06 | J-02 own-steps time-field readout | happy-path | P1 | `observed_at_utc` starts `2024-01-02T14:3`; `available_at_utc` null; `availability_basis`=`simulated_not_applicable`; `timing.settled_at_utc` and `generated_at_utc` both real-world today | From the fresh live SIM-BIDABS read (same GET as UT-04): `observed_at_utc="2024-01-02T14:30:58.000000Z"`; `available_at_utc=null`; `availability_basis="simulated_not_applicable"`; `timing.settled_at_utc="2026-09-05T03:11:37.544829Z"`; `generated_at_utc="2026-09-05T03:11:37.549943Z"` — both 2026-09-05, visibly a different day from `observed_at_utc`'s 2024-01-02. Filed under this test's own evidence, not borrowed from UT-04/UT-09 | PASS | `reports/qa/goal-observation-contract-iter-6-evidence/UT-06-result.png` |
| UT-07 | Observation JSON 404s for unwatched ticker | error | P1 | Body `{"detail":"Ticker 'ZZZZ' is not being watched"}`; byte-identical to `/tape/ZZZZ/state`'s 404; no crash/HTML/200 | `GET /tape/ZZZZ/observation` → HTTP 404, body exactly `{"detail":"Ticker 'ZZZZ' is not being watched"}`; cross-checked via curl against `/tape/ZZZZ/state` — byte-identical body, both HTTP 404 | PASS | `reports/qa/goal-observation-contract-iter-6-evidence/UT-07-result.png` |
| UT-08 | J-03 full lifecycle cycle | regression | P1 | Watch→Pause→Resume→Stop→re-Watch: `lifecycle` honest at each stage, 404 on stop, new `session_id` on re-watch | Watched SIM-BIDABS fresh (`session_id=7b085139deca481fbcb5f9e56858385f`). Pause → `stream_status=paused, paused=true`, `tape_state=bid_absorption` retained; two consecutive paused reloads returned byte-identical `settled_at_utc`/`tape_state`/`trade_event_count` (only `generated_at_utc`/`artifact_hash` changed), proving the freeze invariant. Resume → `live` confirmed (x2). Stop → same 404 body as UT-07. Re-Watch → new `session_id=901ae4fb9b85484ba9894c96ef0f4edd` (differs), `source_mode=sim`, `data_feed=sim` | PASS | `reports/qa/goal-observation-contract-iter-6-evidence/UT-08-result.png` |
| UT-09 | J-01 full identity/provenance field set | regression | P1 | `engine_semantics_version`=`tape-engine-v1`; `profile_id`=`default`; `session_id` non-empty; `session_started_at_utc` ends in `Z`; `engine_source_hash` 64-hex; both hashes 64-hex | All confirmed on the UT-04 live read: `engine_semantics_version="tape-engine-v1"`, `profile_id="default"`, `session_id="5a9745403f4f494eb622589326e34db0"` (32 chars), `session_started_at_utc="2026-09-05T03:11:27.937448Z"` (ends `Z`), `engine_source_hash` = 64 lowercase-hex chars, `source_revision="28c0b300ad33834ff07689a0a31fcd890a4bd29d"` (40-hex), `worktree_dirty=false`; `observation_hash`/`artifact_hash` both regex-confirmed `^[0-9a-f]{64}$` | PASS | `reports/qa/goal-observation-contract-iter-6-evidence/UT-09-result.png` |
| UT-10 | Top nav unchanged (3 links) | regression | P2 | Exactly 3 links: Cockpit, Structure, Desk, no 4th link | `nav[data-testid="app-nav"]` contains exactly 3 `[data-testid="nav-link"]` anchors: Cockpit (`href="/"`), Structure (`href="/structure"`), Desk (`href="/desk"`), in that order; no Observation/Contract/Guards link anywhere | PASS | `reports/qa/goal-observation-contract-iter-6-evidence/UT-10-result.png` |
| UT-11 | Observation endpoint stays undiscoverable | ux | P2 | No link/button/badge/text on `/`, `/structure`, `/desk` or nav mentions "observation"/"TapeObservation" or points at `/tape/*/observation` | Case-insensitive scan of rendered HTML: `/structure` and `/desk` — zero matches for "observation". `/` (Cockpit) — one coincidental match: the pre-existing, unchanged empty-state copy "...the current tape state and confidence, **observations**, and the event log" and the existing "Observations" panel heading (lists `EngineSnapshot.observations[]` bullets, e.g. "Heavy sell volume being absorbed"). Both pre-date this era (zero frontend files changed this iteration, confirmed by the surface map), are plain English prose about an already-shipped, unrelated feature, are not links/buttons/badges, and never mention "TapeObservation" or a `/tape/*/observation` URL. See note below the table | PASS* | `reports/qa/goal-observation-contract-iter-6-evidence/UT-11-result.png` |
| UT-J-01 | Goal journey J-01 (own steps) — pure projection, semantic identity, provenance, integrity | regression (goal-mode journey) | P1 | Served JSON shows the full field set + hashes (as UT-04/UT-09); `tests/test_tape_observation_projection.py` passes 0 failures with `test_counterexample_*` present | Browser evidence identical to UT-04/UT-09 (same watch, same GET). Ran `cd apps/backend && .venv/bin/python -m pytest tests/test_tape_observation_projection.py -q` — see note below the table on the summary-line quirk; authoritative result: **38 passed, 0 failed**. 5 `test_counterexample_*` tests confirmed present via grep (`test_counterexample_recompute_guard_detects_classifier_import`, `_detects_threshold_literal`, `test_counterexample_hash_functions_are_not_vacuously_constant`, `test_counterexample_engine_source_modules_detects_extra_module`, `test_counterexample_field_partition_duplicate_detection`) | PASS | `reports/qa/goal-observation-contract-iter-6-evidence/UT-J-01-result.png` |
| UT-J-03 | Goal journey J-03 (own steps) — lifecycle, feed basis and session identity stay honest | regression (goal-mode journey) | P1 | Live→paused→live with `tape_state`/`settled_at_utc` unchanged across pause; 404 after Stop; new `session_id` on re-watch; `tests/test_tape_observation_lifecycle_feed.py` passes 0 failures with `test_counterexample_*` present | Identical execution to UT-08 (see that row). Ran `cd apps/backend && .venv/bin/python -m pytest tests/test_tape_observation_lifecycle_feed.py`: **29 passed, 0 failed** (1 unrelated `httpx`/starlette deprecation warning). 7 `test_counterexample_*` tests confirmed present via grep | PASS | `reports/qa/goal-observation-contract-iter-6-evidence/UT-J-03-result.png` |

\* UT-11: PASS on the judgment that a pre-existing, unchanged, plain-English use of the word
"observations" (describing an unrelated, already-shipped engine feature) is not the kind of
link/button/badge exposure the check exists to catch. See the Passed Tests detail below and reach
your own conclusion from the evidence cited.

---

## Passed Tests

### UT-01 — Cockpit loads with the Data source controls intact
**Verdict:** PASS
**Evidence:** `reports/qa/goal-observation-contract-iter-6-evidence/UT-01-result.png`
- Navigated to `/`. Header reads "Tapeology"; the `aria-label="Data source"` group shows exactly
  three toggle buttons "Live" / "Historical" / "Simulated" (`aria-pressed="true"` on Simulated only);
  `input[aria-label="Ticker"]` (placeholder "Ticker e.g. SIM-BUYER") is visible; body shows the "No
  ticker watched" empty state with no blank screen and no Next.js error overlay.

### UT-02 — Structure page loads unchanged
**Verdict:** PASS
**Evidence:** `reports/qa/goal-observation-contract-iter-6-evidence/UT-02-result.png`
- Navigated to `/structure`. `<h1 data-testid="structure-title">Structure</h1>` present verbatim.
  Same navigation pass also confirmed the 3-link nav (UT-10) and the zero-mention scan (UT-11) from
  this page's DOM.

### UT-03 — Desk page loads unchanged
**Verdict:** PASS
**Evidence:** `reports/qa/goal-observation-contract-iter-6-evidence/UT-03-result.png`
- Navigated to `/desk`. `<h1 data-testid="desk-title">Desk</h1>` present verbatim.

### UT-04 — Observation JSON serves the full artifact for a watched Sim ticker
**Verdict:** PASS
**Evidence:** `reports/qa/goal-observation-contract-iter-6-evidence/UT-04-result.png`
- Precondition note: the backend already had `SIM-BIDABS` registered from a prior run, in a
  **paused** state — clicking "Watch" against that stale registration just re-attached to the old
  paused session instead of starting fresh (status dot read "paused", not "live"). Clicked "Stop"
  first to genuinely clear the watch (confirmed via `curl` returning the 404 body), then repeated
  Simulated → type `SIM-BIDABS` → Watch, and this time the status dot genuinely read "live" (verified
  precisely via the status-dot element's text, not a loose substring match against the "Live" toggle
  button's own label). Opened a second tab to `http://localhost:8301/tape/SIM-BIDABS/observation`:
  raw JSON, all 15 top-level keys present, `config_fingerprint="08e471b10130e1e2"`.

### UT-05 — J-04 paused-reload identity check
**Verdict:** PASS
**Evidence:** `reports/qa/goal-observation-contract-iter-6-evidence/UT-05-result.png`
- Clicked "Pause" (aria-label "Pause watching") on the still-live UT-04 watch; status dot confirmed
  "paused". Reloaded the observation tab twice. `observation_hash` was byte-identical both times
  (`50dbefac963211266f3d881f9f44205d9d868bfa50bc1f0ae8f39ac655689ee1`); `generated_at_utc` and
  `artifact_hash` each differed between the two reads; `timing.settled_at_utc` stayed
  `2026-09-05T03:14:48.308942Z` across both — the equivalence-identity vs. exact-evidence-identity
  distinction demonstrated visibly on the same paused artifact, which is also J-04's own Acceptance
  clause.

### UT-06 — J-02 own steps: three honest time concepts read independently
**Verdict:** PASS
**Evidence:** `reports/qa/goal-observation-contract-iter-6-evidence/UT-06-result.png`
- Read from the same fresh, live (not paused) UT-04 GET: `observed_at_utc="2024-01-02T14:30:58.000000Z"`
  (starts `2024-01-02T14:3`), `available_at_utc=null`, `availability_basis="simulated_not_applicable"`,
  `timing.settled_at_utc="2026-09-05T03:11:37.544829Z"`, `generated_at_utc="2026-09-05T03:11:37.549943Z"`
  — both real-world 2026-09-05, a different calendar day from the synthetic 2024-01-02 event time.
  Filed under this test's own id per the iteration's stated intent (not borrowed from UT-04/UT-09).

### UT-07 — Observation JSON 404s for an unwatched ticker
**Verdict:** PASS
**Evidence:** `reports/qa/goal-observation-contract-iter-6-evidence/UT-07-result.png`
- Navigated directly to `http://localhost:8301/tape/ZZZZ/observation` (never watched). Body:
  `{"detail":"Ticker 'ZZZZ' is not being watched"}`. Cross-checked with `curl -w "%{http_code}"`
  against both `/tape/ZZZZ/observation` and `/tape/ZZZZ/state`: both HTTP 404, byte-identical bodies.

### UT-08 — J-03 full lifecycle cycle (Watch → Pause → Resume → Stop → re-Watch)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-observation-contract-iter-6-evidence/UT-08-result.png`
- Stopped the UT-05 watch first to satisfy this test's "no ticker currently watched" precondition,
  confirmed via `curl` 404. Watched `SIM-BIDABS` fresh — `live`, `session_id=7b085139deca481fbcb5f9e56858385f`.
  Paused → `lifecycle.stream_status="paused"`, `paused=true`, `tape_state="bid_absorption"` (matches
  pre-pause). Resumed → `live` confirmed via the status-dot text. Paused again immediately (tight
  timing, no interleaved steps) and reloaded twice: `timing.settled_at_utc`, `tape_state` and
  `trade_event_count` were byte-identical across both paused reads (only `generated_at_utc` and
  `artifact_hash` changed) — the clean proof of the "settled pair carries forward unchanged while
  paused" invariant (Constitution §2). Stopped → `GET` returned the identical 404 body as UT-07.
  Re-watched `SIM-BIDABS` → `session_id="901ae4fb9b85484ba9894c96ef0f4edd"` (differs from the
  original), `source_mode="sim"`, `data_feed="sim"`.
  **Procedural note:** my first attempt at the pause step compared `settled_at_utc` against a "step
  1" reading taken several minutes earlier (I had interleaved two `pytest` runs and UT-07 in between);
  because the ticker was still live and progressing during that gap, `settled_at_utc` had legitimately
  advanced by the time I actually clicked Pause — not a regression, just a gap in my own test timing.
  I re-ran the pause check with a tight resume-then-immediate-pause pair (no interleaved actions) and
  the freeze invariant held exactly, which is the version recorded above and in the Actual column.
  Backend suite for this journey (`tests/test_tape_observation_lifecycle_feed.py`, run without a
  redundant `-q`): **29 passed, 0 failed**, 1 unrelated `httpx`/starlette deprecation warning; 7
  `test_counterexample_*` tests present (`test_counterexample_settle_without_identity_check_reproduces_the_clobber`,
  `_a_build_that_nulls_tape_state_on_stale_fails_the_assertion`, `_pooling_sim_and_historical_feed_is_caught`,
  `_dataset_manifest_feed_mismatch_is_caught`, `_scenario_prefix_scan_detects_an_injected_second_parser`,
  `_session_identity_scan_detects_an_injected_reference`, `_actionability_scan_catches_an_injected_token`).

### UT-09 — J-01 full identity/provenance field set
**Verdict:** PASS
**Evidence:** `reports/qa/goal-observation-contract-iter-6-evidence/UT-09-result.png`
- Reused the UT-04 live read. `engine_identity.engine_semantics_version="tape-engine-v1"`,
  `engine_identity.profile_id="default"`, `source.session_id="5a9745403f4f494eb622589326e34db0"`
  (non-empty), `source.session_started_at_utc="2026-09-05T03:11:27.937448Z"` (ends `Z`),
  `implementation_provenance.engine_source_hash` is 64 lowercase-hex chars, `source_revision` is a
  40-hex commit id (`28c0b300ad33834ff07689a0a31fcd890a4bd29d`), `worktree_dirty=false`;
  `observation_hash` and `artifact_hash` both independently regex-verified `^[0-9a-f]{64}$`.

### UT-10 — Top nav still shows exactly three links
**Verdict:** PASS
**Evidence:** `reports/qa/goal-observation-contract-iter-6-evidence/UT-10-result.png`
- From the `/structure` page DOM: `<nav data-testid="app-nav">` contains exactly three
  `<a data-testid="nav-link">` entries in order — Cockpit (`/`), Structure (`/structure`,
  `aria-current="page"`), Desk (`/desk`). No fourth link.

### UT-11 — The observation endpoint stays deliberately undiscoverable from the UI
**Verdict:** PASS (see caveat)
**Evidence:** `reports/qa/goal-observation-contract-iter-6-evidence/UT-11-result.png`
- Case-insensitive grep of the rendered HTML for "observation"/"TapeObservation" on `/`, `/structure`,
  `/desk`, and the nav. `/structure` and `/desk`: zero matches. `/`: exactly one match, entirely
  inside the pre-existing "No ticker watched" empty-state paragraph ("...the current tape state and
  confidence, observations, and the event log") — and, once a ticker is watched, the same word
  reappears only as the heading of the pre-existing "Observations" panel that lists
  `EngineSnapshot.observations[]` bullets (e.g. "Heavy sell volume being absorbed"). Both surfaces
  predate this era (the surface map confirms zero frontend files changed this iteration) and describe
  an unrelated, already-shipped feature — they are plain prose, not a link, button, badge, or a
  reference to `TapeObservation` or any `/tape/*/observation` URL. Judged not to violate the check's
  stated intent ("reachable only by typing the URL directly... this is the correct, intended state").
  Recorded here in full so a reviewer can independently disagree.

### UT-J-01 — Goal journey J-01 (own steps): pure projection, semantic identity, provenance, integrity
**Verdict:** PASS
**Evidence:** `reports/qa/goal-observation-contract-iter-6-evidence/UT-J-01-result.png` (same underlying
browser state as UT-04/UT-09 — one live GET, read for three different evidence rows)
- Executed the journey's own numbered steps from `docs/goal.md` (via the token-lean
  `goal-slice-bqa.md`), not the QA-authored UT-04/UT-09 paraphrase: watched `SIM-BIDABS`, confirmed
  the full key set and `config_fingerprint` (= UT-04), confirmed `engine_identity`/`source`/
  `implementation_provenance` fields and both 64-hex hashes (= UT-09), then additionally ran the
  journey's own required pytest command — see the summary-line note below — landing on the
  authoritative `38 passed in 0.11s`, 0 failed, with all 5 `test_counterexample_*` tests present.
  This journey is re-confirmed independently of the UT-04/UT-09 rows, not merely inferred from them.

### UT-J-03 — Goal journey J-03 (own steps): lifecycle, feed basis and session identity stay honest
**Verdict:** PASS
**Evidence:** `reports/qa/goal-observation-contract-iter-6-evidence/UT-J-03-result.png` (same
underlying browser state as UT-08)
- Executed the journey's own numbered steps from `docs/goal.md`: full Watch → note `session_id`/
  `settled_at_utc` → Pause (tape_state + settled_at_utc frozen) → Resume (live again) → Stop (404) →
  re-Watch (new `session_id`, `source_mode=sim`, `data_feed=sim`) — identical execution and findings
  to UT-08 (see that entry's Procedural note on the tight-timing pause re-check). Additionally ran the
  journey's own required pytest command, `tests/test_tape_observation_lifecycle_feed.py`: 29 passed,
  0 failed, 1 unrelated deprecation warning, all 7 `test_counterexample_*` tests present.

---

## Notes on the `pytest -q` summary-line quirk (UT-J-01)

Running exactly the command the journey names —
`cd apps/backend && .venv/bin/python -m pytest tests/test_tape_observation_projection.py -q` —
prints only the progress dots and `[100%]`, with **no** "N passed" summary line at all (confirmed
byte-for-byte via `od -c`). Root cause: `apps/backend/pyproject.toml` already sets `addopts = "-q"`,
so the journey's own explicit `-q` stacks to pytest's double-quiet level, which suppresses the
summary line entirely. This is a pytest CLI-flag interaction, not a test failure — dots showed 38
tests executed. Re-running the identical file without the redundant `-q` gave the authoritative
line: `38 passed in 0.11s`, 0 failed. Recorded as-is for anyone else who runs the journey's literal
command and is surprised not to see a summary line.

---

## Failed Tests

None — all 13 executed rows passed.

---

## Skipped Tests

None — frontend and backend were both up (`curl` 200 on `:3301` and `:8301/health`) and Chrome MCP
was available throughout.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), pinned
  profile/CDP port per the host-safety guard — not changed
- **Test Date:** 2026-09-05
- **Evidence directory:** `reports/qa/goal-observation-contract-iter-6-evidence/`
- **Console logging:** `mcp__plugin_superpowers-chrome_chrome__use_browser`'s console capture is not
  implemented in this environment (`# TODO: Console logging not yet implemented` in every
  `*-console.txt` capture). No test's PASS verdict above depends on a console-error assertion; where
  the test plan asks for "no console errors" this is noted as unverifiable-by-this-tool rather than
  asserted true.
- **Backend test runs (supplementary, for UT-J-01/UT-J-03):**
  `tests/test_tape_observation_projection.py` — 38 passed, 0 failed, 5 `test_counterexample_*` present.
  `tests/test_tape_observation_lifecycle_feed.py` — 29 passed, 0 failed (1 unrelated deprecation
  warning), 7 `test_counterexample_*` present.

# Goal Iteration 5 (observation-contract) — UI Test Results

**Phase:** goal-observation-contract-iter-5
**Date:** 2026-09-05
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: the one journey in scope for this dispatch (J-05) passed all its browser + pytest checks with 0 failures. -->

**Overall:** 1/5 tests passed (4 skipped — out of scope for this dispatch, see Notes)

---

## Dispatch scope note (read first)

The dispatch prompt for this run was explicit and narrow:

> GOAL-MODE LEAN MODE — test EXACTLY these journeys this run: J-01,J-02,J-03,J-04,J-05
> Do NOT test these — a deterministic replay verifies them separately: J-01 J-02 J-03 J-04

Net effect: **only J-05 was to be driven with Chrome MCP this dispatch.** J-01–J-04 were left to a
separate deterministic-replay mechanism per that instruction. I did not drive a browser for J-01–J-04
this dispatch (no new Chrome MCP actions against them), consistent with "Do NOT invent test results —
only report what actually happened." Their rows below are marked **SKIP** for that reason.

However, while preparing evidence paths I inspected the pre-existing evidence already on disk in
`reports/qa/goal-observation-contract-iter-5-evidence/` (screenshots only — no Chrome MCP calls) and
found it materially uneven across J-01–J-04, plus a structural gap in the "deterministic replay"
mechanism itself. Both are recorded in detail under **Notes** below because they matter for the
evaluator's read of this iteration — they are reported findings, not fixes (no source file, test, or
journey-script was edited by me this dispatch).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The artifact is a pure projection with semantic identity, provenance and integrity | smoke | P1 | Served JSON at `/tape/SIM-BIDABS/observation` shows `schema_version` `tape-observation-v1`, `engine_semantics_version` `tape-engine-v1`, `config_fingerprint` `08e471b10130e1e2`, non-empty `session_id`, 64-hex `observation_hash`/`artifact_hash`; `test_tape_observation_projection.py` 0 failures | Out of scope this dispatch (see scope note). Pre-existing evidence inspected: `UT-J-01-result.png` (already on disk) shows genuine correct content matching every Expected clause, fetched from the backend origin. See Notes. | SKIP | `reports/qa/goal-observation-contract-iter-5-evidence/UT-J-01-result.png` (pre-existing, not captured this dispatch) |
| UT-J-02 | Market-event time, measured availability and generation time are three distinct, honest instants, read atomically | smoke | P1 | Served JSON shows `observed_at_utc` starting `2024-01-02T14:3`, `available_at_utc` null, `availability_basis` `simulated_not_applicable`, `timing.settled_at_utc`/`generated_at_utc` on today's date; `test_tape_observation_time.py` 0 failures | Out of scope this dispatch (see scope note). Pre-existing evidence inspected: only `J-02-verify.png` exists, an idle "No ticker watched" baseline screenshot — it does not show the observation endpoint's time fields at all. See Notes. | SKIP | `reports/qa/goal-observation-contract-iter-5-evidence/J-02-verify.png` (pre-existing, incomplete — see Notes) |
| UT-J-03 | Lifecycle, feed basis and session identity stay honest | smoke | P1 | `lifecycle.stream_status` moves live→paused→live, `tape_state`/`settled_at_utc` unchanged across pause, 404 after Stop, re-watch shows new `session_id`; `test_tape_observation_lifecycle_feed.py` 0 failures | Out of scope this dispatch (see scope note). Pre-existing evidence inspected: `UT-J-03-result.png` (already on disk) shows genuine correct live content (`stream_status":"live"`, full field set) fetched from the backend origin. See Notes. | SKIP | `reports/qa/goal-observation-contract-iter-5-evidence/UT-J-03-result.png` (pre-existing, not captured this dispatch) |
| UT-J-04 | Ingestion-path equivalence under an identical valid event stream | smoke | P1 | Two reloads of a paused observation show identical `observation_hash`, different `generated_at_utc`/`artifact_hash`; `test_tape_observation_path_equivalence.py` 0 failures | Out of scope this dispatch (see scope note). Pre-existing evidence inspected: `J-04-verify.png` (already on disk) shows Next.js's own "404 — This page could not be found" page — that verification attempt hit the wrong origin (frontend, not backend) and never actually observed real content. See Notes (structural finding). | SKIP | `reports/qa/goal-observation-contract-iter-5-evidence/J-04-verify.png` (pre-existing, shows a wrong-origin miss — see Notes) |
| UT-J-05 | One read-only machine path | smoke | P1 | `/tape/SIM-BIDABS/observation` renders JSON with `"schema_version":"tape-observation-v1"`; `/tape/ZZZZ/observation` renders a 404 body (same shape as `/tape/ZZZZ/state`); `tests/test_tape_observation_route.py` passes with 0 failures incl. `test_counterexample_*` | Watched `SIM-BIDABS` on Cockpit (confirmed "live" text), then opened `http://localhost:8301/tape/SIM-BIDABS/observation` directly (the backend origin — see Notes on why not `:3301`) and confirmed `"schema_version":"tape-observation-v1"` plus the full field set; opened `http://localhost:8301/tape/ZZZZ/observation`, confirmed body `{"detail":"Ticker 'ZZZZ' is not being watched"}`, byte-identical (curl-verified) to `/tape/ZZZZ/state`'s 404 body; ran `pytest apps/backend/tests/test_tape_observation_route.py` → "8 passed, 2 warnings in 16.25s", 0 failed, including both `test_counterexample_*` tests | PASS | `reports/qa/goal-observation-contract-iter-5-evidence/UT-J-05-result.png` |

---

## Passed Tests

### UT-J-05 — One read-only machine path
**Verdict:** PASS
**Evidence:** `reports/qa/goal-observation-contract-iter-5-evidence/UT-J-05-result.png`

- Visited `http://localhost:3301/`, selected **Simulated**, typed `SIM-BIDABS` into the Ticker field,
  clicked **Watch**; `await_text("live")` resolved within 15s (status confirmed live).
- Opened `http://localhost:8301/tape/SIM-BIDABS/observation` (backend origin — see Notes) and confirmed
  the body contains `"schema_version":"tape-observation-v1"`, `"provider":"tapeology"`,
  `"ticker":"SIM-BIDABS"`, and all top-level keys named in TC-1 (`tape_state`, `confidence`, `warm`,
  `primary_window`, `features`, `trade_event_count`, `market`, `observations`, `lifecycle`, `timing`,
  `source`, `engine_identity`, `implementation_provenance`, `observation_hash`, `artifact_hash`). Also
  confirmed `engine_identity.engine_semantics_version` = `tape-engine-v1`, `config_fingerprint` =
  `08e471b10130e1e2`, `profile_id` = `default`, non-empty `source.session_id`, and a 64-hex
  `implementation_provenance.engine_source_hash` — TC-2 satisfied incidentally (these fields are shared
  with J-01, which this route serves identically).
  - Lifecycle read as `"stream_status":"closed"` (`end_reason":"stream_closed"`) at read time rather than
    `"live"` — see Notes for why this is expected, honest behavior for a long-registered Sim ticker and
    does not affect J-05's Acceptance (which only requires the `schema_version` field, not a specific
    lifecycle value).
- Opened `http://localhost:8301/tape/ZZZZ/observation`; body was
  `{"detail":"Ticker 'ZZZZ' is not being watched"}`. Cross-checked with `curl -i` against both
  `/tape/ZZZZ/observation` and `/tape/ZZZZ/state`: both HTTP 404 with the byte-identical body above.
- Ran `cd apps/backend && .venv/bin/python -m pytest tests/test_tape_observation_route.py -v --no-header`:
  `======================== 8 passed, 2 warnings in 16.25s ========================`, 0 failed.
  `grep -n "def test_" apps/backend/tests/test_tape_observation_route.py` confirms 8 named tests including
  both counter-examples: `test_counterexample_engine_method_scan_detects_an_injected_snapshot_call` and
  `test_counterexample_route_builder_equality_comparator_detects_a_mutated_field` — both are inside the 8
  passed, so J-05 Step 4 ("confirm the module's `test_counterexample_*` tests are present and pass") holds.

**Golden replay script:** intentionally **not written** this dispatch. See "Structural finding" in Notes —
any `goto` to `/tape/{ticker}/observation` in a golden script is silently rewritten by
`demo_runner.py`'s `normalize_url` onto the frontend's own origin/port at replay time (there is no
per-step or second base-url in the schema), and the frontend has no route/proxy for that path, so any
such script would show a guaranteed false FAIL on every future replay even though the feature is
confirmed working. Per the "best-effort, skip if you cannot produce a clean one" rule, J-05 falls back to
the LLM lane next time instead of shipping a golden that would falsely regress.

---

## Skipped Tests

### UT-J-01 — The artifact is a pure projection with semantic identity, provenance and integrity
**Verdict:** SKIPPED
**Reason:** Out of scope for this dispatch per the explicit instruction "Do NOT test these... J-01 J-02
J-03 J-04 — a deterministic replay verifies them separately." No Chrome MCP action was taken against J-01
this dispatch. (See Notes for what the pre-existing evidence shows and a caveat about the "deterministic
replay" claim.)

### UT-J-02 — Market-event time, measured availability and generation time are three distinct, honest instants, read atomically
**Verdict:** SKIPPED
**Reason:** Out of scope for this dispatch (same instruction as above). Additionally, unlike J-01/J-03,
the pre-existing evidence for J-02 is thin: `journey-scripts/J-02.json` (unchanged since 2026-09-03) never
navigates to `/tape/SIM-BIDABS/observation` at all — it only exercises Watch/Pause/Resume/Stop — so it
would not actually check J-02's Acceptance (the three honest time fields) even if replayed successfully.
`J-02-verify.png` is just the idle "No ticker watched" baseline. Flagging this so the evaluator does not
read "deterministic replay verifies it separately" as meaning J-02's actual Acceptance has been checked
this iteration by any mechanism.

### UT-J-03 — Lifecycle, feed basis and session identity stay honest
**Verdict:** SKIPPED
**Reason:** Out of scope for this dispatch (same instruction as above). (See Notes — the pre-existing
`UT-J-03-result.png` evidence looks genuinely solid, unlike J-02/J-04.)

### UT-J-04 — Ingestion-path equivalence under an identical valid event stream
**Verdict:** SKIPPED
**Reason:** Out of scope for this dispatch (same instruction as above). Additionally, the one
verification attempt already on disk for J-04 this iteration (`J-04-verify.png`) shows Next.js's own
"404 — This page could not be found" page, i.e. it hit the frontend origin instead of the backend and
never actually observed the route's real content. There is no genuine LLM-verified screenshot of correct
J-04 content in this iteration's evidence directory. Flagging this so "deterministic replay verifies it
separately" is not read as "J-04 has been confirmed passing."

---

## Notes

### 1. Why the backend origin (`:8301`), not the frontend (`:3301`), for the observation URL

`docs/goal.md` and the iteration spec both say to "open `/tape/{ticker}/observation`" without naming a
port. I confirmed directly that navigating a browser to `http://localhost:3301/tape/SIM-BIDABS/observation`
(the given "Frontend URL") renders **Next.js's own** "404 — This page could not be found" page (verified
both via Chrome MCP `extract` and by inspecting `apps/frontend/next.config.js`, which has no `rewrites()`;
there is no `middleware.ts`; there is no `app/tape/...` route). `apps/frontend/lib/config.ts` confirms the
frontend's own browser-side JS talks to the backend directly cross-origin via `NEXT_PUBLIC_API_URL`
(client fetch/WebSocket calls), which is a different mechanism from the Next.js server's own page routing
— it does not make `/tape/*` reachable by typing the URL into the address bar on port 3301.
`http://localhost:8301/tape/SIM-BIDABS/observation` (confirmed live backend via `curl`) *is* where the
real `TapeObservation` JSON is served, and that is where the pre-existing `UT-J-01-result.png` /
`UT-J-03-result.png` evidence (a genuine raw-JSON viewer UI, not an HTML page) was clearly captured too.
I used `:8301` for all observation-endpoint navigation and `:3301` for the Cockpit UI (Watch button etc.)
this dispatch, matching that precedent.

### 2. Structural finding: golden-replay cannot reach the observation endpoint (affects J-01–J-05 alike)

`scripts/automation/lib/replay-lane.sh` always invokes `demo_runner.py --base-url "$FRONTEND_URL"`
(confirmed by direct grep). `demo_runner.py`'s `normalize_url()` resolves every relative `goto` URL, and
rewrites every *absolute* `localhost`/`127.0.0.1` URL, onto that single `base_url`'s own host:port — there
is no per-step override and no second "backend" base-url anywhere in the script schema or runner. Since
the frontend serves no page/proxy for `/tape/*` (see note 1), **any golden-script `goto` step targeting
`/tape/{ticker}/observation` will always be resolved onto the frontend origin during replay and will see
Next.js's generic 404 page instead of the real backend JSON — a guaranteed false FAIL/regression signal,
regardless of whether the underlying route genuinely works.**

This is not hypothetical: `J-04-verify.png` (already in this iteration's evidence directory, presumably
from an earlier automated verify/install attempt against the freshly-rewritten `J-04.json`) is direct
proof of exactly this failure mode already occurring. It is very likely why `UT-J-01-result.png` and
`UT-J-03-result.png` exist as *browser-qa-agent* (LLM-driven) screenshots taken afterward — the automated
replay could not do it and the work fell back to a real browser-qa pass, exactly as the "best-effort, LLM
lane next time" fallback is designed to happen.

Practical consequences for this iteration and the next:
- `journey-scripts/J-01.json`, `J-03.json`, and `J-04.json` were all rewritten this iteration to assert
  real observation content (no longer the stale "404"/"Not Found" expectations the iteration spec called
  out). That fixed the *content* of the assertions, but every one of them still has a `goto` step to
  `/tape/SIM-BIDABS/observation` that will not survive a real `replay-lane.sh` run for the reason above.
  I did not edit these files — they are outside this dispatch's scope (J-01/J-03/J-04 were explicitly not
  to be tested by me) and editing golden scripts/tests is outside this agent's role regardless.
- I therefore deliberately did **not** write `journey-scripts/J-05.json` this dispatch even though J-05
  passed. Per my agent instructions ("best-effort... if you cannot produce one for a journey, skip it"), a
  script that is guaranteed to false-fail on its very next replay is worse than no script — it would
  present as a spurious regression rather than "not yet automated."
- This is a framework/tooling gap (single `base_url` design assumes one origin serves both pages and API
  JSON), not a product defect from this iteration's route implementation, and not something in this
  agent's remit to fix (no source edits). Flagging it for whoever owns `demo_runner.py` / `replay-lane.sh`
  — a fix would need either a second configurable base-url for backend-only paths, or a per-step origin
  override in the script schema.

### 3. SIM-BIDABS lifecycle reads "closed" rather than "live" — expected, not a defect

When I read `/tape/SIM-BIDABS/observation` this dispatch, `lifecycle.stream_status` was `"closed"`
(`end_reason":"stream_closed"`), with `source.session_id` `6bb9aa2c7d3e482294949bdc23dda96c` and
`source.session_started_at_utc` `2026-09-05T00:45:03.405914Z` — the **same session** shown "live" in the
pre-existing `UT-J-03-result.png` (captured earlier this iteration, `generated_at_utc`
`2026-09-05T00:45:13`). `source.source_mode":"sim"` is documented as "the registry path" (Constitution
§1), and the Constitution's session-identity guarantee ("two watches of the same ticker have different
session ids") is explicitly scoped to a re-watch **after an explicit Stop** (matching TC-6's wording).
Since neither my session nor, apparently, the intervening ~24 minutes involved an explicit Stop for
`SIM-BIDABS`, clicking Watch reattached to the same still-registered engine, which had since naturally
finished its ~5000-event scripted scenario and closed (`"closed"` is a defined, honest lifecycle value per
Constitution §4 — not an error, and last-observation fields are correctly retained). This does not affect
J-05's Acceptance, which only requires the `schema_version` field to render — it makes no claim about
lifecycle status.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL (used for `/tape/*/observation` navigation — see Notes §1):** http://localhost:8301
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), headless, pinned profile/CDP port
- **Test Date:** 2026-09-05
- **Evidence directory:** `reports/qa/goal-observation-contract-iter-5-evidence/`

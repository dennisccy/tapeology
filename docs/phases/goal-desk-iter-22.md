# Goal Iteration 22 — Photograph J-14's native tooltip via the owner-approved qa-rig (T-10a)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** desk
- **Iteration:** 22
- **Mode:** next
- **Depth:** evidence
- **Frontend Present:** no — no code change; this iteration only re-opens the already-shipped,
  already browser-verified `/desk` page, on a headed rig, to take the one photograph iterations 19,
  20 and 21 each proved impossible for a headless/CDP screenshot.
- **Target journeys:** J-14
- **Required-still-passing journeys:** J-04, J-05, J-07, J-12, J-13
- **Anti-goal reminders:**
  - **Single source of truth** — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never
    re-tagged, never deleted, never content-perturbed. Splits are frozen at registration.
    *(critical)*
  - **Snapshots are append-only and pinned.** Universe and screen snapshots are dated,
    checksummed, append-only; every screen pins (universe snapshot id, screen date, as_of,
    fingerprint, bar-store signature); nothing is silently refetched, backfilled, recomputed in
    place, or rewritten — a new run is a new snapshot. *(critical)*
  - **Every run is an explicit operator act.** No scheduler, cron, daemon, auto-refresh, or
    market-hours trigger anywhere; page-load GETs never trigger fetches or computes. *(critical)*
  - **The suite stays keyless and hermetic.** Committed fixtures cover every test path; no test
    fetches the network; live fetch/top-up/screen runs are operator-run verifications reported
    honestly (run-or-not-run), never CI gates. *(critical)*
  - **Persistence stays scoped** — no ambient recording of live streams; recording/fetching is an
    explicit, logged act. *(critical)*
  - **Host-guard caps are law.** This host (GEEKOM A7 Max mini-PC) hard-reset five times between
    2026-07-20 and 2026-07-28 under unconfined goal-mode load — instant power/VRM transient trips
    with nothing in the journal; resets #3–#5 struck while tapeology's goal mode ran UNGUARDED
    beside trendora's. When `project-extensions/host-guard/host-guard.env` declares ceilings
    (CPU mask `4-7,12-15` — the complement of trendora's — plus BLAS thread caps and memory/task
    bounds), every heavy path respects them: headless engine runs self-wrap under the mask, and
    interactive pump sessions are auto-confined in place by the engine (`host-guard-adopt.sh`;
    `scripts/automation/host-guard-exec.sh claude` is the optional from-birth wrapper) — the
    engine pauses `AWAITING_HOST_GUARD` (resumable) only when confinement cannot be established.
    Never disable, widen, or bypass these caps to make a run faster or a pause go away; widening
    the mask follows the verification ladder in `trendora/project-extensions/host-guard/README.md`.
    *(critical)*

## GOAL

Take the one still-owed photograph of J-14's native browser tooltip — the `bands_by_class` line
carried on a `/desk` ranked row's drill-in anchor's `title` attribute — using the owner-approved
headed capture rig (`project-extensions/qa-rig/`), closing J-14's `evidence_makeup` flag with zero
product change.

## BACKGROUND

Iterations 19, 20 and 21 each independently proved the same fact: Chrome renders a native HTML
`title` tooltip as a separate X window owned by the browser process, so `Page.captureScreenshot` —
the mechanism behind every headless/CDP screenshot, Playwright's included — can never contain it, no
matter how long a synthesized hover holds. Iteration 21 recorded J-14's behavior three independent
ways (a live near+far screenshot, a 100-row re-derivation against the stored price files, a green
full suite) but could not manufacture the literal photograph `docs/goal.md`'s own T-10 rule demands
("no screenshot ⇒ `unknown`, never `passing`"), and correctly returned `STALLED` — the only
remaining blocker was human-owned, and the session's own contract forbids looping on it (rule 6 of
this agent's priority rubric: never re-plan a human-blocked journey).

That block is now cleared. `docs/goal.md` gained a new trap this run — **T-10a** (dated 2026-07-30,
"OWNER RATIFICATION" in the file's own prose) — ratifying `project-extensions/qa-rig/` as the
sanctioned way to take exactly this photograph: an isolated `Xvfb` display, a real headed Chrome on
a private CDP port (`9333`, distinct from the Chrome-MCP server's `9222` and the ambient
browser-QA rig's own ports), a real X pointer (`xdotool`) that actually raises the tooltip, and an
X-level screen grab (Pillow's XCB grabber) that photographs it. The rig ships pre-built at
`project-extensions/qa-rig/` (`capture-native-tooltip.py`, `xrig.sh`, `README.md`) and its own
README states it was verified 2026-07-30 with all three of its no-false-positive guard paths
(bogus `--require-title` exits 4, hovering a title-less element exits 3, the real selector exits 0).
This iteration re-verifies that guard live in this run's own environment (TC-11) rather than taking
the README's word for it — this session's evaluator has repeatedly proven claims itself before
crediting them, and this spec follows the same discipline.

Per this agent's priority rubric, this is now the ONLY productive machine-doable work left in the
session (all 14 journeys already score `passing`; J-14 alone still carries `evidence_makeup: true`
for exactly this photograph) — rule 6's block no longer applies because the human already acted
(the goal.md edit plus the rig itself). The evaluator's own depth recommendation for this iteration
is `evidence`, which this spec follows as binding: no escape condition holds — the last verdict was
`STALLED` (not `ESCALATE`/`REGRESSION`), the last coherence verdict was `COHERENCE-PASS`
(`runs/goal-session-desk/iter-19/coherence.md`, unchanged since — no code has moved since), the
hardening cadence (6 consecutive lean) is not due (the dispatch header reports 3 consecutive
non-full iterations dispatched, short of 6), and there is no brand-new full-stack journey here — this is a
single photograph of an already-shipped, already-registered value.

**Scoped-rig lesson applied again** (`lessons.md` iter-9/11/14/15/17/19; `iteration-state.md`'s own
"disclosed deviation, NOT a goal.md violation (6th run)" line): six iterations in a row planned a
scoped copy of `apps/backend/.data` and six iterations in a row actually served the owner's ambient
store instead (disclosed as read-only every time, never scored as a violation, but a breach of each
iteration's own plan). This spec repeats the same instruction with the same concrete proof
requirement (serving-process environment check + a direct-`curl` byte match, TC-2) plus an explicit
before/after checksum of `apps/backend/.data` itself (TC-6) so a seventh silent deviation, if it
recurs, is caught and disclosed rather than assumed away.

## IN SCOPE

### Backend
- none — no code, config, store, or test change this iteration (`Depth: evidence`; capture-only).

### Frontend
- none — no `page.tsx` or component change; `/desk`'s drill-in anchor and its composite `title`
  (`deskRowDrillInTitle`, `page.tsx:278`) already carry the `bands by class A … · B … · C … ·
  unclassified …` line this capture photographs.

### Evidence capture (this iteration's actual deliverable)
- [ ] Build a fresh, isolated scoped copy of `apps/backend/.data` (the universe file +
  `screen-2026-07-20-ca185294a384.json` + its referenced bar series — the same fields-complete,
  100-ranked-row recording iterations 20/21 already used and independently re-verified) under a
  throwaway directory, plus a COPIED `apps/frontend` tree (never a second `next dev` sharing the
  ambient `.next`, per `lessons.md` iter-17). Boot backend + frontend against the copy on ports
  distinct from the ambient `:8301`/`:3301` rig and the qa-rig's own CDP `:9333`, with a fresh
  `rm -rf .next` rebuild (T-9). Confirm via the serving backend process's own environment that its
  data-directory override points away from `apps/backend/.data`, and via a direct `curl` to that
  scoped backend that a rendered `/desk` value matches it byte-for-byte.
- [ ] Start the qa-rig (`project-extensions/qa-rig/xrig.sh up`); confirm it reports the isolated
  `Xvfb`/Chrome pair is up and writes `$QA_RIG_HOME/state.env`.
- [ ] Run the rig's own negative-guard check once, live, before trusting any positive result: hover
  an element that carries no matching `title` (e.g. the page's own `<h1>`) and confirm exit code `3`
  or `4` with nothing written — proves this run's rig genuinely cannot produce a false positive,
  rather than assuming the README's own verification still holds.
- [ ] Run `capture-native-tooltip.py --url http://localhost:<scoped-frontend-port>/desk
  --hover-selector '[data-testid="desk-row-drill-in"]' --require-title 'bands by class' --out
  reports/qa/goal-desk-iter-22-evidence/J-14-tooltip.png --crop-out
  reports/qa/goal-desk-iter-22-evidence/J-14-tooltip-crop.png` against the scoped rig's `/desk`
  (which serves `screen-2026-07-20-ca185294a384` as its latest screen). Confirm exit `0`, both PNGs
  written and non-empty, and the printed JSON's `title` field contains the literal substring
  `bands by class`.
- [ ] Cross-read the SAME hovered row's `title` attribute independently via a plain DOM read
  (Playwright `get_attribute`, not the rig script's own internal value) and confirm its
  `A n · B n · C n · unclassified n` counts match that row's own `bands_by_class` field in
  `screen-2026-07-20-ca185294a384.json` on disk — T-10a's own text: "A DOM read-out … is a useful
  cross-check but is NOT the artifact and never substitutes for it," so both are captured, neither
  alone.
- [ ] Tear the rig down (`xrig.sh down`) and confirm no rig process remains running on the host.
- [ ] Diff `apps/backend/.data` before/after this iteration (file list + per-file checksums);
  confirm zero new, modified, or removed files.
- [ ] Replay the required-still-passing journeys (J-04, J-05, J-07, J-12, J-13) and re-run the whole
  backend suite once (fingerprint `08e471b10130e1e2`, exactly 17 MCP tools, copy-discipline lint
  green) to confirm this iteration's zero-diff claim holds.

### New user-facing capability
None — the `bands_by_class` line already ships (iter-18/19); this iteration only photographs it.

### New information displayed
None new — this iteration captures evidence of an already-registered, already-rendered value.

### New user actions
None.

### UI surface changes
None — no `page.tsx` or component edit.

### Product surface delta
None. The product is unchanged; only its evidence trail closes one remaining gap.

### Blueprint conformance
`/desk` (Desk section, per `blueprint.md`'s Information Architecture) — no new page, no
nav-skeleton change. `blueprint.md` already registers `opposite_band`/`bands_by_class` (iter-18/19)
under their existing single owner (`desk_screen.py`) and single serving endpoint
(`GET /research/desk/screen`). A `NOTED at iter-22` documentation-currency entry has been appended
to `blueprint.md` (no new Data-Contract row, no nav-skeleton change) naming T-10a, the qa-rig, and
this capture target.

### Data-contract additions
None — no new value, owner, or endpoint. This iteration reads exclusively an already-registered
Data-Contract field (`bands_by_class`, on the "Screen snapshots, rank rows, skip rows" row).

## OUT OF SCOPE

- Any change to `page.tsx`, `deskRowDrillInTitle`, `desk_screen.py`, or any test file — this is a
  capture-only iteration; the tooltip's CONTENT is already shipped and already proven correct.
- Any real ~100-symbol top-up, real universe fetch, or real screen compute against
  `apps/backend/.data` — the scoped rig reads a COPY of an already-recorded file only; nothing new
  is fetched or computed anywhere this iteration.
- Any change to `project-extensions/qa-rig/` itself (the capture script, `xrig.sh`, its README) —
  the rig is owner-approved and owner-verified as-is; this iteration only USES it.
- Re-litigating whether the photograph is required at all, or proposing an alternative wording for
  T-10/T-14's acceptance text — the owner already ruled (T-10a): the bar stands unchanged, this rig
  is how it is met.
- `docs/goal.md`'s host-protection paragraph text tidy-up (a carried owner-track item) — not a chain
  deliverable.
- Desk-page length reduction, history-row keyboard access, or run-table pagination — real, carried
  items from prior recommendations, distinct from this iteration's one named capture; they ride
  whichever future iteration next touches `/desk`.

## DEFINITION OF DONE

- [ ] `reports/qa/goal-desk-iter-22-evidence/J-14-tooltip.png` and
  `J-14-tooltip-crop.png` exist, are non-empty, and were produced by
  `capture-native-tooltip.py` exiting `0` with a printed `title` field containing the literal
  substring `bands by class`.
- [ ] The crop image, opened directly, shows a legible tooltip popup (not blank page background)
  whose text begins `bands by class`.
- [ ] The DOM-read cross-check of the same row's `title` attribute matches that row's recorded
  `bands_by_class` counts in `screen-2026-07-20-ca185294a384.json` on disk.
- [ ] The capture ran on a fixture-scoped rig proven isolated from the owner's ambient
  `apps/backend/.data` (serving-process environment check + a direct-`curl` byte match), and that
  ambient store shows zero new/modified/removed files after the run.
- [ ] J-14 remains `passing`, with its `evidence_makeup` flag able to clear (no behavioral clause is
  reopened — only the artifact was missing).
- [ ] Required-still-passing journeys (J-04, J-05, J-07, J-12, J-13) remain green via deterministic
  replay + LLM fallback.
- [ ] No anti-goal violation introduced.
- [ ] No production code, test, or config diff (`git diff` against the pre-iteration tree is empty
  outside `docs/`, `reports/`, and `runs/`).
- [ ] The qa-rig is torn down cleanly at the end of the pass (`xrig.sh down`), leaving no rig
  process running on the host.
- [ ] Dev handoff written at `docs/handoffs/goal-desk-iter-22-dev.md` (records what was captured, on
  which rig, and confirms zero production diff — the developer role this iteration is capture
  coordination, not code).

## TESTING REQUIREMENTS

- Browser: J-14 (the tooltip capture only — its behavioral acceptance is already proven and is NOT
  re-tested here); J-04, J-05, J-07, J-12, J-13 (regression replay).
- Unit/integration: none new — the existing suite is expected to show zero diff and zero new
  failures; re-run it once to confirm.
- Error cases: none new — the one "invalid input" this iteration guards against is a false-positive
  tooltip capture, caught by re-verifying the rig's own negative-guard behavior live (TC-11) rather
  than trusting its README.

Test-first contract:

- TC-1: given `~/.cache/tapeology-qa-rig/prefix` (fetched on first use if absent), when
  `project-extensions/qa-rig/xrig.sh up` runs, then it starts `Xvfb` on `:99` plus a headed Chrome
  with CDP on `:9333`, writes a state file at `$QA_RIG_HOME/state.env`, and refuses to start if
  `:9333` already answers for a Chrome that is not the rig's own.
- TC-2: given a fresh, isolated scoped copy of `apps/backend/.data` (universe file +
  `screen-2026-07-20-ca185294a384.json` + its referenced bar series) plus a COPIED `apps/frontend`
  tree, when both are booted on ports distinct from `:8301`/`:3301`, then a direct `curl` to the
  scoped backend's `/research/desk/screen` matches the rendered `/desk` page byte-for-byte for the
  same row, and the serving backend process's own environment shows a data-directory override
  pointing away from `apps/backend/.data`.
- TC-3: given that scoped rig serving `/desk` with `screen-2026-07-20-ca185294a384` as its latest
  screen, when `capture-native-tooltip.py --url http://localhost:<scoped-frontend-port>/desk
  --hover-selector '[data-testid="desk-row-drill-in"]' --require-title 'bands by class' --out
  reports/qa/goal-desk-iter-22-evidence/J-14-tooltip.png --crop-out
  reports/qa/goal-desk-iter-22-evidence/J-14-tooltip-crop.png` runs, then it exits `0`, writes both
  PNG files non-empty, and prints a JSON object whose `title` field contains the literal substring
  `bands by class`.
- TC-4: given the written `J-14-tooltip-crop.png`, when it is opened, then it shows a visible
  tooltip popup window (not empty page background) with legible text starting `bands by class`.
- TC-5: given the hovered row's own `title` attribute, when it is cross-read directly from the DOM
  (Playwright `get_attribute`, independent of the rig script's own internal read), then its
  `A n · B n · C n · unclassified n` counts match the same row's `bands_by_class` field in
  `screen-2026-07-20-ca185294a384.json` on disk.
- TC-6: given `apps/backend/.data`, when its contents are compared before and after this iteration
  (file list + per-file checksums), then zero files are new, modified, or removed.
- TC-7: given the iteration's file changes, when `git status`/`git diff` is inspected against the
  pre-iteration tree, then it shows changes only under `docs/`, `reports/`, and `runs/` — zero diff
  to `apps/backend/app/`, `apps/frontend/`, or any test file.
- TC-8: given the required-still-passing journeys (J-04, J-05, J-07, J-12, J-13), when their golden
  replay scripts run against the ambient rig, then all report PASS with no regression.
- TC-9: given the whole backend suite, when run once during this iteration, then it passes with zero
  failures, `Config().config_fingerprint()` prints `08e471b10130e1e2`, exactly 17 MCP tools are
  counted, and `tests/test_copy_discipline.py` passes unmodified.
- TC-10: given `xrig.sh down` runs at the end of the capture pass, when the rig's `Xvfb`/Chrome
  processes and state file are checked afterward, then no rig process remains running on the host.
- TC-11: given the rig up and pointed at `/desk`, when `capture-native-tooltip.py` is run once with
  `--hover-selector 'h1'` (an element carrying no `title` containing `bands by class`), then it
  exits non-zero (`3` or `4`) and writes no PNG file — confirming this run's own rig instance cannot
  produce a false positive, live, rather than assuming the README's prior verification still holds.

## NOTES

- Binding "Do not redo" (from `iteration-state.md`, unless `docs/goal.md` changed for these
  items — for J-14 it changed only by ADDING T-10a, which does not reopen the behavioral clause):
  J-12 is COMPLETE INCLUDING ITS PICTURES — do not re-capture it. J-13/J-14 are COMPLETE IN CODE
  (fields, distance-first selection, render, tooltip line, tests, MCP proxy) — do not re-open
  `_select_opposite_band`, `_select_best_band`, or `_row_rank_key`; this iteration touches none of
  them. Never write a screen/universe snapshot or run a top-up into `apps/backend/.data`; never
  start a second `next dev` from `apps/frontend` while another runs. Zero diff stays law for
  `engine/`, `config.py`, `tradability.py`, `levels.py`, `bars.py`, `bar_index.py`,
  `desk_coverage.py`, both charts, `test_copy_discipline.py`; pin `08e471b10130e1e2`; exactly 17
  MCP tools; no `/desk` "Universe ledger"; no CLI warmer.
- `docs/goal.md`'s T-10a is the owner's own resolution of the exact contradiction that produced
  iteration 21's `STALLED` verdict (`lessons.md` iter-21: "the framework's own two rails then point
  in opposite directions"). This spec does not reinterpret T-10a — it executes it literally: the
  rig is the sanctioned mechanism, the acceptance bar (T-10) is unchanged, and the DOM read-out
  stays a cross-check, never a substitute (T-10a's own text, restated verbatim in the IN SCOPE
  bullets above).
- If this run's evidence lane again fails to use a genuinely scoped copy of `apps/backend/.data`
  (the sixth-in-a-row deviation `iteration-state.md` discloses), that is a process failure to flag
  explicitly in the results report — the spec's own instruction has not changed and does not need
  to; TC-6's before/after checksum catches it either way.
- `blueprint.md` gained a `NOTED at iter-22` documentation-currency entry (no new Data-Contract row,
  no nav-skeleton change) naming T-10a, the qa-rig, and this capture target.
- If the capture succeeds, the evaluator's own next step is to re-attempt `GOAL_ACHIEVED` — every
  other journey and every other clause of J-14 is already independently proven; this photograph was
  the session's sole remaining open item.

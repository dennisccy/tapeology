# Goal Iteration 20 — Fresh evidence-only re-check of J-07 "Graduation"

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** rapid-microscope
- **Iteration:** 20
- **Mode:** next
- **Depth:** evidence
- **Frontend Present:** yes
- **Target journeys:** J-07
- **Required-still-passing journeys:** J-08, J-10
- **Anti-goal reminders:**
  - **No execution path, ever** — no brokerage/trading API, no order tickets, no live OR paper
    trading, no "just to test" exceptions. *(critical)*
  - **No profit claims and no advice** — every $ figure is a simulated measurement carrying R,
    n, fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language,
    no imperative trading cues. *(critical)*
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five
    states and thresholds, the frozen structure computations, the JSON `BarStore`, and every
    KEPT surface's behaviour stay byte-identical. New work is additive and versioned beside
    them, never a mutation of them. *(critical)*
  - **Hold-out-only promotion** — the champion pointer moves only on a genuine hold-out
    survival through the sweep gate PLUS a valid Referee certificate. Train-only wins are
    labeled overfit. Never lower a minimum sample size, widen a gate, or pool across
    feeds/fingerprints to manufacture a survivor. *(critical)*
  - **No lookahead** — every value computed as-of T uses only events/bars fully completed at T.
    *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*
  - **Deterministic and seeded** — every random draw uses a recorded named seed via per-row
    streams; identical requests reproduce byte-identical results; no wall-clock, no unseeded
    randomness in any research artifact. *(critical)*
  - **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on
    the MCP surface can change state. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed,
    never re-tagged, never deleted, never content-perturbed. Splits are frozen at
    registration. *(critical)*
  - **Persistence stays scoped** — no ambient recording of live streams; recording/fetching
    is an explicit, logged act. *(critical)*
  - **No exploratory read of a sealed shard.** *(critical)*
  - **Sealed exposure is family-level and single-shot — never a second draw.** *(critical)*
  - **A recorded tranche is one opaque research pool until its shards are exposed.** *(critical
    — spec r5)*
  - **Evidence classes never mix.** *(critical)*
  - **No fold geometry change after fold 1** without a recorded voiding event. *(critical)*
  - **No threshold, grid, formula, embargo, or fold parameter is chosen or revised from
    validation, sealed, or holdout outcomes.** *(critical)*
  - **The denominator never shrinks.** *(critical)*
  - **The accessor is the only data door.** *(critical)*
  - **No microstructure claim beyond what L1 supports.** *(critical)*
  - **No sub-second outcome horizon** and no latency-sensitive mechanism. *(critical)*
  - **No cross-unit liquidity arithmetic.** *(critical)*
  - **No value is served before it exists.** *(critical)*
  - **The 12 pre-existing tick symbol-days are permanently exploratory.** *(critical)*
  - **The ~150-symbol-day research-readiness gate is never lowered or silently satisfied.**
    *(critical)*
  - **Referee modules are byte-untouched this era.** *(critical)*
  - **The vault secret never enters the repo, a log, a payload, or a screenshot.** *(critical)*
  - **The enhancement loop stays inside its box** — `AUTO:journeys` marker block only.
    *(critical)*
  - **Host-guard caps are law** — never disable, widen, or bypass the host's CPU/memory/task
    ceilings to make a run faster. *(critical)*

## GOAL

Produce one fresh, genuinely-discriminating browser-QA capture that re-verifies J-07
"Graduation" against the current (byte-unchanged) code, closing the only machine work this era
has left before the human-blocked items are the sole remaining gate.

## BACKGROUND

Iteration 19's evaluator was explicit and unambiguous: J-07 was verified in iteration 18 with a
capture that could genuinely have failed, but iteration 19's own wall-clock trimmer skipped its
re-check entirely (`UT-J-07 = DEFERRED-BUDGET`). `journey-history.json` already carries
`evidence_makeup: true` on J-07 for exactly this reason, and it mechanically blocks
`GOAL_ACHIEVED` until one fresh pass lands. `micro_graduation.py` and `micro_sealed_evaluation.py`
are byte-unchanged since iteration 18 (confirmed: `git status` shows both clean), so there is no
new code for a developer or reviewer to touch — this is a pure re-verification round, which is
exactly the `Depth: evidence` exception (rule 7): the prior evaluator's next-step asked ONLY for
evidence on an already-passing journey. The evaluator's depth recommendation for this iteration is
`evidence` and no escape condition holds (iter-19 verdict was CONTINUE not ESCALATE/REGRESSION,
iter-19's `coherence.md` reads COHERENCE-PASS, the hardening cadence is disabled at 0, and this is
a re-verification of an existing journey, not a brand-new full-stack one) — so `evidence` is both
recommended and binding here.

Two lessons this iteration must apply. First (iter-19 second, and reconfirmed by iter-19's own
verdict text): J-07 structurally cannot carry a stored golden replay script — `normalize_url()`
rewrites any localhost URL onto the frontend base, there is no `/research/*` proxy, and `/desk`
renders zero graduation content — so this round must NOT attempt to author one; the LLM
browser-qa lane, navigating directly to the backend's own port, is the correct and only lane by
design. Second (iter-18, both entries): a QA report must cite the actual store a browser pass ran
against by file path, never assert "real data store" from its own shell — `reports/qa-scoped-
backend-store-manifest.md` (closed iter-19, TC-9) already exists for exactly this and must simply
be cited, not re-derived.

## IN SCOPE

### Backend
- None. No production or test code changes this iteration — evidence capture only.

### Frontend (if applicable)
- None. No `.tsx`/`.ts` changes.

### New user-facing capability
None — this iteration re-verifies existing, previously-shipped behaviour. No product capability
changes.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None — zero product diff. The only artifact this iteration produces is a fresh evidence capture
(screenshot + captured JSON body) proving the already-shipped Graduation endpoint still behaves
as iteration 18 proved it does.

### Blueprint conformance
No new surfaces. J-07 re-verifies the already-registered "Graduation states (J-07)" Information
Architecture row (`state/blueprint.md`, keyless/automated — surfaces via the Scout Ledger /
Walk-Forward / Vault rows it attaches to) and the already-registered "Graduation states + export
bundles" Data Contract row (owner `micro_sealed_evaluation.py` for the verdict sub-computation,
`micro_graduation.py` for persistence/transition; serving endpoint `GET /research/desk/micro/
graduation`, unchanged).

### Data-contract additions
None.

## OUT OF SCOPE

- **Writing a stored golden replay script for J-07.** Confirmed infeasible by the iter-19 lesson
  (second entry): `normalize_url()` rewrites any localhost URL onto the frontend base, no
  `/research/*` proxy exists, and `/desk` has zero graduation content. Do not attempt this.
- **The sealed judge's economic floor / evidence-label sourcing** (iter-18/19 recommendation item
  1). Human-blocked: no revision after r9 has landed in `docs/rapid-validation-spec.md` as of
  this iteration's authoring (re-confirmed by `grep`). Leave `micro_sealed_evaluation.py`'s
  `econ_floor` untouched per the standing "Do not redo" list.
- **J-06 step 4, real Alpaca tranche recording.** Human-blocked (operator act, forbidden by every
  spec since iteration 13). Do not record real tape.
- **J-09 "The pilot studies."** Explicitly out of scope per the iter-19 evaluator's next-step
  recommendation — its answers would be graded by the same judge that still has the money-floor
  hole. Do not start it.
- **Any edit to TR-1…TR-30, `SEALED_PASS_RULE_V1`, or J-08/J-10's `iter18-qa-universe` vault
  assertions.** Per the "Do not redo" list — all settled, none need re-touching.
- **Deepening or otherwise re-touching the J-02–J-05 golden scripts.** Already fixed iteration 19;
  the "cannot-fail checks" finding is closed.
- **Any change to `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` or its seed
  scripts.** The rig is already correctly shaped for this capture (it already runs
  `seed_micro_graduation_iter18_fixture.py`); per the iter-18 lesson, ANY edit to this shared rig
  is a change to every journey it serves and would force a full replay-set re-run this round is
  explicitly sized to avoid.

## DEFINITION OF DONE

- [ ] J-07 passes via browser-qa-agent: a fresh, non-golden LLM-driven navigation directly to the
      scoped backend's `GET /research/desk/micro/graduation` (port read from `reports/qa-scoped-
      backend-store-manifest.md`, NOT hardcoded) returns a non-empty, discriminating body.
- [ ] Required-still-passing journeys J-08 and J-10 remain green via their stored golden replay
      scripts against the same scoped-backend launch (both include assertions on the
      `iter18-qa-universe` vault shard that would fail if the rig's state regressed).
- [ ] No anti-goal violation introduced (trivially satisfied — zero product diff this iteration;
      the browser-qa-agent's report must still explicitly re-confirm the vault secret never
      appears in the captured screenshot or JSON body).
- [ ] Unit tests pass; no regressions — the full backend suite is re-run and its pass/skip/fail
      counts are recorded and compared against iteration 19's own baseline (3,281 passed / 8
      skipped / 0 failed / 0 errors) to confirm the zero-diff claim is not merely assumed.
- [ ] Dev handoff written at `docs/handoffs/goal-rapid-microscope-iter-20-dev.md`, stating plainly
      that no code changed and this was an evidence-only round.

## TESTING REQUIREMENTS

- Browser: J-07 (fresh LLM-driven capture, direct backend navigation, not a stored script).
- Unit/integration: no new tests required (no code changed); the full existing suite must still
  pass at its current counts.
- Error cases: N/A — no new code path is introduced this iteration.

Test-first contract scenarios:

- TC-1: given the QA-scoped backend launcher (`qa_playbook_iter7_fixture_scoped_backend.sh`)
  running with its existing `seed_micro_graduation_iter18_fixture.py` seed applied, when
  browser-qa-agent navigates directly to `http://localhost:<port>/research/desk/micro/graduation`
  (port taken from `reports/qa-scoped-backend-store-manifest.md`'s `port:` line for this launch),
  then the response is HTTP 200 with a `families` array of length 1 whose single entry has
  `verdict: "pass"`, `n: 30`, and a `rule_hash` string that starts with `8aaea80b`.
- TC-2: given that same captured JSON body, when the browser-qa-agent (or the evaluator) recomputes
  `SEALED_PASS_RULE_V1`'s `rule_hash` fresh from the shipped `micro_sealed_evaluation.py` source
  and diffs the captured `floors_applied` object (`min_observations: 30`, `min_signal_sessions:
  "not_applicable_single_shard"`, `min_symbols: "not_applicable_single_shard"`) against the
  on-disk ledger row for the same family under the scoped rig's `TAPEOLOGY_DESK_UNIVERSE_DIR`
  (per the manifest), then the two match byte for byte, character for character.
- TC-3: given the same page load used for TC-1, when the browser-qa-agent captures the browser
  console during that navigation, then zero console errors are recorded.
- TC-4: given the fresh screenshot and JSON capture, when the resulting QA/browser report names
  which store the pass ran against, then the report cites `reports/qa-scoped-backend-store-
  manifest.md` by path (never asserts "real data store" from its own shell) — per the iter-18
  lesson.
- TC-5: given the same scoped-backend rig launch, when browser-qa-agent replays J-08's stored
  golden script (`journey-scripts/J-08.json`) and J-10's stored golden script
  (`journey-scripts/J-10.json`), then both report 0 failed steps, including J-08 step 5's and
  J-10 step 12's `iter18-qa-universe` vault-shard-name assertion.
- TC-6: given zero production files changed this iteration (`git status` shows
  `apps/backend/app/research/micro_graduation.py` and `micro_sealed_evaluation.py` clean, and
  `git diff <iter-19-snapshot-sha> -- apps/backend/app/ apps/frontend/` empty), when the full
  backend pytest suite (`.venv/bin/python -m pytest tests/ -q -p no:randomly`) is run, then it
  exits 0 with a progress-marker census matching iteration 19's own baseline: 3,281 passed, 8
  skipped, 0 failed, 0 errors.
- TC-7: given the captured screenshot and JSON body from TC-1, when a human or the auditor scans
  both for the literal vault-secret string (`TAPEOLOGY_VAULT_SECRET_FILE`'s contents), then it is
  absent from both — only the sha256 commitment ever appears, matching the standing anti-goal.

## NOTES

- This is a `Depth: evidence` round — the engine dispatches capture + evaluation only, skipping
  developer and reviewer, per the goal-decomposer's own depth rules. `Frontend Present: yes` is
  set deliberately (per the iter-18 lesson: any spec whose DoD names `browser-qa-agent` must set
  this, even when no `.tsx` file changes) so the UI/browser lane is not silently switched off.
- Applies the iter-19 (second) lesson verbatim: do not attempt to author a J-07 golden replay
  script — it is structurally impossible with the current harness, not an authoring oversight.
- Applies the iter-18 lessons verbatim: (a) a change to the shared QA rig is a change to every
  journey it serves — this round makes NO rig change, so no full replay-set re-run is required
  beyond the two-journey smoke set named above; (b) cite the store-provenance manifest by path,
  never assert "real data store" from an uninspected shell.
- Per the evaluator's iter-19 next-step recommendation: do NOT record real tape and do NOT start
  J-09 this round. Both remain human-blocked (see Active blockers in the inlined iteration state)
  and are explicitly out of scope above.
- After this round, if J-07's capture lands clean, 9 of 10 journeys are passing and J-06/J-09 are
  both fully human-blocked (the economic-floor/evidence-label ruling and the real-tape-recording
  authorisation). The evaluator should weigh whether the era is effectively stalled pending those
  two human decisions.

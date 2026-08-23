# Goal Iteration 25 — Photograph the fixed Vault, and make its opacity checkable

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** rapid-microscope
- **Iteration:** 25
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** no
- **Target journeys:** J-06
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-08, J-09, J-10
- **Anti-goal reminders:**
  - 6. **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - **No exploratory read of a sealed shard.** Event data and outcome aggregates of a `sealed` shard are refused everywhere (routes, MCP, accessor, readiness) until its recorded exposure; the refusal is typed, tested, and fail-closed. *(critical)*
  - **A recorded tranche is one opaque research pool until its shards are exposed.** No served surface — readiness, recorder progress, datasets, backtests, PnL ledger, Scout, walk-forward, graduation, MCP, UI — may present a complete identity-labelled partition of "exploratory" versus "sealed", nor a complete per-shard list of EITHER side while any pool member is unexposed; the registered universe is public by construction, so a complete list of one side identifies the other by subtraction. Unexposed pool members stay mutually indistinguishable; identity becomes public only at real exposure or assignment. The governing test is the TR-2 inference trap: given the registered universe plus every public artifact, no still-unexposed vault-eligible shard is identifiable with certainty. *(critical — spec r5)*
  - **Sealed exposure is family-level and single-shot — never a second draw.** No more than one evaluation per (family, shard) exists, ever; a failed sealed verdict is permanent and travels in every later export bundle; no perturbed re-submission resets it. *(critical)*
  - **The vault secret never enters the repo, a log, a payload, or a screenshot** — only its sha256 commitment is ever recorded. *(critical)*

## GOAL

Close J-06 from `partial` to `passing` by producing the one fresh, correct photograph of the
Validation Vault's "Sealed at" cell the repaired formatter has never been given, and by making the
long-unrunnable "a sealed row stays opaque" check actually runnable and run.

## BACKGROUND

J-06 is the ONLY non-passing journey in the era (9/10 passing per the inlined journey digest);
every other journey, including this round's regression set, is stable. Iteration 24 fixed a real
defect (the Vault "Sealed at" cell was rendering the previous calendar day plus a fabricated
20:00 ET time — `page.tsx:6807` now uses `formatDayMarker`, pinned by
`tests/test_desk_vault_sealed_at_day_marker_guard.py`) but never re-photographed the fixed cell —
the evaluator's own rule ("never green on a promise") downgraded J-06 to `partial` on that missing
evidence alone, not on any remaining defect. The iter-24 evaluator's next-step recommendation is
explicit and small: (1) restart the rig and photograph the fixed cell; (2) put one still-sealed
recording into the rig so the "gives nothing away" check — unrunnable for three rounds because the
rig's only shard is already `exposed` — can finally run, and give J-06's own golden something on
the Vault to look at (today it asserts an unrelated Microscope Readiness line, "No integrity
errors.", confirmed by reading `journey-scripts/J-06.json` directly); (3) run all nine
golden-bearing journeys through the harness, not the seven the machine happened to run last round;
(4) if time allows, de-ambiguate the two-section-collision assertion string. This iteration is
exactly that list, kept small, per the evaluator's own ordering. This is a target-selection
deviation from the usual "smallest failing journey" framing only in the sense that there is no
alternative failing journey to weigh it against (rubric point 1/3 both degenerate to J-06); no
other journey is regressed, and iter-24's coherence audit was PASS, so no consolidation is owed
either.

Depth is **lean**, per the binding evaluator recommendation for this iteration, and no escape
condition fires: the prior verdict was `CONTINUE` (not ESCALATE/REGRESSION), the prior coherence
verdict was `COHERENCE-PASS`, the hardening cadence is disabled for this session (0), and this is
not a brand-new full-stack journey — it is finishing an already-96%-built one whose remaining gap
is a fixture addition, two golden-script edits, and a re-capture. No production `vault.py` or
`page.tsx` code changes are planned; the sealed-row render branch this iteration finally exercises
(`page.tsx:6810-6819`) already shipped and is already guarded.

**Lessons applied:** (iter-24, first) narrowing a served field's precision is never backend-only —
inapplicable here since nothing changes precision or shape this round, but the same discipline
applies in reverse: confirm via `git diff` that no frontend line moves, because the sealed-row
branch this iteration exercises for the first time is pre-existing, unmodified code, not new
code the reviewer/QA lanes might assume "must have shipped with a frontend diff." (iter-22, first)
any screen/join test whose acceptable outcome includes a refusal/opacity path needs an explicit
non-vacuity assertion on the thing actually being refused — if the sealed-shard-refusal test suite
gains a case for the new fixture shard, it must assert the refusal actually fires for THIS shard,
not merely that no exception occurred. (iter-21, second) a change to the shared QA rig is a change
to every journey it serves — the new fixture shard is added to the SAME launcher every regression
journey uses, hence the wide Required-still-passing set below. (iter-20) do not copy forward a
"human-blocked" label without re-deriving it — the remaining J-06 gap (a photograph and a fixture
addition) is explicitly NOT human-blocked; nothing here needs the owner.

## IN SCOPE

### Backend
- [ ] Add one fixture-seeding step (extend an existing iter-18/iter-24-style seeder or add a small
      new one, wired into `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` after
      the existing seed steps) that plants a REAL second dataset and calls the real
      `vault.seal_shard(...)` on it — and never calls `assign_shard`/`expose_shard` — so the
      fixture rig carries at least one shard permanently in `sealed` state alongside the existing
      `exposed` one.
- [ ] Extend `journey-scripts/J-06.json` with a genuine Validation Vault assertion: expand
      `desk-section-expand-validationVault` and assert Vault-specific content (the bare-date
      "Sealed at" cell and/or the new sealed shard's opaque-row text) — not the unrelated
      Microscope Readiness line it asserts today.
- [ ] Wire `journey-scripts/J-09.json` (authored iter-24, never yet executed through the harness)
      into this iteration's replay run of the fixture-scoped rig.
- [ ] Give `journey-scripts/J-08.json` step 3 and `journey-scripts/J-10.json` step 12 a
      section-unique assertion string in place of the ambiguous shared "Ledger chain
      verification:" text (present in both the Scout Ledger and Walk-Forward sections,
      `page.tsx:6282` and `:6518`) — confirm uniqueness via grep count == 1 before committing to a
      string.
- [ ] Extend the sealed-shard-refusal test coverage (`test_vault.py` / `test_micro_accessor.py`)
      to cover the new fixture shard shape if not already fully parametric over shard identity, so
      the refusal is proven non-vacuously for THIS shard, not merely asserted absent an exception.

### Frontend
None planned. The sealed-row render branch (`page.tsx:6810-6819`) and the day-marker formatter
(`page.tsx:6807`) already shipped at iter-14/iter-24 respectively and are unmodified this round —
do not touch either (binding "Do not redo").

### New user-facing capability
None — this iteration proves and photographs already-shipped Vault behavior; it ships no new
capability.

### New information displayed
None — no new served field. The fixture rig will, for the first time, exercise an
already-existing conditional render path (`shard.exposure_state === "sealed"`) that has had no
fixture data to trigger it for three rounds.

### New user actions
None.

### UI surface changes
None — no page, component, or route changes.

### Product surface delta
None. Only QA-fixture composition (`apps/backend/scripts/`), the golden-replay scripts
(`journey-scripts/*.json`), and their test coverage change.

### Blueprint conformance
No new page or section — the Validation Vault stays at its already-registered canonical home,
`/desk` → Validation Vault (blueprint.md's Information Architecture table, J-06's row). This
iteration is QA-harness/evidence work only, matching the blueprint's own iter-19-note precedent
for harness-only changes; the blueprint gains an iter-25 note recording that, not a new IA or Data
Contract row.

### Data-contract additions
None. `sealed_at` and `exposure_state` are already-registered sub-fields of the "Vault shards,
universes, exposure ledger" row (owner `vault.py`, endpoint `GET /research/desk/micro/vault`,
blueprint.md line ~58); this iteration adds no new field, owner, or endpoint — it only adds a
second REAL shard, produced through the same already-registered `vault.seal_shard` production
function, to the fixture rig's existing pool.

## OUT OF SCOPE

- The real `.data/datasets`-backed tranche (80/80 recorded, sealed subset unchanged since iter-23)
  — do NOT re-record tape, do NOT expose/assign any real sealed shard.
- Do NOT run J-09's three studies against the real recorded corpus (irreversible; breaks J-10's
  golden per binding "Do not redo").
- The `desk_micro_readiness` MCP tool's real-store timeout (~13.5s vs. its 10s budget) — carried
  as an unchanged passenger item, not part of this round's plan (the iter-24 evaluator's next-step
  list does not name it).
- The sealed judge's money-floor ruling and the ~150-symbol-day research-readiness gate (currently
  honest-unmet at 80) — both owner-owned, both blocking no journey; untouched.
- `recording-runs.json`'s five historical `sealed_this_run` entries — stay byte-untouched per the
  iter-24 "Do not redo."
- Re-deriving or widening `stage_tr2()`'s TR-2 join model — already closed at iter-24, not
  reopened; the new fixture shard here is a browser-evidence addition to a DIFFERENT (throwaway
  QA) universe, not a change to the real tranche's own TR-2 check.

## DEFINITION OF DONE

- [ ] J-06 passes via browser-qa-agent: a fresh screenshot shows the existing shard's "Sealed at"
      cell as a bare date with no clock time, AND a fresh screenshot shows the new still-sealed
      shard's row rendering opaque (no symbol/date/dataset id).
- [ ] `journey-scripts/J-06.json` carries a genuine Validation Vault assertion and passes via
      `demo_runner.py --mode verify` against the rebuilt fixture-scoped rig.
- [ ] All nine golden-bearing journeys (J-01, J-02, J-03, J-04, J-05, J-06, J-08, J-09, J-10) are
      executed through the harness this round — not claimed from a prior or dev-local run — and
      recorded in `reports/phase-goal-rapid-microscope-iter-25-regression-replay-results.md`.
- [ ] `journey-scripts/J-08.json` step 3 and `journey-scripts/J-10.json` step 12 assert
      section-unique strings and remain order-independent.
- [ ] No anti-goal violation introduced: the new fixture shard's event data and identity stay
      refused everywhere outside the Vault's own opaque projection; TR-2/TR-4-class refusal
      behavior is proven non-vacuously against it.
- [ ] Unit tests pass; no regressions (full backend suite green, count >= iter-24 baseline).
- [ ] Dev handoff written at `docs/handoffs/goal-rapid-microscope-iter-25-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-06 (Vault "Sealed at" bare-date cell + new sealed shard's opaque row), plus the
  Required-still-passing set (J-01, J-02, J-03, J-04, J-05, J-08, J-09, J-10) via deterministic
  replay, with LLM fallback for anything without a fresh golden.
- Unit/integration: sealed-shard refusal coverage (`test_vault.py`/`test_micro_accessor.py`)
  extended for the new fixture shard's identity; full backend suite run.
- Error cases: an attempted read of the new sealed shard's event data or identity through any
  non-Vault surface (dataset listing, accessor, MCP, readiness per-shard enumeration) must be
  refused exactly as every other sealed shard's refusal is already tested.

- TC-1: given the fixture-scoped QA rig's seeding step plants a second real dataset and calls
  `vault.seal_shard(...)` on it without ever calling `assign_shard`/`expose_shard`, when
  `GET /research/desk/micro/vault` is queried on that rig, then the response lists this shard with
  `exposure_state == "sealed"` and no `symbol`/`session_date`/`dataset_id`/`family_root_id` field
  populated (opaque projection only).
- TC-2: given the rig from TC-1 with a freshly rebuilt frontend (`rm -rf apps/frontend/.next` +
  rebuild + restart, per T-9), when the QA agent navigates to `/desk` and expands "Validation
  Vault", then a screenshot shows the new sealed shard's row rendering the literal text
  "sealed — opaque" across the Dataset/Family root/Symbol/Session date/Assigned at/Exposed
  at/Content checksum columns.
- TC-3: given the same rig and page state as TC-2, when the screenshot captures the pre-existing
  exposed shard's "Sealed at" column cell, then it reads a bare date string (e.g. `2026-05-01`)
  containing no `T` character, no colon, and no clock time.
- TC-4: given `journey-scripts/J-06.json` is extended with a step that expands
  `desk-section-expand-validationVault` and asserts Vault-specific text, when
  `demo_runner.py --mode verify` replays J-06.json against the rebuilt fixture-scoped rig, then
  all steps PASS.
- TC-5: given `journey-scripts/J-09.json` (authored iter-24, never executed through the harness)
  is added to this iteration's replay run, when it is executed via
  `demo_runner.py --mode verify`, then it PASSES and the run is recorded in
  `reports/phase-goal-rapid-microscope-iter-25-regression-replay-results.md`.
- TC-6: given `journey-scripts/J-08.json` step 3 and `journey-scripts/J-10.json` step 12 both
  currently assert the shared string "Ledger chain verification:" (present in both the Scout
  Ledger and Walk-Forward sections), when each is edited to assert a string confirmed unique to
  its own section (grep count == 1 in `apps/frontend/app/desk/page.tsx`), then both scripts
  continue to PASS via `demo_runner.py --mode verify`, and a deliberate skip-then-restore proof of
  the developer's own choosing shows each assertion now fails if its own section's expand step is
  skipped.
- TC-7: given all nine golden-bearing journeys (J-01, J-02, J-03, J-04, J-05, J-06, J-08, J-09,
  J-10) are replayed via `demo_runner.py --mode verify` against the fixture-scoped rig in one run,
  when the run completes, then all nine report PASS with zero regressions.
- TC-8: given the new still-sealed fixture shard from TC-1 exists on the rig, when any non-Vault
  surface (dataset listing route, MCP proxy, readiness per-shard enumeration, direct accessor
  read) is queried for that shard's identity or event data on that rig, then the request is
  refused exactly as every other sealed shard's already-tested refusal behavior, proven
  non-vacuously (the test asserts the refusal actually fired for THIS shard's id, not merely that
  no exception occurred).
- TC-9: given the full backend test suite including any new/extended unit tests from this
  iteration, when `pytest` runs, then it reports zero failures and a pass count at or above the
  iter-24 baseline.

## NOTES

- The eval log's own words for why this is small and final for J-06: "this is the round that would
  finally certify the era" — but per the iter-24 evaluator's own explicit statement, none of its
  decision rules fire for ESCALATE here (no journey has failed twice running, review passed, and
  iter-24 was already a heavy round); this iteration follows that reasoning and plans lean.
- If the owner wants the independent checker present for the round that would finally certify the
  era, the evaluator already named the correct lever in its iter-24 reasoning: `CHAIN_REQUIRE_FULL_DEPTH`,
  set by the owner for a specific run — not a self-written `Depth enforcement:` line in this spec.
- Read `page.tsx:6801-6819`'s own comment before touching the sealed-row branch or the day-marker
  formatter — both explain, in place, exactly why they read the way they do; do not re-derive.
- The `desk_micro_readiness` MCP timeout is a real, felt gap (nothing currently fixes it) but is
  explicitly deferred — it does not block J-06 or any other journey, and the iter-24 evaluator's
  own next-step ordering does not name it as this round's work.

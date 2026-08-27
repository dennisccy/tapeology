# Goal Session hypothesis-foundry — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-0 — 2026-08-26T20:30:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration that needs browser evidence (i.e. all of them) — and any future
science-contract revision (r15+) that adds a required field, which should sweep
`apps/backend/scripts/seed_*_fixture.py` in the same commit.

## iter-1 — 2026-08-26T21:55:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** every future iteration whose journey evidence is a Foundry read surface over a
recorded artifact — J-01 step 5, J-02, J-04, J-06, J-07, J-08 — and to any QA-rig provisioning work.

## iter-2 — 2026-08-26T23:05:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose spec sets a full-depth trigger, and any evaluator deciding
between CONTINUE-with-`full`-recommendation and ESCALATE.
**Applies to:** every future Foundry journey whose evidence is a read surface over a recorded
artifact — J-02, J-04, J-06, J-07, J-08.

## iter-3 — 2026-08-27T00:40:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose Definition of Done claims an END-TO-END path across modules —
grep for the producing function's name in the consuming test and confirm the object actually crosses
the boundary, rather than trusting a test name or a handoff sentence. Also: never demote a
spec-declared `full` depth on an iteration whose own trigger names a cross-module seam.

## iter-3 — 2026-08-27T00:41:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any crash/resume/cache-invalidation test — ask what state the simulated failure
actually destroys, and whether the mechanism named in the assertion exists at all. Carry this into
J-06/J-07 rather than treating checkpoint safety as already proven.

## iter-4 — 2026-08-27T03:05:00Z

**Verdict:** ESCALATE
**Lesson:** A depth *recommendation* is not binding — the engine's depth arbiter grants FULL only
after a prior **ESCALATE verdict**, and demotes a spec-declared `Depth: full` to lean on any budget
breach (engine.log 21:47:43 iter-2, 00:47:55 iter-4; contrast 23:07:44 "FULL pass granted (reason:
prior-verdict-ESCALATE)"). Every iteration of this session has breached the 3600s budget, so
recommending `full` from a CONTINUE verdict is a guaranteed no-op: if the next iteration genuinely
needs an auditor, the verdict itself must be ESCALATE.
**Applies to:** any goal-mode iteration whose spec declares `Depth: full` in a session that is
routinely over the wall-clock budget.

## iter-4 — 2026-08-27T03:05:00Z

**Verdict:** ESCALATE
**Lesson:** A read surface can pass its own tests while still failing the journey, because the tests
assert the *payload* and the journey asserts the *screen*. Three separate gaps this iteration were
invisible to a green suite: `sources_compiler` carries `operative_formula_refs`/`superseded_fields`/
`aliases_lineage_ids` but `SourcesCompilerSubsection` never renders them; `hermetic_oracles` proves
the Scout-kill→`foundry_state` mapping in code but exposes no per-row state to render; `freeze_record`
pins the manifest/source/spec/config identities in `build_freeze_record` but the subview drops them.
When a journey step enumerates fields to "confirm each record shows", diff that list against the JSX,
not against the payload schema.
**Applies to:** any iteration building a read surface whose acceptance steps enumerate fields.

## iter-5 — 2026-08-27T07:10:00Z

**Verdict:** ESCALATE
**Lesson:** The era's single irreplaceable artefact (`docs/hypothesis-foundry/*.json`, one commit,
no second epoch permitted) shipped with ZERO automated coverage — nothing in 3,879 tests would have
noticed a hand-edited disposition, a dropped `audit_note`, or the five files leaving `HEAD`. Only the
hard auditor caught it (B4) and wrote `tests/test_foundry_real_epoch_artifacts.py`. Related trap in
the same file: `lint_quoted_spans` verifies a span against its OWN record's `source_excerpt`, and
`source_hash` is `sha256(source_excerpt)` — both sides authored by the same agent, so a "citation
lint" proved nothing about the cited file until a cross-file test was added.
**Applies to:** any iteration that writes a one-time, non-regenerable artefact (freeze sets,
manifests, registries, epoch records) — require a read-only guard test over the committed bytes IN
THE SAME iteration, and check that any self-consistency lint actually reaches the external source it
claims to verify.

## iter-5 — 2026-08-27T07:10:00Z (second)

**Verdict:** ESCALATE
**Lesson:** A "one and only one X" rule enforced by *the presence of a state file* is not enforced at
all: `_load_existing_manifest_store` returns `{}` when `epoch-manifest.json` is absent, so deleting
that file silently bypasses `ManifestDriftRefused` and mints a fresh `epoch_id`. That is exactly how a
first real epoch was minted and discarded this iteration (auditor B5) — honestly disclosed, but the
uniqueness guarantee was mechanical in name only.
**Applies to:** any uniqueness/idempotency guard in this codebase (`generate_or_verify_manifest`,
freeze-set verification, first-read locks) — the guard must key on something that cannot be removed
by deleting a file, and the evaluator should test the delete-then-regenerate path, not just the
drifted-input path.

## iter-6 — 2026-08-27T11:40:00Z

**Verdict:** CONTINUE
**Lesson:** Writing a one-way freeze lock turns ordinary code-quality findings into permanent
scars: the moment `record_epoch_open` pinned `runner_hash`/`freeze_set_hash` (2026-08-27T06:55:51Z),
every one of the 59 files in `docs/hypothesis-foundry/freeze-set.json` became uneditable — including
`apps/backend/scripts/run_hypothesis_foundry_real_exhaust.py`, which the SAME iteration's coherence
audit then told us to edit to fix a duplicate-computation FAIL. The iteration created the defect and
sealed away its own fix in one run. The ordering rule to carry forward: run coherence + a duplicate-
computation sweep over the candidate freeze set BEFORE the lock is written, never in the same
iteration as the lock, and prefer keeping new CLIs OUT of the freeze set unless the spec truly
requires them.
**Applies to:** any iteration that writes a one-way lock, freeze set, or immutable manifest — and
specifically iter-7's attempt to resolve this coherence FAIL.

## iter-6 — 2026-08-27T11:40:00Z (second)

**Verdict:** CONTINUE
**Lesson:** The QA report's own four cited "proof" screenshots
(`reports/qa/goal-hypothesis-foundry-iter-6-*.png`) were one byte-identical 9,344-byte blank image
reused four times, while the browser-QA lane's `-evidence/UT-*.png` captures were genuine — the hard
auditor caught it (T1) because it compared md5s rather than reading the filenames. A QA report citing
N distinct views should never resolve to one file; check sizes/hashes before treating a QA citation
as evidence, and read journey proof off the `-evidence/` lane.
**Applies to:** any iteration where the QA report and the browser-QA lane both claim to cover the
same new surface.

## iter-7 — 2026-08-27T12:55:00Z

**Verdict:** ESCALATE
**Lesson:** A "Frontend Present: no" iteration is NOT a no-browser iteration. QA read that flag as
permission to record "Browser Checks: SKIPPED" while still certifying "Definition of Done ✓
Complete" — and the browser lane that *did* run covered only the regression set J-01..J-06 and
never replayed J-07, the iteration's own TARGET journey, which DoD item 4 and TC-4 both demanded.
`status.json` carried `browser_checks_run: false` on top of it. Only the hard auditor caught it
(`docs/handoffs/goal-hypothesis-foundry-iter-7-audit.md` F1). The flag governs whether the developer
edits `apps/frontend/**`; it never waives a spec that mandates re-replaying journeys because the
diff touched the one shared serving module behind all of them.
**Applies to:** any backend-only iteration whose spec still lists Target journeys or a
Required-still-passing set — the target journey must be replayed regardless of the frontend flag.

## iter-7 — 2026-08-27T12:56:00Z

**Verdict:** ESCALATE
**Lesson:** An equivalence-pinning test written against a permanently-empty collection is a
tautology, and calling it drift protection is wrong in mechanism even when right in conclusion.
`test_frozen_ready_total_sealed_cli_formula_agrees_with_the_canonical_helper` compares the sealed
CLI's `sum(len(fm.get("variants", [])) …)` against `micro_routes.compute_frozen_ready_total`'s
`sum(f["variant_count"] …)` on a manifest whose `families` is `[]`, so both return `0` for *any*
pair of formulas. The evaluator ran both on synthetic input: `[{variant_count:25, variants:[]}]`
gives 25 vs 0, and `[{variants:["a","b"]}]` gives `KeyError` vs 2. What actually prevents divergence
is that both operands are sha256-pinned `freeze-set.json` entries — the freeze-set is the guard, not
the test.
**Applies to:** any consolidation that "pins" two implementations with a test; check the fixture is
non-degenerate before claiming the test detects drift, and say plainly which mechanism supplies the
guarantee.

## iter-7 — 2026-08-27T12:57:00Z

**Verdict:** ESCALATE
**Lesson:** The Chrome-MCP deep-scroll capture path reliably returns solid-navy blank PNGs for the
`/desk` Foundry accordion subsections — four of this iteration's evidence files are the *same* blank
image (md5 `5167f380a66763a1219c996433733438`), reproduced independently by the auditor even after
viewport enlargement to 1400×2400 and a `scrollIntoView` confirmed in-viewport by
`getBoundingClientRect()`. The deterministic replay lane (`demo_runner --mode verify`) does NOT
suffer this: it produced a normal 147 KB render of the same page. This is now the second consecutive
iteration bitten by blank Foundry captures.
**Applies to:** any iteration capturing evidence for a `/desk` collapsible subsection — take the
screenshot through `demo_runner --mode verify`, not the Chrome-MCP screenshot tool.

## iter-8 — 2026-08-27T17:05:00Z

**Verdict:** STALLED
**Lesson:** When the hard auditor APPLIES a product fix during its own pass, every screenshot the
browser-QA lane already captured is stale by one change — here `apps/frontend/app/desk/page.tsx` moved
at 16:25 while all evidence PNGs were taken at 16:08, so the shipped Final Summary carried an honesty
caveat that no filed screenshot showed. Re-run `demo_runner --mode verify` yourself after any
audit-applied fix and file your own capture; do not certify a journey on a picture that predates the
last product edit.
**Applies to:** any full-depth iteration whose audit report has a non-empty "Fixes Applied During This
Audit" section touching frontend or route code.

## iter-8 — 2026-08-27T17:06:00Z

**Verdict:** STALLED
**Lesson:** A walkthrough recording can report `RECORDED_WITH_NOTES` and look complete while showing
entirely the wrong page: this iteration's demo script clicked `desk-section-expand-*` testids that do
not exist anywhere in `apps/frontend/app/desk/page.tsx`, all 7 clicks silently failed, and every step
screenshot captured the top of `/desk` instead of the Foundry panel. The golden journey scripts use
different, real selectors and replayed 8/8 green — so check the demo script's selectors against the
golden scripts, not against the spec text, before trusting a recording as showcase evidence.
**Applies to:** any iteration whose demo-results file carries "couldn't perform click (unresolvable
target ...)" soft notes.

## iter-9 — 2026-08-27T21:55:00Z

**Verdict:** GOAL_ACHIEVED
**Lesson:** Two capture-script traps surfaced together and neither is what the prose said it was.
(1) `reports/phase-goal-hypothesis-foundry-iter-8-demo-results.md` blamed missing
`desk-section-expand-*` testids; the real cause is a wrong target-key SHAPE in the walkthrough
script — `{"data-testid": ...}` instead of the `{"testid": ...}` `demo_runner.py` resolves
(`lib/demo_runner.py:117`). The testids exist and are generated dynamically at
`apps/frontend/components/CollapsibleSection.tsx:45`, so grepping `app/desk/page.tsx` for them
always returns 0 and always misleads. (2) `tests/test_tick_recorder.py::test_tr31_format_cli_
progress_line_serves_only_the_whitelisted_aggregates` asserts forbidden digit substrings against a
string that embeds real wall-clock elapsed seconds measured from a fixed 2026-06-01 literal — a
calendar-dependent time-bomb that will flake harder every month.
**Applies to:** any iteration writing or debugging a `demo_runner.py` script (golden replay or
walkthrough) — verify the target key against `resolve_spec`, and never conclude a testid is
missing from a grep of the page file alone; and any iteration triaging a "flaky, unrelated" test
claim in a dev handoff — reproduce the mechanism live before accepting or rejecting it.

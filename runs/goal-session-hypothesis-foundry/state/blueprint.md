# App Blueprint — hypothesis-foundry

<!--
This is the coherence contract for the whole app. The goal-decomposer drafts it at baseline; the
human approves it once (auto-approved by default for this run); the coherence-auditor enforces it
every iteration.

Written at iter-0 (baseline). This era builds ADDITIVELY on the product left by prior eras: Cockpit
`/` + Structure `/structure` + Desk `/desk` (Era B "The Desk" + "Playbook" + "Rapid Microscope"),
config fingerprint `08e471b10130e1e2`. Confirmed live on the current tree at baseline time:
- `apps/frontend/app/desk/page.tsx` exists with an established `<section aria-label="...">` pattern
  (Screen History, Forward Returns, Provenance, Playbook Signals, Referee Registry/Adjudications/
  Runs, Microscope Readiness, Scout Ledger, Walk-Forward, Validation Vault, Graduation, Feature
  Snapshots, etc.).
- `apps/backend/app/research/micro_routes.py` owns the existing `/research/desk/micro/*` prefix
  (Rapid Microscope era: readiness, snapshots, scout compute, recorder, walkforward, etc.) — GET
  routes never compute (established page-load-never-computes convention this era inherits).
- NOTHING under `docs/hypothesis-foundry/`, no `app/research/foundry_*.py` module, and no
  "Hypothesis Foundry" section on `/desk` exist yet — this era's entire surface is unbuilt as of
  iter-0. The era-transition paperwork (archived predecessor goal, dated opening note in
  `docs/research-directions.md`, `project-extensions/proposer-guidance.md` absent so the two-file
  proposer opt-in is unsatisfied) was already done before this session opened.

Updated at iter-1: rows 1-3 of the Data Contract table below are now partially SHIPPED (module
names finalized, "(planned)" removed where real) — see the iteration note under the table.

Updated at iter-2: rows 3-8's computing modules move from "(planned)" to real, hermetically proven
implementations (`foundry_interpreter.py`, `foundry_family.py`, `foundry_freeze.py`,
`foundry_ledger.py`, `foundry_runner.py`) — see the iteration note under the table. No row added, no
IA/nav change; no `blueprint.reapproval-requested` needed.

Updated at iter-3: the same rows 2/7/8's already-registered computing modules
(`foundry_source_registry.py`, `foundry_runner.py`, `foundry_ledger.py`) gained a hermetic
“complete factory” oracle-suite proof (composite multi-outcome epoch, all-blocked, all-
killed, multi-survivor, large-scale checkpoint/resume, protected-data-trip/evidence-class-
immutability) plus two schema fields (`SourceRecord.source_hash`,
`SourceRecord.alternatives`) and a resume-identity integrity fix — see the iteration note
under the table. No row added, no IA/nav change; no `blueprint.reapproval-requested`
needed.

Updated at iter-5 (planned): adds one new Data Contract row (`epoch_manifest`, the real non-fixture
counterpart to rows 2-5, targeting J-06) and extends the already-registered `hermetic_oracles` row
with two new fields (`kill_type_mapping`, `best_of_n_disclosure`, targeting J-05's remaining gap).
Both are additive — same reused modules, same single endpoint — no IA/nav change, no
`blueprint.reapproval-requested` needed. See the iteration note under the table.


Updated at iter-6 (planned): adds one new Data Contract row (`exhaust_progress`, real J-07
runner/first-read-lock/checkpoint state over the already-committed real epoch) and one new
`/desk` → Hypothesis Foundry subsection ("Runner / Checkpoint", home already registered at
baseline). Additive only — reuses `foundry_runner.py`/`foundry_ledger.py`, same single endpoint,
no IA/nav change, no `blueprint.reapproval-requested` needed. See the iteration note under the
table.
-->

## Information Architecture

**Layout shell:** persistent top nav bar + main content area (unchanged this era).

**Navigation skeleton** (current state; Foundry adds no new top-level route):

```
Tapeology
├── Cockpit      /             live/sim/historical tape watch — UNCHANGED this era
├── Structure    /structure    bars, levels/zones, tradable map, edge report, strategy registry —
│                               UNCHANGED this era
└── Desk         /desk         existing Rapid-Microscope-era sections (Screen History, Forward
                                Returns, Provenance, Playbook Signals, Referee Registry/
                                Adjudications/Runs, Microscope Readiness, Scout Ledger,
                                Walk-Forward, Validation Vault, Graduation, Feature Snapshots, ...)
                                — all UNCHANGED this era.
                                **Hypothesis Foundry** — a new
                                `<section aria-label="Hypothesis Foundry">` appended BELOW the
                                existing shipped sections, using its own new `data-testid` family
                                (`foundry-*`), per `docs/goal.md` Product Shape: "No dedicated
                                mutation page is introduced. The Foundry surface is read-only."
                                iter-1 shipped the panel HEADER (era identity + era-open
                                baseline). iter-4 additionally ships four fixture-scope subsections
                                below the header — Sources/Compiler, Interpreter fixtures, Freeze/
                                Integrity, Hermetic Oracles — each a HERMETIC/FIXTURE demonstration
                                of the already-built compiler/interpreter/family/freeze/ledger
                                machinery, visibly labelled as fixture-scope and distinct from the
                                header's real era-open baseline. The real Epoch/Manifest subsection
                                (J-06) is PLANNED for iter-5 (real, non-fixture source registry +
                                family/variant manifest + freeze identity, read from the Git-tracked
                                `docs/hypothesis-foundry/` artifacts — see Data Contract below);
                                Runner/Checkpoint (J-07) is PLANNED for iter-6 (real, non-fixture
                                first-read-lock + checkpoint/exhaustion state over the already-
                                committed real epoch, including a freeze-set/freeze-record
                                bookkeeping repair pass that must precede the lock — see Data
                                Contract below).
```

**Feature / journey homes** (each reachable in ≤2 clicks from the nav):

| Feature / journey | Canonical home (route) | Nav section |
|---|---|---|
| J-01 Era transition / proposer-inactive banner | `/desk` → Hypothesis Foundry panel header | Desk |
| J-02 Sources / Compiler fixture view (CandidateSpec detail) | `/desk` → Hypothesis Foundry → Sources/Compiler | Desk |
| J-03 Generic interpreter equivalence fixture views | `/desk` → Hypothesis Foundry → Interpreter fixtures | Desk |
| J-04 Family/denominator/freeze-barrier/integrity fixture views | `/desk` → Hypothesis Foundry → Freeze/Integrity | Desk |
| J-05 Hermetic oracle summary | `/desk` → Hypothesis Foundry → Hermetic Oracles | Desk |
| J-06 Real epoch / manifest (post-freeze) | `/desk` → Hypothesis Foundry → Epoch / Manifest | Desk |
| J-07 Exhaust runner checkpoint/progress | `/desk` → Hypothesis Foundry → Runner / Checkpoint | Desk |
| J-08 Final Foundry truth (source/epoch/family/variant/integrity summary + detail drill-in) | `/desk` → Hypothesis Foundry (top-level summary + detail view) | Desk |

No new page is introduced anywhere in this era; every journey's home is a subsection of the single
new `/desk` → `Hypothesis Foundry` panel.

## Data Contract

Single canonical REST owner for every Foundry-displayed value, per `docs/goal.md` Product Shape:
`GET /research/desk/micro/foundry`. It may expose named subviews (sources, epoch/manifest, family/
variant, runner/checkpoint) only if every subview still reads from this same one backend read
model — no second calculation or fetch path. Exact backend module split is finalized here at the
iteration that first ships each row (see iteration note below the table).

| Value / entity | Computed by (single module/function) | Served by (single endpoint) | Notes |
|---|---|---|---|
| Era/session identity, methodology/spec version, source-registry hash | `app/research/foundry_source_registry.py` | `GET /research/desk/micro/foundry` | era-open baseline (full-suite pass/skip, config fingerprint, Referee-module SHA-256) is part of this bundle; `source_registry_hash` stays `null`/`not_yet_generated` until the real registry exists (Binding Order step 6 / J-06, planned iter-5) |
| Source dispositions + lineage/alias refs (one of the closed §7.1 vocabulary per required source object) | `app/research/foundry_source_registry.py` | `GET /research/desk/micro/foundry` | no required source may be silently absent; iter-1 proves the compile RULES on 7 hermetic fixture source types only — the REAL 11 required-source-object registry content is planned to ship at iter-5 (J-06), served under the new `epoch_manifest` key below |
| Per-variant `CandidateSpec` + `candidate_spec_hash` + population/coordinate/direction/horizon summary | `app/research/foundry_compiler.py` (fixture-compilable candidates) + `app/research/foundry_interpreter.py` (owns deferred/population resolution; ships hermetically at iter-2 for J-03 fixtures) | `GET /research/desk/micro/foundry` | every §3 science-affecting field must move the hash |
| Epoch id, manifest hash, freeze commit, freeze integrity verdict, first-outcome-read boundary status/time | `app/research/foundry_freeze.py` (ships hermetically at iter-2; real epoch/commit values planned at iter-5 under `epoch_manifest`, J-06) | `GET /research/desk/micro/foundry` | freeze-set = enumerated checked-in path+sha256 manifest, not an adjective |
| Family/variant counts, family order, variant ordinals, per-family frozen denominator, blocked/excluded/aliased counts by reason | `app/research/foundry_family.py` (ships hermetically at iter-2) | `GET /research/desk/micro/foundry` | denominator frozen pre-outcome; over-cap blocks whole; real values planned at iter-5 under `epoch_manifest` |
| Unresolved-deferred counts, eligible resolved anchors, candidate/comparator counts, usable sessions, evidence class | `app/research/foundry_interpreter.py` (ships hermetically at iter-2) | `GET /research/desk/micro/foundry` | population symmetry per §4.1 |
| Materialized econ floor + unit/provenance, Scout decision, p-screen/effect-bps/concentration/economic/fragility disclosures, best-of-N disclosure, `DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN` state | `app/research/foundry_runner.py` calling the unchanged `scout.screen_candidate` (ships hermetically at iter-2 for fixture candidates; real corpus/econ-floor materialization still awaits J-07) | `GET /research/desk/micro/foundry` | Foundry never adds a second statistical rail; values are the verbatim Scout screen payload |
| Protected/withheld/sealed ids read by the real Foundry runner (must be zero; identity-safe aggregate only) | `app/research/foundry_runner.py` (module ships hermetically at iter-2; real protected-access census still awaits J-07) | `GET /research/desk/micro/foundry` | never sealed identities, joins the existing TR-2-style inference sweep |
| Current runner checkpoint / next manifest ordinal, ledger chain/integrity verification | `app/research/foundry_ledger.py` (ships hermetically at iter-2) | `GET /research/desk/micro/foundry` | Foundry's own hash-chained append-only trial ledger; never registered into the Scout ledger |
| `sources_compiler` (7→8 hermetic J-02 source fixtures + compiled `CandidateSpec`/block reason + outcome-noise immutability proof) | `app/research/foundry_source_registry.py` + `app/research/foundry_compiler.py` (reused, no new module) | `GET /research/desk/micro/foundry` (`sources_compiler` key) | shipped iter-4; fixture-scope only, visibly labelled distinct from any future real registry (J-06); iter-5 (planned) surfaces both sibling records of the two-variant alias family (was 7 entries with 1 sibling implicit via `alternatives`, becomes 8 with both explicit) plus renders `operative_formula_refs`/`superseded_fields`/`aliases_lineage_ids` (already-computed fields, frontend-only fix) |
| `interpreter_fixtures` (5 hermetic J-03 interpreter scenarios: immediate-scalar equivalence, conjunction, deferred `refill_consistent`, mirrored direction, unsupported-relation block) | `app/research/foundry_interpreter.py` (reused, no new module) | `GET /research/desk/micro/foundry` (`interpreter_fixtures` key) | ships iter-4; fixture-scope only |
| `freeze_integrity` (family denominator fixtures, late-insertion refusal, generation replay verify/drift-refusal, fixture freeze record/freeze-set schema, first-read-lock + hash-drift + non-science-file exemption, replay idempotence/conflict/single-flight) | `app/research/foundry_family.py` + `app/research/foundry_freeze.py` + `app/research/foundry_ledger.py` (reused, no new module) | `GET /research/desk/micro/foundry` (`freeze_integrity` key) | ships iter-4; fixture-scope only — `freeze_record.freeze_set_target_path` NAMES the real `docs/hypothesis-foundry/freeze-set.json` path without that file existing yet (see `state/assumptions.md` iter-4); iter-5 (planned) is when that path is expected to start existing for real, via the separate `epoch_manifest` key, not this one |
| `hermetic_oracles` (composite multi-outcome-type epoch coverage + all-blocked/all-killed/multi-survivor/crash-resume-at-scale/protected-data-trip/evidence-class-immutability pass/fail summary; **+ `kill_type_mapping` / `best_of_n_disclosure`, planned iter-5**) | `app/research/foundry_hermetic_summary.py` — a thin summary builder over `apps/backend/tests/test_foundry_hermetic_epoch.py`'s existing hermetic suite; introduces no second oracle implementation (reused, no new module for the iter-5 fields) | `GET /research/desk/micro/foundry` (`hermetic_oracles` key) | shipped iter-4; precomputed once (module-level cache or checked-in snapshot), never recomputed per request, per the router's established GET-never-computes convention. iter-5 (planned) adds `kill_type_mapping: list[{outcome_label, foundry_state}]` (real per-row read, closing the "outcome_types_present is a hard-coded label dict" gap) and `best_of_n_disclosure: {n_variants_tried, threshold_bps}` (sourced from the existing per-row `screen_result.best_of_n_disclosure`); also removes the two open-anti-goal `scout._two_sided_p` reassignments from this module's serving-process code path |
| `epoch_manifest` (**NEW row, planned iter-5, targets J-06**) — real, non-fixture per-source disposition list for all 11 required source objects; real family/variant manifest with denominators/`candidate_spec_hash`/future `rule_id`/`prospective_root_status`; freeze identity `epoch_id`/`source_registry_hash`/`manifest_hash`/`freeze_set_hash`/`freeze_commit`; `outcome_access_census`; `source_registry_audit` report reference | `app/research/foundry_source_registry.py` + `app/research/foundry_compiler.py` + `app/research/foundry_family.py` + `app/research/foundry_freeze.py` (ALL reused, no new module) — reads the literal Git-tracked `docs/hypothesis-foundry/*.json` / `reports/hypothesis-foundry/source-registry-audit.md` paths directly, never through `get_foundry_dir()`/`resolve_foundry_dir()` (that resolver is reserved for the runtime-scoped era-open baseline / trial ledger per §8.2's tracked-vs-runtime split) | `GET /research/desk/micro/foundry` (`epoch_manifest` key) | the REAL non-fixture counterpart to the rows above; at most one real `epoch_id` may ever exist for this era (§8.1); visibly labelled distinct from the four fixture-scope subsections; also becomes the real source for the top-level `source_registry_hash`/`source_registry_status` fields `get_foundry()` already stubs today (no second calculation path for those two fields once real) |
| `exhaust_progress` (**NEW row, planned iter-6, targets J-07**) — real first-read-lock status/timestamp; resolved eligible-corpus `(dataset_id, checksum)` manifest hash; total/terminal `FROZEN_READY` variant counts (0/0 for this epoch); current checkpoint ordinal; protected/withheld/sealed read census (must be zero); single-flight status; freeze-integrity verdict; honest exhaust-complete flag | `app/research/foundry_runner.py` + `app/research/foundry_ledger.py` (reused; `foundry_ledger.py` gains one additive epoch-opening row-kind method alongside its existing `record_intent`/`record_terminal`, no new module, no second ledger) | `GET /research/desk/micro/foundry` (`exhaust_progress` key) | reads the REAL trial ledger under the already-committed real `epoch_id`; zero compiled candidates makes exhaustion vacuous but the first-read-lock row is still written once, per §8.5, before this key can report anything but `not_yet_run` |

**Iteration note (iter-1):** shipped for real — the `GET /research/desk/micro/foundry` route itself
(new, mounted on the existing `micro_routes.py` router, GET-only / never-computes); row 1's era
identity + era-open baseline (static one-time snapshot, not recomputed per request); row 2's owner
meta-policy compile RULES + exact-quote lint, proven on 7 hermetic fixture source records (not the
real 11 required source objects); row 3's `CandidateSpec` schema + `candidate_spec_hash` for the
subset of fixtures that compile directly (no deferred/population resolution — that still needs the
not-yet-built `foundry_interpreter.py`). No UI subsection beyond the panel header ships this
iteration; the Sources/Compiler fixture view (and all other subviews) ship together in a later
consolidated read-surface iteration per `docs/goal.md` Binding Execution Order step 5.

**Iteration note (iter-2):** shipped for real, hermetically — `foundry_interpreter.py` (generic
population resolution + boolean-membership projection + Scout-boundary adapter calling
`scout.screen_candidate` directly, proven byte-identical to the existing direct scalar path on
fixtures); `foundry_family.py` (pre-outcome family denominator, hard-cap block, late-insertion
refusal); `foundry_freeze.py` (deterministic manifest generation/replay, freeze-set + freeze-record
construction, first-read-lock hash-drift simulation); `foundry_ledger.py` (hash-chained append-only
trial ledger, checkpoint/resume, single-flight, replay idempotence, deterministic `rule_id` +
`prospective_root_status`); `foundry_runner.py` (canonical-order orchestration, mechanical Scout-
verdict mapping). All of this operates on hermetic fixture epoch ids only — no real epoch, no real
candidate outcome read, no UI. Rows 4/7/8's real-epoch/real-corpus values (freeze commit,
materialized econ floor, protected-access census) still await J-06/J-07. J-01's era-open baseline
(row 1) also became visible to the scoped QA rig this iteration via a read-only
`TAPEOLOGY_FOUNDRY_DIR`-style visibility fix — the computing module and endpoint are unchanged, so
this is not a new Data Contract row.

**Iteration note (iter-3):** shipped for real, hermetically — the composite “complete
factory” hermetic oracle suite (`apps/backend/tests/test_foundry_hermetic_epoch.py`)
exercises the full compiler → interpreter → family → freeze/ledger → runner path under
every outcome type at once (compiled/blocked/excluded/aliased sources;
insufficient/killed/survivor terminal variants), plus all-blocked, all-killed,
multi-survivor, large-scale checkpoint/resume, and
protected-data-trip/evidence-class-immutability fixtures (reusing the existing
`micro_accessor` `MicroAccessorSealedShardError`/`MicroAccessorOriginFenceError` exception
types — no new accessor abstraction). `foundry_runner.run_one_candidate`'s
already-terminal fast path now re-verifies `manifest_hash`/`econ_floor_bps` before
returning a cached row (closes the iter-2-carried resume-identity gap).
`foundry_source_registry.SourceRecord` gains `source_hash` (`sha256(source_excerpt)`, per
`docs/hypothesis-foundry-spec.md` §1.4) and `alternatives` (closes the iter-1-carried §1.4
field gap; see `state/assumptions.md` iter-3 for the exact-shape reading). All of this
still operates on hermetic fixture epoch ids only — no real epoch, no real candidate
outcome read, no UI; real `MicroAccessor` wiring for the real corpus stays J-07 territory.

**Iteration note (iter-4):** shipped for real — the consolidated Binding Execution Order step-5 read
surface. `GET /research/desk/micro/foundry` gains four new top-level keys (`sources_compiler`,
`interpreter_fixtures`, `freeze_integrity`, `hermetic_oracles`, table rows above), each read verbatim
by four new `/desk` → Hypothesis Foundry subsections (Sources/Compiler, Interpreter fixtures, Freeze/
Integrity, Hermetic Oracles) — all four rendered from a precomputed/cached fixture result, never
computed per GET request. Two carried integrity repairs also closed: `foundry_source_registry.py`
gained a fail-closed batch lint over `SourceRecord.alternatives` (rejects a nonexistent, wrong-family,
or self-referential sibling id — auditor B7); `foundry_runner.run_one_candidate`'s
intent-without-terminal ("crash") branch now also re-verifies the pinned intent row's `manifest_hash`
against the current invocation, mirroring the already-terminal path's iter-3 fix (auditor B4). No IA/
nav change (all four subsections live under the already-registered blueprint homes); no
`blueprint.reapproval-requested` needed. Real epoch/manifest (J-06), the real committed
`reports/hypothesis-foundry/source-registry-audit.md` J-02 depends on, and the Runner/Checkpoint
subview (J-07) remain unbuilt.

**Iteration note (iter-5, planned):** targets J-06 — the ONE real epoch generation this era permits
(§8.1). Plans to add the `epoch_manifest` key (new row above) to `GET /research/desk/micro/foundry`
and its `/desk` → Hypothesis Foundry → Epoch / Manifest subsection (blueprint home already
registered above, previously `[PLANNED, not yet built]`), reusing only already-registered Foundry
modules — no new computing module for any row. Also plans two small extensions to already-shipped
fixture rows: `hermetic_oracles` gains `kill_type_mapping`/`best_of_n_disclosure` (closing J-05's
remaining on-screen gap) and `sources_compiler` gains a second alias-family sibling entry plus
on-screen `operative_formula_refs`/`superseded_fields`/`aliases_lineage_ids` (closing J-02's
remaining on-screen gap; these three fields were already computed, this is a rendering-only fix, not
a new value). No IA/nav change (Epoch/Manifest's home was already registered at baseline); no
`blueprint.reapproval-requested` needed. This note will be confirmed or corrected by the next
iteration's decomposer once execution results are known.

**Iteration note (iter-6, planned):** targets J-07 — the real deterministic exhaust pass over the already-frozen, zero-candidate epoch. Because two committed freeze-bookkeeping gaps (absolute freeze-set paths; a `freeze_commit` that predates `foundry_compiler.py`) and one completeness gap (freeze-set/record omissions) must be closed BEFORE the one-way first-read lock is written — `docs/goal.md` §7.3 delegates exactly this class of pre-outcome-read repair to Goal Mode — this iteration first regenerates `docs/hypothesis-foundry/freeze-set.json` and `freeze-record.json` via the already-proven deterministic `generate_freeze_set`/`build_freeze_record` functions (never touching `epoch_id`, `source-registry.json`, or `epoch-manifest.json` content, so §8.1's one-epoch rule is untouched), then runs the new real exhaust CLI, which appends the `exhaust_progress` row above. Adds the `exhaust_progress` key (new row above) and its `/desk` → Hypothesis Foundry → Runner / Checkpoint subsection (blueprint home already registered above, previously `[PLANNED, not yet built]`), reusing only already-registered Foundry modules — no new computing module for any row. No IA/nav change; no `blueprint.reapproval-requested` needed. This note will be confirmed or corrected by the next iteration's decomposer once execution results are known.

An optional read-only MCP proxy (`desk_micro_foundry`) is deferrable per the goal; if built later it
must be a byte-identical GET proxy of this same endpoint and joins the existing MCP contract tests —
it introduces no new computing or serving path.

No shared canonical value outside this table is introduced by this era; every existing Cockpit/
Structure/Desk Data Contract row from prior eras is read-only foundation here and is not
re-registered.

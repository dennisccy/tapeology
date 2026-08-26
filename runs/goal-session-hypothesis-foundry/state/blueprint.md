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
                                iter-1 ships only the panel HEADER (era identity + era-open
                                baseline); the Sources/Compiler/Interpreter/Freeze subsections are
                                still [PLANNED, not yet built].
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
| Era/session identity, methodology/spec version, source-registry hash | `app/research/foundry_source_registry.py` | `GET /research/desk/micro/foundry` | era-open baseline (full-suite pass/skip, config fingerprint, Referee-module SHA-256) is part of this bundle; `source_registry_hash` stays `null`/`not_yet_generated` until the real registry exists (Binding Order step 6 / J-06) |
| Source dispositions + lineage/alias refs (one of the closed §7.1 vocabulary per required source object) | `app/research/foundry_source_registry.py` | `GET /research/desk/micro/foundry` | no required source may be silently absent; iter-1 proves the compile RULES on 7 hermetic fixture source types only — the REAL 11 required-source-object registry content ships at J-06 |
| Per-variant `CandidateSpec` + `candidate_spec_hash` + population/coordinate/direction/horizon summary | `app/research/foundry_compiler.py` (fixture-compilable candidates) + `app/research/foundry_interpreter.py` (planned; owns deferred/population resolution for J-03) | `GET /research/desk/micro/foundry` | every §3 science-affecting field must move the hash |
| Epoch id, manifest hash, freeze commit, freeze integrity verdict, first-outcome-read boundary status/time | `app/research/foundry_freeze.py` (planned) | `GET /research/desk/micro/foundry` | freeze-set = enumerated checked-in path+sha256 manifest, not an adjective |
| Family/variant counts, family order, variant ordinals, per-family frozen denominator, blocked/excluded/aliased counts by reason | `app/research/foundry_family.py` (planned) | `GET /research/desk/micro/foundry` | denominator frozen pre-outcome; over-cap blocks whole |
| Unresolved-deferred counts, eligible resolved anchors, candidate/comparator counts, usable sessions, evidence class | `app/research/foundry_interpreter.py` (planned) | `GET /research/desk/micro/foundry` | population symmetry per §4.1 |
| Materialized econ floor + unit/provenance, Scout decision, p-screen/effect-bps/concentration/economic/fragility disclosures, best-of-N disclosure, `DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN` state | `app/research/foundry_runner.py` calling the unchanged `scout.screen_candidate` (planned) | `GET /research/desk/micro/foundry` | Foundry never adds a second statistical rail; values are the verbatim Scout screen payload |
| Protected/withheld/sealed ids read by the real Foundry runner (must be zero; identity-safe aggregate only) | `app/research/foundry_runner.py` (planned) | `GET /research/desk/micro/foundry` | never sealed identities, joins the existing TR-2-style inference sweep |
| Current runner checkpoint / next manifest ordinal, ledger chain/integrity verification | `app/research/foundry_ledger.py` (planned) | `GET /research/desk/micro/foundry` | Foundry's own hash-chained append-only trial ledger; never registered into the Scout ledger |

**Iteration note (iter-1):** shipped for real — the `GET /research/desk/micro/foundry` route itself
(new, mounted on the existing `micro_routes.py` router, GET-only / never-computes); row 1's era
identity + era-open baseline (static one-time snapshot, not recomputed per request); row 2's owner
meta-policy compile RULES + exact-quote lint, proven on 7 hermetic fixture source records (not the
real 11 required source objects); row 3's `CandidateSpec` schema + `candidate_spec_hash` for the
subset of fixtures that compile directly (no deferred/population resolution — that still needs the
not-yet-built `foundry_interpreter.py`). No UI subsection beyond the panel header ships this
iteration; the Sources/Compiler fixture view (and all other subviews) ship together in a later
consolidated read-surface iteration per `docs/goal.md` Binding Execution Order step 5.

An optional read-only MCP proxy (`desk_micro_foundry`) is deferrable per the goal; if built later it
must be a byte-identical GET proxy of this same endpoint and joins the existing MCP contract tests —
it introduces no new computing or serving path.

No shared canonical value outside this table is introduced by this era; every existing Cockpit/
Structure/Desk Data Contract row from prior eras is read-only foundation here and is not
re-registered.

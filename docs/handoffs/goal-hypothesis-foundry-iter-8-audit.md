# goal-hypothesis-foundry-iter-8 Audit Report

**Date:** 2026-08-27
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-08 genuinely ships and the era's scientific rails held: I independently recomputed all 59
freeze-set hashes (byte-identical), cross-checked every one of the 11 served source records
field-by-field against both sealed artifacts (zero drift), extracted the live `/desk` DOM myself and
matched 27 values byte-for-byte against the served JSON, and re-ran all 8 golden journeys green.
One IMPORTANT honesty defect was found and fixed during this audit — the new top-level "final truth"
screen stated `Exhaust complete` **without** the vacuity caveat its own sibling subsection already
carries, on an epoch with zero frozen candidates. Two IMPORTANT evidence-integrity defects remain in
the QA report artifact (a blank screenshot cited as proof; a sealed file named as "modified"); both
are reporting defects, not product defects, and the underlying claims stand on other evidence.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (verified, no action): the sealed-file deviation is real and the dev handled it correctly**
The spec's IN SCOPE and `plan.md` both instructed the work into
`apps/backend/app/research/foundry_runner.py` and `foundry_source_registry.py`. I recomputed the
freeze-set myself: **both** files are entries in `docs/hypothesis-foundry/freeze-set.json`, so the
spec AND the plan were wrong on two counts, not one. The dev caught it, reverted byte-identically,
and relocated the field to `micro_routes.py:994`. Independently confirmed: all 59 sealed entries hash
byte-identical to their pinned `sha256` **after** my own fix as well, and `git status --porcelain`
lists no sealed path. `SCOUT_TO_FOUNDRY_STATE["survive"]` (`foundry_runner.py:52`) is reused rather
than re-literalled, so the survivor state has one definition.

**B2 — GAP (documented): `_compute_diagnostic_survivor_count` opens a second ledger read per request**
`micro_routes.py:994-1002` constructs its own `FoundryLedger` and calls `all_rows()`, duplicating the
read `read_exhaust_progress` already performs for `terminal_count` in the same request (the reviewer
filed this as a NOTE). I verified it is harmless in every dimension that matters: `HashChainedLedger.
__init__`/`_read_raw` (`micro_chain_ledger.py:64-138`) perform **no** `mkdir` and no write, and the
real ledger is 1,294 bytes. Empirically confirmed with an mtime/size diff of
`apps/backend/.data/foundry/` across three consecutive GETs — the only file touched was the
pre-existing `foundry_exhaust_runner.lock` (the already-open, owner-owned anti-goal item, whose only
repair site is sealed). The ledger and its chain-head anchor were **not** touched. Not fixed: the
only cleaner shape (threading the row list out of `read_exhaust_progress`) requires editing a sealed
file.

**B3 — GAP (documented): the §8.2 outcome-shaped-value sweep no longer covers the enriched payload**
`apps/backend/tests/test_foundry_real_epoch_artifacts.py:315` scans `json.dumps(manifest)` — the raw
tracked file — for `p_value`/`p_screen`/`effect_bps`/`forward_return`/`observation_count`/`pnl`. Until
this iteration the deleted assertion `served["source_dispositions"] == manifest["source_dispositions"]`
(same file, line 295 pre-diff) transitively extended that sweep to the served body. Its replacement
proves base-field fidelity plus enrichment presence, but the sweep itself no longer reaches the 11
new prose/hash fields per source. I checked the live served body directly: all six forbidden tokens
are absent. Not fixed, and it cannot newly fail: **both** `docs/hypothesis-foundry/source-registry.json`
and `epoch-manifest.json` are themselves freeze-set-sealed, so the enriched content is structurally
frozen for the life of the era.

**B4 — OBSERVATION: the enrichment merge is correctly bounded**
`_enrich_source_dispositions_with_registry_provenance` (`micro_routes.py:824-843`) merges only the 11
fields in an explicit tuple, so no stray registry key (`proxy_of`, `source_excerpt`, `source_path`,
`explicit_exclusion`, …) can leak into the served contract, and no registry value can overwrite a
manifest base field. Honest-absence defaults are per-entry copies, never a shared mutable. I also
checked the two artifacts cannot silently disagree: all 11 registry records carry their own
`disposition`, and all 11 agree with the manifest's.

### Frontend Findings

**F1 — IMPORTANT (fixed): the Final Summary claimed exhaust completion without the vacuity caveat**
`apps/frontend/app/desk/page.tsx:8047-8049` rendered, in emerald, `Exhaust complete -- every frozen
candidate reached a terminal state.` for an epoch whose `frozen_ready_total` is `0` — i.e. nothing was
ever evaluated. The shipped sibling `RunnerCheckpointSubsection` (`page.tsx:7888-7893`) states the
same served fact **with** the caveat `(zero FROZEN_READY variants this epoch — an honest, vacuous
completion).`, conditioned on exactly `data.frozen_ready_total === 0`. The browser-QA lane even quoted
the sibling's caveated sentence in UT-05 and the new caveat-free one in UT-02 without noticing the
asymmetry. This matters more here than anywhere else on the page: this subsection's own intro copy
says it is "synthesized from the six subsections below", and the phase GOAL is that the operator sees
the final truth *without* expanding them — so an operator reading only this screen got a materially
rosier reading than the truth. **Fixed** by mirroring the sibling's conditional verbatim; evidence in
§4.

**F2 — GAP (documented): TC-2's literal one-expand wording is not met — the subsection needs a second click**
TC-2 reads "when the operator visits `/desk` and expands the Hypothesis Foundry panel, then a
subsection with `data-testid="foundry-final-summary"` renders those seven values". I probed this
directly with Playwright against the live `:3301`: after expanding only the Hypothesis Foundry panel,
`FINAL_SUMMARY_IN_DOM_AFTER_PANEL_EXPAND_ONLY: False` — the block is unmounted until its own
`CollapsibleSection` (`page.tsx:8271`, `id="foundry-final-summary-section"`) is opened. Not fixed:
this is the convention all six sibling subsections already follow, `plan.md` explicitly authorised
`CollapsibleSection`, the section is first in DOM order so it is the first thing an operator meets,
and UT-06 verified discoverability from `/` in a short click path. Recorded because the DoD line
"J-08 passes via browser-qa-agent (TC-1 through TC-4)" is satisfied only under the browser lane's
two-click reading of TC-2, not TC-2's literal text.

**F3 — GAP (documented): two rendered audit notes cross-reference a field the drill-in never shows**
The `audit_note` for `pilot-study-1-range-wall-failed-aggression` (rendered verbatim, confirmed in the
live DOM) says "recorded via `unresolved_magnitude_words` below so an auditor sees the full mechanism
could not compile even absent the proxy rule". The drill-in
(`page.tsx:8073-8123`) does not render `unresolved_magnitude_words`; the value is real
(`['high','collapsing']`) and non-empty on 3 of 11 records, and 2 of 11 audit notes point at it. So
the shipped provenance view contains a dangling internal reference. Not fixed: the spec's IN SCOPE and
Data-contract enumerate exactly the 11 fields that shipped, and `unresolved_magnitude_words` is not
among them — adding a 12th field is scope creep past an explicit list.

**F4 — OBSERVATION: the hardcoded `11` and the client-side `.length` counts follow shipped precedent**
`page.tsx:8065` renders `Source detail ({sourceDispositions.length} of 11 required objects)` — a
backend-owned count literalled client-side — and `page.tsx:7992` renders
`({dispositionEntries.length} distinct dispositions)`. Neither is arithmetic on a served numeric
field, and the `11` pattern is copied verbatim from the pre-existing `EpochManifestSubsection`
(`page.tsx:7755`, shipped iter-5). Cannot go stale this era: the manifest is freeze-set-sealed at 11.
No action.

### Test Findings

**T1 — OBSERVATION: TC-6's counter-test is a regex-level proof, not a real injection**
`test_desk_page_price_arithmetic_guard_catches_foundry_field_arithmetic`
(`test_desk_ui_guards.py:2053-2072`) asserts the extended pattern matches five seeded strings rather
than injecting a violation into `page.tsx` and re-running the sweep. This matches the established
convention of ~15 sibling tests (e.g. `..._catches_playbook_field_arithmetic`, line 505), and TC-6's
other half — "passes against the shipped page" — is genuinely covered, because the sweep at
`test_desk_ui_guards.py:381-394` reads the whole real `apps/frontend/app/desk/page.tsx`. No action.

**T2 — OBSERVATION: the guard binds the `data.` prefix**
The new group `data\.(?:family_count|variant_count|frozen_ready_total|diagnostic_survivor_count|
protected_read_count)` catches `data.family_count - 1` but would not catch a destructured
`const { family_count } = data; family_count - 1`. This is a pattern-class limitation shared by every
pre-existing group in the same regex, not something this iteration introduced. No action.

**T3 — the new tests are genuinely discriminating (verified, positive finding)**
Two tests are load-bearing and neither passes by accident:
`test_iter8_exhaust_progress_diagnostic_survivor_count_is_a_genuine_filter_not_a_copy_of_terminal_count`
builds a ledger with 2 terminal rows of which 1 survived and asserts `terminal_count == 2` /
`diagnostic_survivor_count == 1` — a copy of `terminal_count` fails it. `test_iter8_final_summary_
copies_frozen_ready_total_verbatim_never_resums_families` passes `frozen_ready_total=5` alongside a
`families` list whose own `variant_count` is `99` — any second counting site fails it. This is
exactly the guard the spec's NOTES section demanded.

### Process / Evidence Findings

**P1 — IMPORTANT (gap; not repairable without falsifying an artifact): the QA report cites a blank screenshot as proof**
`reports/qa/goal-hypothesis-foundry-iter-8-qa.md` lists
`…-evidence/final-summary-section.png` as "Final Summary subsection visible on page" and passes UI
Evolution item 2 ("Visibility"). That PNG is **uniformly blank** — grayscale extrema `(14, 14)`,
dominant-pixel share `1.000` over all 1400×2400 pixels. This breaches the project's evidence floor
("UI journey passes" requires a screenshot showing the acceptance state) and the era's own T-10 rule
("no screenshot ⇒ `unknown`"). The claim itself is nonetheless **true**: the browser-QA lane
(`reports/phase-goal-hypothesis-foundry-iter-8-ui-test-results.md`, UT-01/UT-02) explicitly declared
which raw captures were blank, re-captured through `demo_runner --mode verify`, and passed on
non-blank images (`UT-02-result.png`, dominant share `0.804`) — and I re-verified the render myself in
a fresh browser. Not repaired: rewriting another lane's verdict artifact would destroy the audit
trail. Belongs in the closure record.

**P2 — IMPORTANT (gap; QA-artifact accuracy): the QA report names a sealed file as "modified"**
The same report's "Code Review Notes" states *"All files modified per spec (micro_routes.py,
**foundry_runner.py**, test_desk_ui_guards.py, page.tsx, lib/types.ts, **lib/api.ts**)"* and then, in
the next bullet, *"foundry_runner.py byte-unchanged"*. Both named extras are wrong: `foundry_runner.py`
is sealed and byte-identical, and `lib/api.ts` was never touched (neither appears in
`git status --porcelain` or in `status.json`'s `changed_files`). The reviewer's own report never made
that claim. A closure-record reader could reasonably conclude a sealed file was edited — the single
most consequential wrong conclusion available in this era. Recorded, not rewritten.

**P3 — OBSERVATION: the UX-regression lane was shed on the era's closing iteration**
`reports/phase-goal-hypothesis-foundry-iter-8-ux-regression.md` is
`UX-REGRESSION-SKIPPED` (SPEED-15 trim rung 3b, wall-clock budget). Non-blocking by design, but worth
one line in the closure record given this is the last journey of the era. The gap it would have
caught — F1 — was caught here instead.

---

## 3. Domain Assessment

The scientific core is sound, and I verified it from the artifacts rather than the prose.

**The seal held.** I recomputed sha256 for all 59 `freeze-set.json` entries: zero mismatches, zero
missing — before and after my own fix. `foundry_runner.py`, `foundry_source_registry.py`,
`epoch-manifest.json`, `source-registry.json` and the sealed exhaust CLI are all byte-identical.

**Serving is verbatim, not derived.** For all 11 source records I diffed the served
`epoch_manifest.source_dispositions[]` against **both** sealed files: every base manifest field
(`source_id`/`disposition`/`lineage_refs`/`alias_refs`) and all 11 provenance fields matched exactly —
zero drift, zero manifest ids missing from the registry, zero registry ids unsurfaced. The served
disposition tally `{ALIASED_PROXY_ONLY:2, BLOCKED_DIRECTION:4, BLOCKED_SPEC_GAP:1,
ALIASED_VARIANT_VOCABULARY:1, EXCLUDED_PREVIOUSLY_KILLED:1, EXCLUDED_PREREQUISITE_UNMET:1,
EXCLUDED_GATE_CLOSED:1}` equals an independent `Counter` over the sealed manifest, summing to 11.

**`final_summary` is a projection, not a second owner.** `variant_count` and `frozen_ready_total` both
come from the single caller-supplied `compute_frozen_ready_total` result rather than a second `sum()`
over `families`; the survivor/integrity/protected-read/completion fields are copied from the one
per-request `exhaust_progress` dict, which is read once and reused for both keys. The one new
computation — tallying already-decided `disposition` strings — is a count of existing facts, not a
re-derivation of what any disposition *is*. Both degrade branches of `read_exhaust_progress`
(`foundry_runner.py:258-283`) carry every key `compute_foundry_final_summary` indexes, so there is no
`KeyError` path, and `read_epoch_manifest_view`'s `not_yet_generated` dict carries
`source_dispositions: []`, so neither the projection nor the JSX crashes on a fresh install.

**`diagnostic_survivor_count` is a real filter.** It matches
`SCOUT_TO_FOUNDRY_STATE["survive"] == "DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN"` over `ROW_KIND_TERMINAL`
rows — the same closed §7.2 vocabulary, no duplicated literal — and the `and` short-circuit means
`row["foundry_state"]` is only read on rows that have it.

**GET stayed read-only.** Three consecutive live GETs changed nothing under
`apps/backend/.data/foundry/` except the mtime of the pre-existing `foundry_exhaust_runner.lock` — the
already-logged, owner-owned "Persistence stays scoped" item whose only repair site is sealed. No new
page-load write, and no new page-load *compute* of any scientific value.

**No outcome-shaped value leaked.** The enriched served `epoch_manifest` contains none of
`p_value`/`p_screen`/`effect_bps`/`forward_return`/`observation_count`/`pnl`, and TR-2's adversarial
join-resistance sweep (16 tests) passes with the new fields present.

**TC-10's correction is factually true.** The sealed CLI at
`apps/backend/scripts/run_hypothesis_foundry_real_exhaust.py:225` really does compute
`sum(len(fm.get("variants", [])) for fm in manifest.get("families", []))`, keyed differently from the
canonical helper's `sum(f["variant_count"] for f in …)`. The corrected docstring says exactly that,
and says the freeze-set pinning — not the assertion — is what prevents divergence. The assertion logic
and the sealed file are byte-unchanged.

**Honest negatives are preserved.** Zero families, zero variants, zero survivors, zero protected
reads, `evidence_class: historical_exposed_diagnostic`, and — after F1's fix — an explicitly *vacuous*
exhaust completion. Nothing in this iteration dresses an empty epoch up as a result.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/frontend/app/desk/page.tsx` (lines 8046-8056) | Final Summary's exhaust-complete sentence now carries the same `frozen_ready_total === 0` vacuity caveat `RunnerCheckpointSubsection` already ships, so the era's top-level truth screen cannot state completion more strongly than the subsection it summarises |

**Post-fix verification (all commands run in the foreground; real exit codes read):**

1. **Live render, before → after.** Playwright against `:3301`, same click path both times:
   - before: `'Exhaust complete -- every frozen candidate reached a terminal state.'`
   - after: `'Exhaust complete -- every frozen candidate reached a terminal state (zero FROZEN_READY variants this epoch — an honest, vacuous completion).'`
   - sibling for comparison, same page load: `'Exhaust complete — every frozen candidate reached a terminal state (zero FROZEN_READY variants this epoch — an honest, vacuous completion).'`
   - console errors: `[]`.
2. **Guards re-run.** `pytest tests/test_desk_ui_guards.py tests/test_copy_discipline.py
   tests/test_table_sort_guards.py tests/test_desk_refresh_chain_guard.py` → **167 passed**. Then every
   test that reads `desk/page.tsx` (13 files) → **269 passed**. The added condition is a `===`
   comparison, so the numeric anti-recomputation regex (which keys on `-+*/`) still reports zero hits.
3. **Full suite.** `cd apps/backend && .venv/bin/python -m pytest tests/ -p no:randomly` →
   **3930 passed, 8 skipped, exit 0** (identical to the pre-audit baseline — zero regressions).
   `cd apps/frontend && npx tsc --noEmit` → exit 0.
4. **All 8 golden journeys re-replayed after the fix.**
   `demo_runner.py --mode verify --journeys J-01..J-08` → `8 journey(s), 0 failed (verdict: PASS)`.
   This re-satisfies TC-12 *and* gives the target journey J-08 its own deterministic replay.
5. **Diff scope.** `git diff --stat` shows `page.tsx` moved from +176 to +184 lines — my one edit and
   nothing else. Freeze-set re-verified after the edit: **59/59 byte-identical**.
6. **No new finding introduced.** The fix adds no escape hatch and silences no error; it strictly
   *adds* a qualification to a claim.

No other finding was fixed: B2/B3/F2/F3 are GAPs (fixing them is scope creep, or requires editing a
sealed file), and P1/P2 are defects inside another lane's verdict artifact that must not be rewritten.

---

## 5. Recommended Next Step

**Proceed to era closure.** J-08 is genuinely built, verified end-to-end against real committed
artifacts, and every one of J-01–J-07 replays green after this audit's fix. No product work remains
that this iteration's spec asked for.

Carry into the closure record, not into repairs:

1. **The two owner-only anti-goal items stay open by design** — "No second real generation epoch"
   (ratify or reject the discarded first `epoch_id`) and "Persistence stays scoped" (the page-load GET
   touches `foundry_exhaust_runner.lock`; I re-confirmed this empirically and re-confirmed its only
   repair site, `foundry_runner.py:197-201`, is sealed). Both need an owner ruling.
2. **The permanently un-fixable-under-freeze advisory** — the sealed CLI keeps a second
   `frozen_ready_total` formula keyed on a different manifest field. TC-10's docstring now states this
   honestly; nothing more can be done without breaking the seal.
3. **The GAPs above** — B2 (second per-request ledger read), B3 (§8.2 sweep no longer reaches the
   enriched payload), F2 (Final Summary needs its own expand), F3 (`unresolved_magnitude_words`
   dangling reference in two rendered audit notes).
4. **Two evidence-integrity defects in this iteration's QA report** — P1 (a uniformly blank PNG cited
   as visibility proof, breaching the era's own T-10 rule) and P2 (a sealed file named among "files
   modified"). Both claims are otherwise independently evidenced, but the report as written would
   mislead a closure-record reader. This is the second consecutive iteration where the QA lane
   certified more than its own evidence supported (iter-7: QA certified "DoD ✓ Complete" while the
   browser lane never replayed the target journey) — worth one framework line, not a product fix.

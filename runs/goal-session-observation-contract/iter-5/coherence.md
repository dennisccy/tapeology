# Iteration 5 — Coherence Audit

**Iteration:** goal-observation-contract-iter-5
**Date:** 2026-09-05
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Scope of this iteration (confirmed by diff inspection)

`git diff ae5e9059e61f06af3fca2442a97c47da00ffbf98 --stat -- . <noise-excludes>` (cross-checked
against `runs/goal-session-observation-contract/iter-5/iter-diff.md`) shows exactly two tracked
files touched plus one new untracked test module:

- `apps/backend/app/main.py` (+48/-0) — one new import, a new tiny `_now_utc()` seam, and the new
  `GET /tape/{ticker}/observation` route.
- `apps/backend/tests/test_tape_observation_path_equivalence.py` (+19/-6) — fixes the vacuous
  `test_counterexample_field_partition_drift_is_detected` (TC-16) to perturb the real
  `observation_contract.MACHINE_OBSERVATION_SEMANTIC_FIELDS` via `monkeypatch` instead of comparing
  two hand-written literals.
- `apps/backend/tests/test_tape_observation_route.py` (new, 398 lines) — the route's own test
  module (TC-8..TC-15), read in full (the bounded diff's 4-line tail omission was read directly
  from source: the closing `assert len(TOOL_NAMES) == 28` pin, nothing else).

The excluded-path stat additionally shows `runs/goal-session-observation-contract/journey-scripts/
{J-01,J-03,J-04}.json` (the three golden-replay fixups named in scope, TC-17) plus harness/report
bookkeeping (`telemetry.jsonl`, `trace.jsonl`, `blueprint.md`, `goal-slice.md`, index HTML) — all
non-code. Zero files under `apps/frontend/` and zero other files under `apps/backend/app/`
(`observation_contract.py`, `watch_manager.py`, `mcp/__init__.py`) appear anywhere in the diff —
confirmed directly, not merely asserted from the spec. This matches the iter spec's IN
SCOPE/OUT OF SCOPE exactly.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Machine observation semantics (`schema_version`, `tape_state`, `confidence`, `market.*`, `engine_identity.*`, …) | OK | `apps/backend/app/main.py:656-676` (`get_observation`) calls only `manager.get_observation_source(ticker)` then `build_tape_observation(...)` — the two already-registered canonical modules, unmodified this iteration. AST guard `test_tape_observation_route.py:240-243` (`test_route_consumes_the_atomic_read_and_calls_no_tape_engine_method`) proves the route calls no `TapeEngine` method; its counter-example (`:246-257`) proves the same scan is not vacuous. |
| Provenance/source/lifecycle metadata (`source.*`, `lifecycle.*`, `timing.*`, `available_at_utc`) | OK | `main.py:659-676` unpacks the atomic 4-tuple from `get_observation_source` and threads every descriptor field verbatim into `build_tape_observation` — no re-derivation, no second parse of any provenance field. |
| `generated_at_utc` (provenance row) | OK | `main.py:675` (`generated_at_utc=_iso_utc(_now_utc())`) — this is the route supplying its own required wall-clock INPUT to the one canonical builder, exactly as the blueprint's row 2 and the iter spec's IN SCOPE text specify ("`generated_at_utc` from the route's own `now`"), not an independent computation of a registered value. The new `_now_utc()` (`main.py:277-284`) is a bare `datetime.now(timezone.utc)` wrapper added solely for monkeypatch-freezability; confirmed the only `datetime.now(timezone.utc)` call site in `main.py` (`grep -n "datetime.now(timezone.utc)" apps/backend/app/*.py` → one hit). It does not duplicate `main.py`'s existing, unmodified `_iso_utc(dt)` (line 267, pre-existing since iter-3) nor `observation_contract.py`/`watch_manager.py`'s separate `_iso_utc(epoch: float)` formatters (different signature, different modules, untouched this iteration, already cross-checked byte-for-byte since iter-4 per that iteration's coherence verdict). |
| Explanatory metadata (`observations[]`) | OK | Unpacked verbatim from `snapshot` inside `build_tape_observation`; untouched by this iteration's diff. |
| Integrity (`observation_hash`, `artifact_hash`) | OK | Route returns `build_tape_observation`'s dict verbatim for FastAPI to serialize (`main.py:660-676`) — no re-hash in the route. `test_tape_observation_route.py:358-367` (`test_hashes_recomputable_from_served_json`) recomputes both hashes from the SERVED JSON via `observation_contract.compute_observation_hash`/`compute_artifact_hash` (the canonical hash laws, not reimplemented) and asserts equality (TC-12). |
| 404 shape for an unwatched ticker | OK | `main.py:657-658` raises `HTTPException(404, f"Ticker '{ticker}' is not being watched")` — byte-identical to the pre-existing `_engine_or_404` helper (`main.py:254-258`) every other `/tape/*` sibling uses. `test_tape_observation_route.py:263-270` (`test_404_parity_with_tape_state_for_an_unwatched_ticker`) asserts the two bodies are equal (TC-9). Not a second 404 convention. |
| MCP `get_endpoint` passthrough | OK | `apps/backend/app/mcp/__init__.py` is absent from the diff (unmodified) — the existing `/tape/` prefix allowlist reaches the new route with zero registry change, confirmed by the iter spec's BACKGROUND and by `test_tape_observation_route.py:469-508` (`test_mcp_get_endpoint_bytes_equal_rest_bytes_against_real_uvicorn`), which proves byte-identical bodies (modulo the two fields — `generated_at_utc`/`artifact_hash` — that are honestly non-reproducible across two independent requests, per Constitution §2/§6, the same non-reproducibility TC-7 already establishes) against a real uvicorn subprocess, zero transformation. |

No new displayed value outside the four already-registered Data Contract rows is introduced — the
"New information displayed" list in the iter spec enumerates only fields already partitioned inside
`observation_contract.py` at iteration 1 (unmodified this iteration), so Data Contract items 4/5
(duplicate-of-existing / unregistered-new-value) do not apply. No new UI surface exists to fetch
anything from a non-canonical source (zero frontend files in the diff).

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `GET /tape/{ticker}/observation` (new) | OK | The blueprint's Information Architecture section pre-declares this exact path under "Machine-only surface (no nav entry — reached by URL / MCP, never a UI control)" — a category established at iter-0 baseline, directly traceable to `docs/goal.md` Product Shape §"Navigation / information architecture" ("Existing product routes remain unchanged... No page, panel, link or component is added or modified"). The route lands at precisely this pre-declared path, with zero frontend files touched (confirmed via `git diff --stat`) — no parallel shell, no new page, no duplicate home for an existing entity. Since the blueprint itself defines "no nav entry" as this feature's canonical home, the standard nav-reachability check does not apply here by design, not by omission. |
| `/`, `/structure`, `/desk` | OK (unchanged) | Zero frontend files in the diff; DEFINITION OF DONE requires and the review/regression-replay evidence in `runs/goal-session-observation-contract/iter-5/` confirms these three render exactly as before — no new panel, link, or control. |

No new page/route requiring nav reachability was introduced. No duplicate home was created for any
existing entity (Cockpit/Structure/Desk are untouched).

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- None beyond what prior iterations already carried and closed. The `_iso_utc` triple-implementation
  question (flagged advisory at iter-3, closed with a byte-for-byte cross-check at iter-4) is
  unaffected — this iteration reuses `main.py`'s existing `_iso_utc(dt)` unmodified and adds a
  distinct, narrowly-scoped `_now_utc()` seam for a different concern (supplying "now," not
  formatting a timestamp).
- This iteration also repairs a Data-Contract-adjacent test hygiene item the iter-4 evaluator found
  (the vacuous `test_counterexample_field_partition_drift_is_detected`) so that the guard now
  perturbs the real `observation_contract` constant rather than a second hand-written literal — a
  fix, not a new finding, and it removes rather than adds coherence risk.
